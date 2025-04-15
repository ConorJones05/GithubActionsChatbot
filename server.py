#  internal
import debug_module
import vector_logic
import supabase_logic

#  external
from fastapi import FastAPI, HTTPException, Request
import uuid
from dotenv import load_dotenv
import re
import base64
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware
import os
import jwt
from datetime import datetime
import secrets
import string

#  built-in

load_dotenv()

app: FastAPI = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    api_key: str
    logs: str
    code_context: Optional[str] = None

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "github-actions-chatbot"}


@app.post("/analyze")
async def analyze_logs(request: AnalyzeRequest) -> Dict[str, Any]:
    """Analyze logs and return insights."""
    api_key = request.api_key
    logs = base64.b64decode(request.logs).decode("utf-8")
    code_context = request.code_context

    if not supabase_logic.check_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API Key")

    logs_packet = debug_module.parse_logs(logs)
    if code_context:
        logs_packet.logs += f"\n\nCode context from repository:\n{code_context}"

    error_id = str(uuid.uuid4())
    processed_logs = vector_logic.token_checker(logs_packet.logs, "cl100k_base")
    error_vector = vector_logic.vector_embeddings(processed_logs)

    analysis = debug_module.call_gpt_fix(logs_packet)
    new_code = debug_module.call_gpt_new_code(logs_packet)

    old_code = ""
    file_name = logs_packet.file_name if logs_packet.file_name else "unknown"
    
    if code_context:
        try:
            decoded_context = base64.b64decode(code_context).decode("utf-8")
            
            context_pattern = r'===BEGIN_FILE: ([^=]+)===\n(.*?)===END_FILE==='
            context_matches = re.findall(context_pattern, decoded_context, re.DOTALL)
            
            if context_matches:
                context_file_name, context_content = context_matches[0]
                
                if "_" in context_file_name:
                    extracted_name = context_file_name.split("_")[-2]
                    if extracted_name:
                        file_name = extracted_name
                
                file_line_match = re.search(r'FILE: ([^,]+), LINE:', context_content)
                if file_line_match:
                    actual_file_path = file_line_match.group(1)
                    file_name = os.path.basename(actual_file_path)
                
                code_lines = context_content.split('\n')
                if code_lines and "FILE:" in code_lines[0] and "LINE:" in code_lines[0]:
                    code_lines = code_lines[1:]
                
                old_code = '\n'.join(code_lines).strip()
                print(f"Extracted old code from code context: {file_name}")
        except Exception as e:
            print(f"Error extracting from code context: {str(e)}")
    
    if not old_code:
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', logs, re.DOTALL)
        if code_blocks:
            old_code = code_blocks[0]
            print("Extracted old code from markdown code blocks")
        
        if not old_code:
            context_pattern = r'===BEGIN_FILE: ([^=]+)===\n(.*?)===END_FILE==='
            context_matches = re.findall(context_pattern, logs, re.DOTALL)
            
            if context_matches:
                context_file_name, old_code = context_matches[0]
                print(f"Extracted old code from log structured format: {context_file_name}")
    
    client = supabase_logic.initialize_supabase()
    user_response = client.table("users").select("user_id").eq("api_key", api_key).execute()
    
    if user_response.data and len(user_response.data) > 0:
        user_id = user_response.data[0]["user_id"]
        
        repo_pattern = r'github\.com/([^/]+/[^/]+)'
        repo_match = re.search(repo_pattern, logs)
        repo = repo_match.group(1) if repo_match else "unknown/repo"
        
        supabase_logic.update_recommendations(
            client, 
            user_id, 
            repo, 
            file_name, 
            old_code, 
            new_code, 
            analysis
        )
        
        supabase_logic.update_user_logs(client, api_key, logs_packet.file_name, repo)
    
    metadata = vector_logic.VectorMetadata(
        genre="errors",
        api_key=api_key,
        issue=str(logs_packet.file_name or "unknown"),
        timestamp=supabase_logic.datetime.now().isoformat(),
    )
    vector_logic.add_vector(vector_id=error_id, vector_values=error_vector, metadata=metadata)

    return {"analysis": analysis, "error_id": error_id, "new_code": new_code}

def verify_jwt(token: str) -> dict:
    """Verify the JWT token from Supabase"""
    try:
        jwt_secret = os.environ.get("SUPABASE_JWT_SECRET", "")
        payload = jwt.decode(
            token, 
            jwt_secret, 
            algorithms=["HS256"],
            options={"verify_signature": True}
        )
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

def generate_api_key(length: int = 32) -> str:
    """Generate a secure random API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

@app.post("/api/generate-key")
async def generate_user_api_key(request: Request) -> Dict[str, str]:
    """Generate an API key for a user."""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = auth_header.split(" ")[1]
        payload = verify_jwt(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user ID")
        
        api_key = generate_api_key()
        client = supabase_logic.initialize_supabase()
        response = client.table("users").select("*").eq("user_id", user_id).execute()
        
        if len(response.data) > 0:
            client.table("users").update({
                "api_key": api_key,
                "last_updated": datetime.now().isoformat()
            }).eq("user_id", user_id).execute()
        else:
            client.table("users").insert({
                "user_id": user_id,
                "api_key": api_key,
                "api_calls": 0,
                "created_at": datetime.now().isoformat(),
                "repo_used": ""
            }).execute()
        
        return {"api_key": api_key}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate API key: {str(e)}")

# Standard library imports
import base64
import os
import re
import secrets
import string
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# Third-party imports
import jwt
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

# Internal imports
import debug_module
import vector_logic
import supabase_logic
from auth_helpers import verify_auth_header

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="GitHub Actions Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://githubactionschatbot.onrender.com",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Pydantic Models -----

class AnalyzeRequest(BaseModel):
    """Request model for log analysis."""
    api_key: str
    logs: str
    code_context: Optional[str] = None

class ApiKeyRequest(BaseModel):
    """Request model for API key generation."""
    user_id: str = Field(..., description="Supabase user ID")

class ApiResponse(BaseModel):
    """Standard API response model."""
    status: str = "success"
    error_id: Optional[str] = None
    message: Optional[str] = None

class AnalysisResponse(ApiResponse):
    """Response model for analysis endpoint."""
    analysis: str
    new_code: str

class ApiKeyResponse(ApiResponse):
    """Response model for API key generation."""
    api_key: str

class CodeExtraction(BaseModel):
    """Model for extracted code information."""
    code: str
    file_name: str

# ----- Helper Functions -----

def generate_api_key(length: int = 32) -> str:
    """Generate a secure random API key."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def verify_jwt(token: str) -> dict:
    """Verify the JWT token from Supabase."""
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

def extract_code_from_context(code_context: str) -> CodeExtraction:
    """Extract code and filename from code context."""
    try:
        decoded_context = base64.b64decode(code_context).decode("utf-8")
        
        context_pattern = r'===BEGIN_FILE: ([^=]+)===\n(.*?)===END_FILE==='
        context_matches = re.findall(context_pattern, decoded_context, re.DOTALL)
        
        if not context_matches:
            return CodeExtraction(code="", file_name="unknown")
            
        context_file_name, context_content = context_matches[0]
        file_name = "unknown"
        
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
        
        return CodeExtraction(code=old_code, file_name=file_name)
        
    except Exception as e:
        print(f"Error extracting from code context: {str(e)}")
        return CodeExtraction(code="", file_name="unknown")

def extract_code_from_logs(logs: str) -> CodeExtraction:
    """Extract code and filename from logs."""
    code_blocks = re.findall(r'```[\w]*\n(.*?)```', logs, re.DOTALL)
    if code_blocks:
        return CodeExtraction(code=code_blocks[0], file_name="unknown")
    
    context_pattern = r'===BEGIN_FILE: ([^=]+)===\n(.*?)===END_FILE==='
    context_matches = re.findall(context_pattern, logs, re.DOTALL)
    
    if context_matches:
        context_file_name, old_code = context_matches[0]
        return CodeExtraction(code=old_code, file_name=context_file_name)
    
    return CodeExtraction(code="", file_name="unknown")

def extract_repository_info(logs: str) -> str:
    """Extract repository info from logs."""
    repo_pattern = r'github\.com/([^/]+/[^/]+)'
    repo_match = re.search(repo_pattern, logs)
    return repo_match.group(1) if repo_match else "unknown/repo"

async def get_auth_user_id(request: Request) -> str:
    """Extract and verify user ID from auth header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = auth_header.split(" ")[1]
    payload = verify_jwt(token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user ID")
    
    return user_id

async def analyze_and_get_results(logs_packet: debug_module.LogPacket) -> Tuple[str, str]:
    """Generate analysis and new code from logs."""
    analysis = debug_module.call_gpt_fix(logs_packet)
    new_code = debug_module.call_gpt_new_code(logs_packet)
    return analysis, new_code

async def create_or_update_user_api_key(user_id: str) -> str:
    """Create or update an API key for a user."""
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
            "repo_used": []
        }).execute()
    
    return api_key

# ----- API Endpoints -----

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "github-actions-chatbot"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_logs(request: AnalyzeRequest) -> AnalysisResponse:
    """Analyze logs and return insights."""
    client = supabase_logic.initialize_supabase()
    
    if not supabase_logic.check_api_key(client, request.api_key):
        raise HTTPException(status_code=401, detail="Invalid API Key")

    logs = base64.b64decode(request.logs).decode("utf-8")
    logs_packet = debug_module.parse_logs(logs)
    
    if request.code_context:
        logs_packet.logs += f"\n\nCode context from repository:\n{request.code_context}"

    error_id = str(uuid.uuid4())
    processed_logs = vector_logic.token_checker(logs_packet.logs, "cl100k_base")
    error_vector = vector_logic.vector_embeddings(processed_logs)

    analysis, new_code = await analyze_and_get_results(logs_packet)

    old_code = ""
    file_name = logs_packet.file_name if logs_packet.file_name else "unknown"
    
    if request.code_context:
        extraction = extract_code_from_context(request.code_context)
        if extraction.code:
            old_code = extraction.code
            file_name = extraction.file_name
    
    if not old_code:
        extraction = extract_code_from_logs(logs)
        if extraction.code:
            old_code = extraction.code
            if extraction.file_name != "unknown":
                file_name = extraction.file_name
    
    user_response = client.table("users").select("user_id").eq("api_key", request.api_key).execute()
    
    if user_response.data and len(user_response.data) > 0:
        user_id = user_response.data[0]["user_id"]
        repo = extract_repository_info(logs)
        
        supabase_logic.update_recommendations(
            client, 
            user_id, 
            repo, 
            file_name, 
            old_code, 
            new_code, 
            analysis
        )
        
        supabase_logic.update_user_logs(client, request.api_key, logs_packet.file_name, repo)
    
    metadata = vector_logic.VectorMetadata(
        genre="errors",
        api_key=request.api_key,
        issue=str(logs_packet.file_name or "unknown"),
        timestamp=supabase_logic.datetime.now().isoformat(),
    )
    vector_logic.add_vector(vector_id=error_id, vector_values=error_vector, metadata=metadata)

    return AnalysisResponse(
        analysis=analysis, 
        error_id=error_id, 
        new_code=new_code
    )

@app.post("/api/generate-key", response_model=ApiKeyResponse)
async def generate_user_api_key(request: Request) -> ApiKeyResponse:
    """Generate an API key for a user."""
    try:
        user_id = await get_auth_user_id(request)
        
        api_key = await create_or_update_user_api_key(user_id)
        
        return ApiKeyResponse(api_key=api_key)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate API key: {str(e)})

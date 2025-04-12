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

#  built-in

load_dotenv()

app: FastAPI = FastAPI()

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
    metadata = vector_logic.VectorMetadata(
        genre="errors",
        api_key=api_key,
        issue=str(logs_packet.file_name or "unknown"),
        timestamp=supabase_logic.datetime.now().isoformat(),
    )
    vector_logic.add_vector(vector_id=error_id, vector_values=error_vector, metadata=metadata)
    supabase_logic.update_user_logs(api_key=api_key, issue=logs_packet.file_name)

    return {"analysis": analysis, "error_id": error_id}
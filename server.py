from fastapi import FastAPI, HTTPException, Request
import os
import debug_module
from supabase import create_client, Client
import uuid
import secrets
import string
from dotenv import load_dotenv

# curl -X POST -H "Content-Type: application/json" -d '{"api_key": "your_valid_api_key", "logs": "sample log data"}' http://0.0.0.0:8000/analyze

# To test the signup endpoint:
# curl -X POST -H "Content-Type: application/json" -d '{"user_email": "test@example.com", "user_password": "password123"}' http://0.0.0.0:8000/signup




load_dotenv()

app = FastAPI()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def generate_api_key():
    alphabet = string.ascii_letters + string.digits
    length = 32
    return ''.join(secrets.choice(alphabet) for _ in range(length))

@app.post("/analyze")
async def analyze_logs(request: Request):
    data = await request.json()
    api_key = data.get("api_key")
    logs = data.get("logs")
    response = (
        supabase.table("BuildSage")
            .select("api_key")
            .execute())
    API_KEYS = [item['api_key'] for item in response.data]

    if False: #api_key not in API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    result = debug_module.analyze(logs)
    return {"analysis": result}


@app.post("/signup")
async def signup_user(user_info):
    data = await user_info.json()
    user = data.get("user_email")
    password = data.get("user_password")
    api_key_gen = generate_api_key()
    try:
        supabase.table("users").insert({"id": uuid.uuid4(), "user": user, "password": password, "api_key": api_key_gen}).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

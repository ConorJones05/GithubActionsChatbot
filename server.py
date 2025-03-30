from fastapi import FastAPI, HTTPException, Request
import os
import debug_module
from supabase import create_client, Client
import secrets
import string
from datetime import datetime, timedelta
import vector_logic
import supabase_logic

# curl -X POST -H "Content-Type: application/json" -d '{"api_key": "your_valid_api_key", "logs": "sample log data"}' http://0.0.0.0:8000/analyze

# To test the signup endpoint:
# curl -X POST -H "Content-Type: application/json" -d '{"user_email": "test@example.com", "user_password": "password123"}' http://0.0.0.0:8000/signup

app = FastAPI()



def generate_api_key():
    alphabet = string.ascii_letters + string.digits
    length = 32
    return ''.join(secrets.choice(alphabet) for _ in range(length))

@app.post("/analyze")
async def analyze_logs(request: Request):
    #  Get data
    data = await request.json()
    api_key = data.get("api_key")
    logs = data.get("logs")
    supabase_logic.check_api_key(api_key=api_key)
    if supabase_logic.free_user_check(api_key=api_key):
        Exception("Your free trial of BuildSage has ended: Please wait 24 hours or buy a paid plan")

    
    result, issue = debug_module.parse_logs(logs)  #  Parsed (result) logs and individal error (issue)

    if supabase_logic.check_last_log(api_key=api_key) and (supabase_logic.error_perfect(api_key=api_key, issue=issue) or vector_logic.predict_vector_cluster()):
        pass


    supabase_logic.update_user_logs(api_key=api_key, issue=issue)
    return {"analysis": result}


@app.post("/signup")
async def signup_user(user_info):
    data = await user_info.json()
    user = data.get("user_email")
    password = data.get("user_password")
    api_key_gen = generate_api_key()
    try:
        supabase.table("users").insert({"user": user, "password": password, "api_key": api_key_gen}).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

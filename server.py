from fastapi import FastAPI, HTTPException, Request
import os
import debug_module
from supabase import create_client, Client
import secrets
import string
from datetime import datetime, timedelta
import vector_logic
import supabase_logic

app = FastAPI()

@app.post("/analyze")
async def analyze_logs(request: Request):
    #  Get data
    data = await request.json()
    api_key = data.get("api_key")
    logs = data.get("logs")
    if supabase_logic.check_api_key(api_key=api_key):
        Exception("Wrong API Key")
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
    try:
        supabase_logic.add_user(user, password, )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

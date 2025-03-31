from fastapi import FastAPI, HTTPException, Request
import os
from supabase import create_client, Client
from datetime import datetime, timedelta
import string
import secrets
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def check_api_key(api_key):
    response = (
        supabase.table("user_master")
            .select("api_key")
            .execute())
    API_KEYS = [item['api_key'] for item in response.data]

    return api_key not in API_KEYS

def free_user_check(api_key):
    """Check if a free user has exceeded their API call limit"""
    response = (supabase.table("user_master")
     .select("api_calls")
     .eq("api_key", api_key)
     .execute()
     )
    if not response.data:
        return True 
    return response.data[0]['api_calls'] >= 4

def error_perfect(api_key, issue):
    """Checks if the user error is the same as last time"""
    response = (
        supabase.table("user_logs")
        .select("call_times")
        .eq("api_key", api_key)
        .execute()
    )
    
    if not response.data or len(response.data) == 0:
        return False
        
    call_times = [item.get('call_times') for item in response.data if item.get('call_times')]
    if not call_times:
        return False
        
    max_time = max(call_times)
    
    past_issue = (
        supabase.table("user_logs")
        .select("issue")
        .eq("call_times", max_time)
        .eq("api_key", api_key)
        .execute()
    )
    
    if not past_issue.data or len(past_issue.data) == 0:
        return False
    
    return past_issue.data[0].get('issue') == issue

def check_last_log(api_key) -> bool:
    """Checks the users request was less than 10 mins ago"""
    response = (
        supabase.table("user_logs")
        .select("time")
        .eq("api_key", api_key)
        .execute()
    )
    
    if not response.data or len(response.data) == 0:
        return False
    
    call_times = [datetime.fromisoformat(item['time']) for item in response.data if 'time' in item]
    
    if not call_times:
        return False
    
    return datetime.now() - max(call_times) < timedelta(minutes=10)

def update_user_logs(api_key, issue):
    """Update the users logs and increment the amount of calls they have"""
    (supabase.table("user_logs")
        .insert({"api_key": api_key, "issue": issue, "time": datetime.now().isoformat()})
        .execute()
    )
    
    response = (supabase.table("user_master")
     .select("api_calls")
     .eq("api_key", api_key)
     .execute()
     )
     
    if response.data and len(response.data) > 0:
        current_calls = response.data[0].get('api_calls', 0)
        (supabase.table("user_master")
         .update({"api_calls": current_calls + 1})
         .eq("api_key", api_key)
         .execute()
        )

def generate_api_key():
    alphabet = string.ascii_letters + string.digits
    length = 32
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def add_user(user, password):
    """Add a new user and return their API key"""
    api_key = generate_api_key()
    supabase.table("user_master").insert({"user": user, "password": password, "api_key": api_key, "api_calls": 0}).execute()
    return api_key
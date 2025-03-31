from fastapi import FastAPI, HTTPException, Request
import os
from supabase import create_client, Client
from datetime import datetime, timedelta
import string
import secrets

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
    response = (supabase.table("user_master")
     .select("api_calls")
     .eq("api_key", api_key)
     .execute()
     )
    return not (response.data >= 4)

def error_perfect(api_key, issue):
    """Checks if the user error is the same as last time"""
    response = (
        supabase.table("user_logs")
        .select("call_times")
        .eq("api_key", api_key)
        .execute()
    )
    past_issue = (
        supabase.table("user_logs")
        .select("issue")
        .eq("call_times", max(response.data))
        .eq("api_key", api_key)
        .execute()
    )
    return past_issue == issue



def check_last_log(api_key) -> bool:
    """Checks the users request was less than 10 mins ago"""
    response = (
        supabase.table("user_logs")
        .select("call_times")
        .eq("api_key", api_key)
        .execute()
    )
    call_times = [item['api_key'] for item in response.data]
    return max(call_times) - datetime.now() < timedelta(minutes=10)

def update_user_logs(api_key, issue):
    """Update the users logs and incremnt the amount of calls they have"""
    (supabase.table("user_logs")
        .insert({"api_key": api_key, "issue": issue, "time": datetime.now()})
        .execute()
    )
    response = (supabase.table("user_master")
     .select("api_calls")
     .eq("api_key", api_key)
     .execute()
     )
    #  Update amount of calls
    (supabase.table("user_master")
     .update("api_calls", response.data + 1)
     .eq("api_key", api_key)
     .execute()
     )

def generate_api_key():
    alphabet = string.ascii_letters + string.digits
    length = 32
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def add_user(user, password):
    supabase.table("users").insert({"user": user, "password": password, "api_key": generate_api_key()}).execute()
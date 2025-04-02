from fastapi import FastAPI, HTTPException, Request
import os
from supabase import create_client, Client
from datetime import datetime, timedelta
import string
import secrets
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if url and key:
    logger.info(f"Connecting to Supabase...")
    try:
        supabase: Client = create_client(url, key)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"ERROR initializing Supabase client: {str(e)}")
        raise e
else:
    logger.error("Missing Supabase credentials")
    raise RuntimeError("Missing required Supabase credentials")

def check_api_key(api_key):
    """
    Verify if the API key is valid
    """
    try:
        response = (supabase.table("users")
            .select("api_key")
            .eq("api_key", api_key)
            .execute())
        return len(response.data) > 0
    except Exception as e:
        logger.error(f"ERROR checking API key: {str(e)}")
        return False

def free_user_check(api_key):
    """Check if a free user has exceeded their API call limit"""
    logger.info(f"Checking free user limits...")
    try:
        response = (supabase.table("users")
         .select("api_calls")
         .eq("api_key", api_key)
         .execute()
         )
        if not response.data:
            logger.warning("No user data found for API key")
            return True 
        api_calls = response.data[0]['api_calls']
        logger.info(f"User has made {api_calls} API calls")
        result = api_calls >= 4
        return result
    except Exception as e:
        logger.error(f"ERROR checking free user limits: {str(e)}")
        return True

def error_perfect(api_key, issue):
    """
    Check if this exact error has been seen before
    """
    try:
        if issue:
            response = (supabase.table("logs")
                .select("issue")
                .eq("api_key", api_key)
                .eq("issue", str(issue))
                .gte("timestamp", (datetime.now() - timedelta(hours=24)).isoformat())
                .execute())
            return len(response.data) > 0
    except Exception as e:
        logger.error(f"ERROR checking for duplicate errors: {str(e)}")
    
    return False

def check_last_log(api_key) -> bool:
    """
    Check if the user has submitted logs recently
    """
    try:
        # Look for logs in the past hour
        response = (supabase.table("logs")
            .select("timestamp")
            .eq("api_key", api_key)
            .gte("timestamp", (datetime.now() - timedelta(hours=1)).isoformat())
            .execute())
        return len(response.data) > 0
    except Exception as e:
        logger.error(f"ERROR checking for recent logs: {str(e)}")
    
    # Default to treating all errors as new
    return False

def update_user_logs(api_key, issue):
    """
    Update user logs in the database
    """
    logger.info(f"Updating logs for user...")
    
    try:
        # Increment the user's API call count
        response = (supabase.table("users")
            .update({"api_calls": supabase.raw("api_calls + 1"), 
                     "last_log_time": datetime.now().isoformat(),
                     "last_issue": str(issue)})
            .eq("api_key", api_key)
            .execute())
        
        log_entry = {
            "api_key": api_key,
            "issue": str(issue),
            "timestamp": datetime.now().isoformat()
        }
        supabase.table("logs").insert(log_entry).execute()
        
        logger.info("Database updated successfully")
        return True
    except Exception as e:
        logger.error(f"ERROR updating user logs in Supabase: {str(e)}")
        # Return False to indicate failure
        return False

def generate_api_key():
    alphabet = string.ascii_letters + string.digits
    length = 32
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def add_user(user, password):
    """Add a new user and return their API key"""
    api_key = generate_api_key()
    supabase.table("users").insert({"user": user, "password": password, "api_key": api_key, "api_calls": 0}).execute()
    return api_key
from fastapi import FastAPI, HTTPException, Request
import os
from supabase import create_client, Client
from datetime import datetime, timedelta
import string
import secrets
from dotenv import load_dotenv
import logging
from pydantic import BaseModel, Field, BaseSettings
from typing import Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class User(BaseModel):
    user: str
    password: str
    api_key: str
    api_calls: int = 0
    last_log_time: Optional[datetime] = None
    last_issue: Optional[str] = None

class LogEntry(BaseModel):
    api_key: str
    issue: str
    timestamp: datetime = Field(default_factory=datetime.now)

class SupabaseConfig(BaseSettings):
    url: str
    key: str
    
    class Config:
        env_prefix = "SUPABASE_"

def initialize_supabase() -> Client:
    """Initialize and return a Supabase client."""
    load_dotenv()
    
    try:
        config = SupabaseConfig()
        logger.info("Connecting to Supabase...")
        client = create_client(config.url, config.key)
        logger.info("Supabase client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"ERROR initializing Supabase client: {str(e)}")
        raise RuntimeError("Failed to initialize Supabase client") from e

def check_api_key(client: Client, api_key: str) -> bool:
    """Verify if the API key is valid"""
    try:
        response = (client.table("users")
            .select("api_key")
            .eq("api_key", api_key)
            .execute())
        return len(response.data) > 0
    except Exception as e:
        logger.error(f"ERROR checking API key: {str(e)}")
        return False

def free_user_check(client: Client, api_key: str) -> bool:
    """Check if a free user has exceeded their API call limit"""
    logger.info("Checking free user limits...")
    try:
        response = (client.table("users")
            .select("api_calls")
            .eq("api_key", api_key)
            .execute())
        if not response.data:
            logger.warning("No user data found for API key")
            return True 
        api_calls = response.data[0]['api_calls']
        logger.info(f"User has made {api_calls} API calls")
        return api_calls >= 4
    except Exception as e:
        logger.error(f"ERROR checking free user limits: {str(e)}")
        return True

def error_perfect(client: Client, api_key: str, issue: Any) -> bool:
    """Check if this exact error has been seen before"""
    try:
        if issue:
            response = (client.table("logs")
                .select("issue")
                .eq("api_key", api_key)
                .eq("issue", str(issue))
                .gte("timestamp", (datetime.now() - timedelta(hours=24)).isoformat())
                .execute())
            return len(response.data) > 0
    except Exception as e:
        logger.error(f"ERROR checking for duplicate errors: {str(e)}")
    return False

def check_last_log(client: Client, api_key: str) -> bool:
    """Check if the user has submitted logs recently"""
    try:
        response = (client.table("logs")
            .select("timestamp")
            .eq("api_key", api_key)
            .gte("timestamp", (datetime.now() - timedelta(hours=1)).isoformat())
            .execute())
        return len(response.data) > 0
    except Exception as e:
        logger.error(f"ERROR checking for recent logs: {str(e)}")
        return False

def update_user_logs(client: Client, api_key: str, issue: Any, repo: str) -> bool:
    """Update user logs in the database"""
    logger.info("Updating logs for user...")
    try:
        client.table("users").update({
            "api_calls": client.raw("api_calls + 1"), 
            "last_log_time": datetime.now().isoformat(),
            "last_issue": str(issue),
            "repo_used": repo
        }).eq("api_key", api_key).execute()
        
        log_entry = LogEntry(api_key=api_key, issue=str(issue))
        client.table("logs").insert(log_entry.dict()).execute()
        
        logger.info("Database updated successfully")
        return True
    except Exception as e:
        logger.error(f"ERROR updating user logs in Supabase: {str(e)}")
        return False

def generate_api_key() -> str:
    """Generate a random API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))

    
def check_user_login(client: Client, username: str, password: str) -> bool:
    """Checks if the user is in the Database"""
    try:
        response = (client.table("users")
            .select("api_key")
            .eq("username", username)
            .eq("password", password)
            .execute())
        return response.data > 0 
    except Exception as e:
        logger.error(f"ERROR checking authenticating user: {str(e)}")
        return False
    
def repo_user_has_used(client: Client, api_key: str) -> set[str]:
    try:
        response = (client.table("users")
            .select("repos")
            .eq("api_key", api_key)
            .execute())
        return set(response.data)
    except Exception as e:
        logger.error(f"ERROR checking repos: {str(e)}")
        return False
    
def update_recommendations(client: Client, user_id: str, repository: str, file_name: str, 
                         old_code: str, new_code: str, response_data: str) -> bool:
    """Create or update recommendation in the database"""
    try:
        logger.info(f"Saving recommendation for repo: {repository}")
        
        # Insert new recommendation
        client.table("recommendations").insert({
            "repository": repository,
            "file_name": file_name,
            "old_code": old_code,
            "new_code": new_code,
            "response_data": response_data,
            "created_at": datetime.now().isoformat(),
            "user_id": user_id
        }).execute()
        
        logger.info("Recommendation saved successfully")
        return True
    except Exception as e:
        logger.error(f"ERROR updating recommendations in Supabase: {str(e)}")
        return False


supabase_client = initialize_supabase()
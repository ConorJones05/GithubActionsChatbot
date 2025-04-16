# Standard library imports
import json
import logging
import os
import secrets
import string
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

# Third-party imports
from fastapi import HTTPException
from pydantic import BaseModel, Field, root_validator, validator
from pydantic_settings import BaseSettings
from supabase import Client, create_client
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("supabase_logic")

# ----- Pydantic Models -----

class UserRole(str, Enum):
    """User role types"""
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"

class RepositoryInfo(BaseModel):
    """Information about a repository"""
    name: str
    url: Optional[str] = None
    last_accessed: Optional[datetime] = None

    class Config:
        frozen = True

class User(BaseModel):
    """User model with API key information"""
    user_id: str
    api_key: str
    username: Optional[str] = None
    email: Optional[str] = None
    api_calls: int = 0
    role: UserRole = UserRole.FREE
    last_log_time: Optional[datetime] = None
    last_issue: Optional[str] = None
    repo_used: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    

class LogEntry(BaseModel):
    """Log entry for user API calls"""
    id: Optional[str] = None
    api_key: str
    issue: str
    repository: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True

class Recommendation(BaseModel):
    """Recommendation model for code fixes"""
    id: Optional[str] = None
    repository: str
    file_name: str
    old_code: str
    new_code: str
    response_data: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    

class SupabaseConfig(BaseSettings):
    """Supabase connection configuration"""
    url: str
    key: str
    jwt_secret: Optional[str] = None
    
    class Config:
        env_prefix = "SUPABASE_"
        case_sensitive = False

class QueryResult(BaseModel):
    """Wrapper for Supabase query results"""
    success: bool
    data: Any = None
    error: Optional[str] = None

# ----- Helper Functions -----

def initialize_supabase() -> Client:
    """Initialize and return a Supabase client."""
    try:
        config = SupabaseConfig()
        logger.info("Connecting to Supabase...")
        client = create_client(config.url, config.key)
        logger.info("Supabase client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"ERROR initializing Supabase client: {str(e)}")
        raise RuntimeError("Failed to initialize Supabase client") from e

def generate_api_key(length: int = 32) -> str:
    """Generate a secure random API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def safely_execute_query(func):
    """Decorator to safely execute Supabase queries"""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return QueryResult(success=True, data=result)
        except Exception as e:
            logger.error(f"ERROR in {func.__name__}: {str(e)}")
            return QueryResult(success=False, error=str(e))
    return wrapper

# ----- User Management Functions -----

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

def check_user_login(client: Client, username: str, password: str) -> bool:
    """Checks if the user is in the Database"""
    try:
        response = (client.table("users")
            .select("api_key")
            .eq("username", username)
            .eq("password", password)
            .execute())
        return len(response.data) > 0 
    except Exception as e:
        logger.error(f"ERROR checking authenticating user: {str(e)}")
        return False

def get_user_by_api_key(client: Client, api_key: str) -> Optional[User]:
    """Get user details from API key"""
    try:
        response = (client.table("users")
            .select("*")
            .eq("api_key", api_key)
            .execute())
        
        if not response.data:
            return None
            
        user_data = response.data[0]
        return User.parse_obj(user_data)
    except Exception as e:
        logger.error(f"ERROR getting user by API key: {str(e)}")
        return None

def create_user(client: Client, user: User) -> bool:
    """Create a new user"""
    try:
        client.table("users").insert(user.dict(exclude={'id'})).execute()
        return True
    except Exception as e:
        logger.error(f"ERROR creating user: {str(e)}")
        return False

# ----- Usage Limit Functions -----

def free_user_check(client: Client, api_key: str) -> bool:
    """Check if a free user has exceeded their API call limit"""
    logger.info("Checking free user limits...")
    try:
        response = (client.table("users")
            .select("api_calls, role")
            .eq("api_key", api_key)
            .execute())
            
        if not response.data:
            logger.warning("No user data found for API key")
            return True 
            
        user_data = response.data[0]
        api_calls = user_data.get('api_calls', 0)
        role = user_data.get('role', 'free')
        
        logger.info(f"User has made {api_calls} API calls, role: {role}")
        
        if role.lower() == 'free':
            return api_calls >= 4
            
        return False
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

# ----- Repository and Log Functions -----

def get_user_repositories(client: Client, api_key: str) -> List[str]:
    """Get list of repositories the user has used"""
    try:
        response = (client.table("users")
            .select("repo_used")
            .eq("api_key", api_key)
            .execute())
            
        if not response.data or not response.data[0]:
            return []
            
        repos_data = response.data[0].get("repo_used", [])
        
        if isinstance(repos_data, list):
            return repos_data
        elif isinstance(repos_data, str):
            try:
                return json.loads(repos_data)
            except:
                return repos_data.split(',')
        return []
    except Exception as e:
        logger.error(f"ERROR getting user repositories: {str(e)}")
        return []

def update_user_logs(
    client: Client, 
    api_key: str, 
    issue: Any, 
    repo: str
) -> bool:
    """Update user logs in the database"""
    logger.info(f"Updating logs for user with repo: {repo}")
    try:
        # First, get the current user data
        response = client.table("users").select("repo_used,api_calls").eq("api_key", api_key).execute()
        
        if not response.data:
            logger.warning(f"No user found with API key: {api_key[:5]}...")
            return False
            
        current_repos = response.data[0].get("repo_used", [])
        current_api_calls = response.data[0].get("api_calls", 0)
        
        # Process repo list
        new_repos = process_repository_list(current_repos, repo)
        
        # Update user data with incremented api_calls count
        client.table("users").update({
            "api_calls": current_api_calls + 1,  # Manually increment instead of using raw()
            "last_log_time": datetime.now().isoformat(),
            "last_issue": str(issue),
            "repo_used": new_repos
        }).eq("api_key", api_key).execute()
        
        # Add log entry with ISO-formatted timestamp
        log_data = {
            "api_key": api_key,
            "issue": str(issue),
            "repository": repo,
            "timestamp": datetime.now().isoformat()
        }
        client.table("logs").insert(log_data).execute()
        
        logger.info(f"Database updated successfully with repo: {repo}")
        return True
    except Exception as e:
        logger.error(f"ERROR updating user logs in Supabase: {str(e)}")
        return False

def process_repository_list(current_repos: Any, new_repo: str) -> List[str]:
    """Process repository list to ensure it's in the correct format"""
    if not current_repos:
        return [new_repo]
    elif isinstance(current_repos, str):
        try:
            existing_repos = json.loads(current_repos)
            if not isinstance(existing_repos, list):
                existing_repos = [existing_repos]
            
            if new_repo not in existing_repos:
                existing_repos.append(new_repo)
            return existing_repos
        except json.JSONDecodeError:
            existing_repos = [r.strip() for r in current_repos.split(",") if r.strip()]
            if new_repo not in existing_repos:
                existing_repos.append(new_repo)
            return existing_repos
    elif isinstance(current_repos, list):
        if new_repo not in current_repos:
            current_repos.append(new_repo)
        return current_repos
    else:
        return [new_repo]

# ----- Recommendation Functions -----

def update_recommendations(
    client: Client, 
    user_id: str, 
    repository: str, 
    file_name: str, 
    old_code: str, 
    new_code: str, 
    response_data: str
) -> bool:
    """Create or update recommendation in the database"""
    try:
        logger.info(f"Saving recommendation for repo: {repository}")
        
        # Create recommendation dict with ISO-formatted datetime
        recommendation_data = {
            "repository": repository,
            "file_name": file_name,
            "old_code": old_code,
            "new_code": new_code,
            "response_data": response_data,
            "user_id": user_id,
            "created_at": datetime.now().isoformat()  # Convert to ISO string
        }
        
        client.table("recommendations").insert(recommendation_data).execute()
        
        logger.info("Recommendation saved successfully")
        return True
    except Exception as e:
        logger.error(f"ERROR updating recommendations in Supabase: {str(e)}")
        return False

def get_recommendations_for_user(
    client: Client, 
    user_id: str, 
    repository: Optional[str] = None
) -> List[Recommendation]:
    """Get recommendations for a user, optionally filtered by repository"""
    try:
        query = client.table("recommendations").select("*").eq("user_id", user_id)
        
        if repository:
            query = query.eq("repository", repository)
            
        response = query.order("created_at", desc=True).execute()
        
        if not response.data:
            return []
            
        recommendations = []
        for item in response.data:
            try:
                recommendations.append(Recommendation.parse_obj(item))
            except Exception as e:
                logger.error(f"Error parsing recommendation: {str(e)}")
                
        return recommendations
    except Exception as e:
        logger.error(f"ERROR getting recommendations: {str(e)}")
        return []


supabase_client = initialize_supabase()
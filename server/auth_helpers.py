# Standard library imports
import os
from typing import Dict, Any

# Third-party imports
from fastapi import HTTPException, Request
import jwt

def verify_auth_header(request: Request) -> Dict[str, Any]:
    """Verify authentication header and return payload."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = auth_header.split(" ")[1]
    return verify_jwt(token)

def verify_jwt(token: str) -> Dict[str, Any]:
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

def get_user_id(payload: Dict[str, Any]) -> str:
    """Extract user ID from JWT payload."""
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user ID")
    return user_id
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config.config import settings

# Define global client and database variables
client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None

async def get_db_client():
    """
    Dependency that returns the global MongoDB client.
    """
    if not client or not db:
        raise HTTPException(status_code=500, detail="Database connection is not available.")
    return db

# Security scheme for bearer token authentication
security = HTTPBearer()

def get_authenticated_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency that authenticates a user based on a bearer token.
    In a real app, this would validate the token against a service like Google.
    """
    # Placeholder for actual token validation
    if credentials and credentials.scheme == "Bearer" and credentials.credentials == "test-token":
        # Return a placeholder user ID for now
        return "test_user_id"
    
    raise HTTPException(
        status_code=401,
        detail="Invalid authentication credentials"
    )

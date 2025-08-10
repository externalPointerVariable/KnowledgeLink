from fastapi import APIRouter, HTTPException, status, Request
from app.config.config import settings
from app.model.link import Token


auth_router = APIRouter(prefix="/api/auth", tags=["auth"])

@auth_router.get("/google")
async def google_login():
    """
    Initiates the Google OAuth flow by redirecting the user to Google's sign-in page.
    """
    state = "some-random-state-string"
    scopes = "openid profile email"
    redirect_uri = "http://localhost:3000/api/auth/google/callback"
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"response_type=code&"
        f"scope={scopes}&"
        f"redirect_uri={redirect_uri}&"
        f"access_type=offline&"
        f"prompt=consent&"
        f"state={state}"
    )
    
    return {"url": auth_url}

@auth_router.get("/google/callback", response_model=Token)
async def google_callback(request: Request, code: str, state: str):
    """
    Handles the callback from Google after the user has authenticated.
    """
    if state != "some-random-state-string":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
        
    # Placeholder for token exchange logic
    return Token(access_token="test-token")

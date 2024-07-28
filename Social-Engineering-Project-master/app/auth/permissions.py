from fastapi import Request, HTTPException, status
from .auth import AuthHandler

auth_handler = AuthHandler()

async def admin_required(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token not found",
        )
    
    user = auth_handler.get_current_user(token)
    if not user or not auth_handler.is_admin(user.get("username", "")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )


async def authentication_required(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token not found",
        )
    
    user = auth_handler.get_current_user(token)
    if not user or not auth_handler.is_authenticated(user.get("username", "")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required",
        )
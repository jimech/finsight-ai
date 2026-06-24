from fastapi import APIRouter, Depends

from app.core.auth import AuthenticatedUser, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def get_me(user: AuthenticatedUser = Depends(get_current_user)):
    return {
        "clerk_user_id": user.clerk_user_id,
        "authenticated": True,
    }

from fastapi import APIRouter, Depends

from app.core.auth import get_current_db_user, get_current_user
from app.core.types import AuthenticatedUser
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def get_me(
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
    user: User = Depends(get_current_db_user),
):
    return {
        "authenticated": True,
        "clerk_user_id": authenticated_user.clerk_user_id,
        "user_id": str(user.id),
        "email": user.email,
    }

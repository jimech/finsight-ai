from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_db_user, get_current_user
from app.core.types import AuthenticatedUser
from app.db.session import get_db
from app.models.user import User
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.profile import update_user_profile
from app.services.users import get_or_create_user_from_auth

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(user: User = Depends(get_current_db_user)):
    return user


@router.put("", response_model=ProfileResponse)
def put_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
):
    user = get_or_create_user_from_auth(db, authenticated_user)
    return update_user_profile(db, user, data)

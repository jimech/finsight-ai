from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.types import AuthenticatedUser
from app.models.user import User


def _placeholder_email(clerk_user_id: str) -> str:
    return f"{clerk_user_id}@clerk.finsight.local"


def get_or_create_user_from_auth(
    db: Session,
    authenticated_user: AuthenticatedUser,
) -> User:
    existing = db.scalar(
        select(User).where(User.clerk_user_id == authenticated_user.clerk_user_id)
    )
    if existing is not None:
        return existing

    email = authenticated_user.email or _placeholder_email(
        authenticated_user.clerk_user_id
    )

    user = User(
        clerk_user_id=authenticated_user.clerk_user_id,
        email=email,
    )
    db.add(user)

    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(User).where(User.clerk_user_id == authenticated_user.clerk_user_id)
        )
        if existing is not None:
            return existing
        raise

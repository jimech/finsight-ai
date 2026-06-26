from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.profile import ProfileUpdate


def is_profile_complete(user: User) -> bool:
    return all(
        [
            user.name,
            user.monthly_income is not None,
            user.savings_goal is not None,
            user.current_savings is not None,
            user.financial_priority,
            user.coaching_tone,
        ]
    )


def update_user_profile(
    db: Session,
    user: User,
    data: ProfileUpdate,
) -> User:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user

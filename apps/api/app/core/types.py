from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class AuthenticatedUser:
    clerk_user_id: str
    email: Optional[str]
    claims: Dict[str, Any]

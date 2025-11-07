from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.auth import verify_firebase_token
from src.models.user import User
from typing import Dict


async def get_current_user(
    db: Session = Depends(get_db),
    token_data: Dict[str, str] = Depends(verify_firebase_token)
) -> User:
    """
    Get current authenticated user from database.

    Raises:
        HTTPException: If user not found in database.
    """
    user = db.query(User).filter(
        User.firebase_uid == token_data["uid"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please complete registration."
        )

    return user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require user to have admin role."""
    from src.models.user import UserRole

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user

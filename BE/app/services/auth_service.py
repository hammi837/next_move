"""
Authentication service — real JWT + bcrypt via sync DB stack.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token, decode_token,
    hash_password, verify_password,
)
from app.db.models import AppUser, UserRole
import logging

logger = logging.getLogger(__name__)


class AuthService:

    # ── Validation ────────────────────────────────────────────────────────

    @staticmethod
    def validate_email(email: str) -> bool:
        return bool(re.match(r'^[^@]+@[^@]+\.[^@]+$', email))

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        return True, "OK"

    # ── User creation ─────────────────────────────────────────────────────

    def register(self, db: Session, username: str, email: str,
                 password: str, full_name: str = "") -> AppUser:
        if not self.validate_email(email):
            raise ValueError("Invalid email format")
        ok, msg = self.validate_password(password)
        if not ok:
            raise ValueError(msg)

        if db.query(AppUser).filter(
            (AppUser.username == username) | (AppUser.email == email)
        ).first():
            raise ValueError("Username or email already taken")

        user = AppUser(
            username        = username,
            email           = email,
            hashed_password = hash_password(password),
            full_name       = full_name or username,
            role            = UserRole.FREE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"✅ Registered: {username}")
        return user

    # ── Login ─────────────────────────────────────────────────────────────

    def login(self, db: Session, username: str,
              password: str) -> Optional[AppUser]:
        user = db.query(AppUser).filter(
            (AppUser.username == username) | (AppUser.email == username)
        ).first()
        if not user or not verify_password(password, user.hashed_password):
            return None
        user.last_login = datetime.utcnow()
        db.commit()
        return user

    # ── Token ─────────────────────────────────────────────────────────────

    @staticmethod
    def issue_token(user: AppUser) -> str:
        return create_access_token({
            "sub":      str(user.id),
            "username": user.username,
            "role":     user.role.value,
        })

    @staticmethod
    def get_user_from_token(db: Session, token: str) -> Optional[AppUser]:
        payload = decode_token(token)
        if not payload:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        return db.query(AppUser).filter(AppUser.id == int(user_id)).first()


auth_service = AuthService()

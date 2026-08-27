"""
User Service for ChargeShield.
Handles User Record CRUD and explicit environment-based development seeding.
"""

from datetime import datetime, timezone
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.db.models import UserModel
from backend.services.auth_service import hash_password
from backend.core.logging import logger

VALID_ROLES = {"ADMIN", "ANALYST", "REVIEWER", "AUDITOR"}

def get_user_by_id(db: Session, user_id: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.user_id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.email == email).first()

def list_users(db: Session) -> List[UserModel]:
    return db.query(UserModel).order_by(UserModel.created_at.desc()).all()

def create_user(
    db: Session,
    email: str,
    username: str,
    password: str,
    role: str = "REVIEWER",
    full_name: str = "System User"
) -> UserModel:
    """Creates a new user record with securely hashed password."""
    role_upper = role.upper()
    if role_upper not in VALID_ROLES:
        raise ValueError(f"Invalid role '{role}'. Must be one of {VALID_ROLES}")

    existing_email = get_user_by_email(db, email)
    if existing_email:
        raise ValueError(f"User with email '{email}' already exists.")

    existing_user = get_user_by_username(db, username)
    if existing_user:
        raise ValueError(f"User with username '{username}' already exists.")

    user = UserModel(
        user_id=f"USR_{uuid.uuid4().hex[:8].upper()}",
        email=email.strip().lower(),
        username=username.strip(),
        hashed_password=hash_password(password),
        role=role_upper,
        full_name=full_name.strip(),
        is_active=1.0,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Created user '{user.username}' with role '{user.role}'.")
    return user

def update_user(
    db: Session,
    user_id: str,
    updates: Dict[str, Any]
) -> Optional[UserModel]:
    """Updates user attributes (role, full_name, is_active, password)."""
    user = get_user_id(db, user_id)
    if not user:
        return None

    if "role" in updates and updates["role"]:
        role_upper = updates["role"].upper()
        if role_upper in VALID_ROLES:
            user.role = role_upper

    if "full_name" in updates and updates["full_name"]:
        user.full_name = updates["full_name"].strip()

    if "password" in updates and updates["password"]:
        user.hashed_password = hash_password(updates["password"])

    if "is_active" in updates:
        user.is_active = 1.0 if updates["is_active"] else 0.0

    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: str) -> bool:
    """Deletes a user account from database."""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    logger.info(f"Deleted user account '{user_id}'.")
    return True

def seed_dev_users(db: Session, admin_username: str = "admin", admin_password: str = "AdminPass123!") -> List[UserModel]:
    """
    Explicit seed function for development environment.
    Populates four role-specific test accounts: ADMIN, ANALYST, REVIEWER, AUDITOR.
    Only called when explicitly invoked via CLI script or SEED_DEV_USER=true.
    """
    created_users = []
    default_accounts = [
        {"username": admin_username, "email": f"{admin_username}@chargeshield.io", "password": admin_password, "role": "ADMIN", "name": "System Administrator"},
        {"username": "analyst", "email": "analyst@chargeshield.io", "password": admin_password, "role": "ANALYST", "name": "Lead Risk Analyst"},
        {"username": "reviewer", "email": "reviewer@chargeshield.io", "password": admin_password, "role": "REVIEWER", "name": "Sarah Jenkins (Reviewer)"},
        {"username": "auditor", "email": "auditor@chargeshield.io", "password": admin_password, "role": "AUDITOR", "name": "Compliance Auditor"}
    ]

    for acc in default_accounts:
        existing = get_user_by_username(db, acc["username"])
        if not existing:
            u = create_user(
                db=db,
                email=acc["email"],
                username=acc["username"],
                password=acc["password"],
                role=acc["role"],
                full_name=acc["name"]
            )
            created_users.append(u)
        else:
            logger.info(f"Seed user '{acc['username']}' already exists.")

    return created_users

"""
Authentication & User Management API Endpoints for ChargeShield.
Supports Login, Current User Profile, Session Logout, and Admin User CRUD.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import UserModel
from backend.services.auth_service import (
    verify_password,
    create_access_token,
    revoke_token
)
from backend.services.user_service import (
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    create_user,
    update_user,
    delete_user,
    list_users
)
from backend.api.dependencies import get_current_user, require_role
from backend.core.logging import logger

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & User Management"])
users_router = APIRouter(prefix="/api/v1/users", tags=["User Management (Admin)"])

# Schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    full_name: str
    is_active: bool
    created_at: str

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class UserCreateRequest(BaseModel):
    email: str
    username: str
    password: str
    role: str = "REVIEWER"
    full_name: str

class UserUpdateRequest(BaseModel):
    role: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/login", response_model=TokenResponse, summary="User Authentication Login")
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates user credentials (username/email and password).
    Returns signed JWT bearer token and user profile details.
    Password hashes are NEVER exposed.
    """
    username_or_email = credentials.username.strip()
    user = get_user_by_username(db, username_or_email)
    if not user:
        user = get_user_by_email(db, username_or_email)

    if not user or not verify_password(credentials.password, user.hashed_password):
        logger.warning(f"Failed login attempt for username/email: '{credentials.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if user.is_active <= 0.0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Contact system administrator."
        )

    token_data = {
        "sub": user.user_id,
        "username": user.username,
        "email": user.email,
        "role": user.role
    }
    access_token = create_access_token(token_data)

    user_resp = UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        is_active=bool(user.is_active > 0.0),
        created_at=user.created_at
    )

    logger.info(f"Successful login for user '{user.username}' ({user.role}).")
    return TokenResponse(access_token=access_token, user=user_resp)


@router.get("/me", response_model=UserResponse, summary="Get Current Authenticated User Profile")
async def get_me(current_user: UserModel = Depends(get_current_user)):
    """Returns profile information for currently logged-in user."""
    return UserResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        full_name=current_user.full_name,
        is_active=bool(current_user.is_active > 0.0),
        created_at=current_user.created_at
    )


@router.post("/logout", summary="User Session Logout")
async def logout(
    authorization: Optional[str] = Header(None),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Invalidates current session JWT token by adding it to the server revocation blacklist.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        revoke_token(token)

    logger.info(f"User '{current_user.username}' logged out successfully.")
    return {"message": "Logged out successfully. Token invalidated."}


# Admin User Management Endpoints

@users_router.get("", response_model=List[UserResponse], summary="List All Users (Admin Only)")
async def get_all_users(
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_role(["ADMIN"]))
):
    """Lists all system user accounts. Restricted to ADMIN role."""
    users = list_users(db)
    return [
        UserResponse(
            user_id=u.user_id,
            username=u.username,
            email=u.email,
            role=u.role,
            full_name=u.full_name,
            is_active=bool(u.is_active > 0.0),
            created_at=u.created_at
        ) for u in users
    ]


@users_router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create User Account (Admin Only)")
async def create_new_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_role(["ADMIN"]))
):
    """Creates a new user account with specified role. Restricted to ADMIN role."""
    try:
        u = create_user(
            db=db,
            email=payload.email,
            username=payload.username,
            password=payload.password,
            role=payload.role,
            full_name=payload.full_name
        )
        return UserResponse(
            user_id=u.user_id,
            username=u.username,
            email=u.email,
            role=u.role,
            full_name=u.full_name,
            is_active=bool(u.is_active > 0.0),
            created_at=u.created_at
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(val_err))


@users_router.patch("/{user_id}", response_model=UserResponse, summary="Update User Account (Admin Only)")
async def update_user_account(
    user_id: str,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_role(["ADMIN"]))
):
    """Updates user role, name, active status, or password. Restricted to ADMIN role."""
    u = update_user(db, user_id, payload.model_dump(exclude_unset=True))
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{user_id}' not found.")

    return UserResponse(
        user_id=u.user_id,
        username=u.username,
        email=u.email,
        role=u.role,
        full_name=u.full_name,
        is_active=bool(u.is_active > 0.0),
        created_at=u.created_at
    )


@users_router.delete("/{user_id}", status_code=status.HTTP_200_OK, summary="Delete User Account (Admin Only)")
async def delete_user_account(
    user_id: str,
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_role(["ADMIN"]))
):
    """Deletes a user account. Restricted to ADMIN role."""
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{user_id}' not found.")
    return {"message": f"User '{user_id}' successfully deleted."}

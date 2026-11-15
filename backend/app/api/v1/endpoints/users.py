from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User, UserProfile
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Retrieve personal profile and workspace details for the authenticated user."""
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user information and profile attributes",
)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Update profile data (headline, target role, links, preferences)."""
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    if user_update.profile is not None:
        # Ensure profile exists
        if current_user.profile is None:
            current_user.profile = UserProfile(user_id=current_user.id)
            db.add(current_user.profile)

        profile_data = user_update.profile.model_dump(exclude_unset=True)
        for key, value in profile_data.items():
            setattr(current_user.profile, key, value)

    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Permanently delete user account and all workspace data (GDPR Purge)",
)
async def delete_my_account(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Permanently delete user account and trigger cascading deletion of all resumes, JDs, and data."""
    await db.delete(current_user)
    await db.commit()
    return {
        "status": "deleted",
        "message": "User account and all associated workspace data have been permanently purged.",
    }

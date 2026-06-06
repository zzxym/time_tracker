"""Admin API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.models.activity import Activity

router = APIRouter()


@router.get("/users/count")
async def get_user_count(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get total user count (admin only).

    Args:
        current_user: Admin user info.
        db: Database session.

    Returns:
        User count.
    """
    result = await db.execute(select(func.count()).select_from(User))
    count = result.scalar() or 0
    return {"code": 0, "data": {"count": count}, "message": "OK"}


@router.get("/activities/count")
async def get_activity_count(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get total activity count (admin only).

    Args:
        current_user: Admin user info.
        db: Database session.

    Returns:
        Activity count.
    """
    result = await db.execute(select(func.count()).select_from(Activity))
    count = result.scalar() or 0
    return {"code": 0, "data": {"count": count}, "message": "OK"}


@router.get("/users")
async def list_users(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only).

    Args:
        page: Page number.
        page_size: Items per page.
        current_user: Admin user info.
        db: Database session.

    Returns:
        Paginated list of users.
    """
    offset = (page - 1) * page_size
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()

    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar() or 0

    return {
        "code": 0,
        "data": {
            "items": [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "role": u.role,
                    "created_at": str(u.created_at),
                }
                for u in users
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        "message": "OK",
    }

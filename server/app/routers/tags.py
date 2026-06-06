"""Tags API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from app.database import get_db
from app.dependencies import get_current_user
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate, TagResponse

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def list_tags(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all tags for the current user.

    Args:
        current_user: Authenticated user info.
        db: Database session.

    Returns:
        List of tags.
    """
    result = await db.execute(
        select(Tag)
        .where(Tag.user_id == current_user["user_id"])
        .order_by(Tag.created_at.desc())
    )
    tags = result.scalars().all()
    return [TagResponse.model_validate(t) for t in tags]


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new tag.

    Args:
        data: Tag creation data.
        current_user: Authenticated user info.
        db: Database session.

    Returns:
        Created tag data.
    """
    tag = Tag(
        id=str(uuid.uuid4()),
        user_id=current_user["user_id"],
        name=data.name,
        color=data.color,
    )
    db.add(tag)
    await db.flush()
    return TagResponse.model_validate(tag)


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: str,
    data: TagUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a tag.

    Args:
        tag_id: Tag UUID.
        data: Update data.
        current_user: Authenticated user info.
        db: Database session.

    Returns:
        Updated tag data.
    """
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user["user_id"])
    )
    tag = result.scalars().first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": 40401, "message": "Tag not found"},
        )

    if data.name is not None:
        tag.name = data.name
    if data.color is not None:
        tag.color = data.color

    await db.flush()
    return TagResponse.model_validate(tag)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a tag.

    Args:
        tag_id: Tag UUID.
        current_user: Authenticated user info.
        db: Database session.
    """
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user["user_id"])
    )
    tag = result.scalars().first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": 40401, "message": "Tag not found"},
        )

    await db.delete(tag)
    await db.flush()

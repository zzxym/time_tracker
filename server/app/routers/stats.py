"""Statistics and export API router."""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import io

from app.database import get_db
from app.dependencies import get_current_user
from app.models.activity import Activity
from app.services.export_service import ExportService

router = APIRouter()


@router.get("/summary")
async def get_stats_summary(
    period: str = Query("day", description="Period: day, week, month"),
    date: str = Query(None, description="Reference date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get statistics summary for a time period.

    Args:
        period: Time period (day, week, month).
        date: Reference date in YYYY-MM-DD format.
        current_user: Authenticated user info.
        db: Database session.

    Returns:
        Statistics summary with total duration and activity breakdown.
    """
    user_id = current_user["user_id"]

    # Calculate date range
    if date:
        ref_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        ref_date = datetime.now(timezone.utc)

    if period == "day":
        start_date = ref_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif period == "week":
        start_date = ref_date.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date - timedelta(days=start_date.weekday())
        end_date = start_date + timedelta(weeks=1)
    else:  # month
        start_date = ref_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)

    # Query activities within the date range
    result = await db.execute(
        select(Activity).where(
            Activity.user_id == user_id,
            Activity.started_at >= start_date,
            Activity.started_at < end_date,
        )
    )
    activities = result.scalars().all()

    # Calculate statistics
    total_duration = 0
    activity_stats = []
    for act in activities:
        duration = act.total_duration_seconds
        # Add current running segment if applicable
        if act.status == "RUNNING" and act.time_segments:
            for seg in act.time_segments:
                if seg.end_time is None:
                    running_seconds = (datetime.now(timezone.utc) - seg.start_time).total_seconds()
                    duration += int(running_seconds)
                    break

        total_duration += duration
        activity_stats.append({
            "activity_id": act.id,
            "activity_name": act.name,
            "activity_color": act.color,
            "total_duration_seconds": duration,
        })

    # Calculate percentages
    for stat in activity_stats:
        stat["percentage"] = round(stat["total_duration_seconds"] / total_duration * 100, 1) if total_duration > 0 else 0

    return {
        "code": 0,
        "data": {
            "total_duration_seconds": total_duration,
            "activity_count": len(activities),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "activities": activity_stats,
        },
        "message": "OK",
    }


@router.get("/export")
async def export_activities(
    format: str = Query("csv", description="Export format: csv, excel, json"),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export activities data in various formats.

    Args:
        format: Export format (csv, excel, json).
        start_date: Optional start date filter.
        end_date: Optional end date filter.
        current_user: Authenticated user info.
        db: Database session.

    Returns:
        File download response.
    """
    user_id = current_user["user_id"]

    # Build query
    query = select(Activity).where(Activity.user_id == user_id)
    if start_date:
        query = query.where(Activity.started_at >= datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc))
    if end_date:
        query = query.where(Activity.started_at < datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1))

    query = query.order_by(Activity.created_at.desc())
    result = await db.execute(query)
    activities = result.scalars().all()

    # Convert to dict list
    data = []
    for act in activities:
        data.append({
            "id": act.id,
            "name": act.name,
            "color": act.color,
            "status": act.status,
            "is_parallel": act.is_parallel,
            "started_at": str(act.started_at) if act.started_at else "",
            "ended_at": str(act.ended_at) if act.ended_at else "",
            "total_duration_seconds": act.total_duration_seconds,
            "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in (act.tags or [])],
            "created_at": str(act.created_at),
        })

    export_service = ExportService()

    if format == "csv":
        csv_content = await export_service.export_csv(data)
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=activities.csv"},
        )
    elif format == "excel":
        excel_bytes = await export_service.export_excel(data)
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=activities.xlsx"},
        )
    elif format == "json":
        json_content = await export_service.export_json(data)
        return StreamingResponse(
            io.StringIO(json_content),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=activities.json"},
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 40001, "message": f"Unsupported export format: {format}"},
        )

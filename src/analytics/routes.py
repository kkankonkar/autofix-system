"""
FastAPI routes for analytics API endpoints.

Provides CRUD operations for analytics events and dashboard aggregations.
"""

from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..middleware.auth import verify_api_key
from .service import analytics_service
from .aggregations import aggregation_service
from .schemas import (
    AnalyticsEventCreate,
    AnalyticsEventResponse,
    EventListResponse,
    DashboardSummary,
    TimelineData,
    RepositoryBreakdown,
    PullRequestSummary,
)

# Create router
router = APIRouter(prefix="/api/v1", tags=["analytics"])

# Analytics CRUD endpoints


@router.post(
    "/analytics",
    response_model=AnalyticsEventResponse,
    status_code=201,
    summary="Create analytics event",
    description="Submit analytics data from Fixium code review, documentation analysis, impact analysis, or fix implementation",
)
async def create_event(
    event: AnalyticsEventCreate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """
    Create a new analytics event.

    **Event Types:**
    - `review`: Code review findings
    - `updatedocs`: Documentation analysis
    - `analyzeimpact`: Impact analysis results
    - `implementfix`: Fix implementation tracking

    **Required Fields by Type:**
    - `review`: Must include `review` object with findings
    - `updatedocs`: Must include `documentation` object
    - `analyzeimpact`: Must include `impact` object with risk metrics
    - `implementfix`: Must include `fix` object with implementation details
    """
    try:
        result = analytics_service.create_event(db, event)
        return AnalyticsEventResponse(
            success=True,
            data=result["data"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")


@router.get(
    "/analytics/{event_id}",
    response_model=dict,
    summary="Get analytics event",
    description="Retrieve details of a single analytics event by its ID",
)
async def get_event(
    event_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get a specific analytics event by ID."""
    event = analytics_service.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event with ID {event_id} not found")

    return {"success": True, "data": event}


@router.get(
    "/analytics",
    response_model=EventListResponse,
    summary="List analytics events",
    description="Get a paginated list of analytics events with optional filtering",
)
async def list_events(
    start_date: Optional[datetime] = Query(None, description="Filter events after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events before this date"),
    repository: Optional[str] = Query(None, description="Filter by repository (owner/repo format)"),
    event_type: Optional[str] = Query(
        None,
        description="Filter by event type",
        regex="^(review|updatedocs|analyzeimpact|implementfix)$",
    ),
    limit: int = Query(50, ge=1, le=100, description="Number of events per page"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """
    List analytics events with filtering and pagination.

    **Filters:**
    - `start_date`: ISO 8601 datetime (e.g., 2026-05-01T00:00:00Z)
    - `end_date`: ISO 8601 datetime
    - `repository`: Format "owner/repo"
    - `event_type`: One of review, updatedocs, analyzeimpact, implementfix

    **Pagination:**
    - `limit`: Max 100 events per page
    - `offset`: Skip N events for pagination
    """
    events = analytics_service.get_events(
        db,
        start_date=start_date,
        end_date=end_date,
        repository=repository,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )

    total = analytics_service.get_event_count(
        db,
        start_date=start_date,
        end_date=end_date,
        repository=repository,
        event_type=event_type,
    )

    return EventListResponse(
        success=True,
        data={
            "events": events,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "hasMore": offset + len(events) < total,
            },
        },
    )


@router.delete(
    "/analytics/{event_id}",
    summary="Delete analytics event",
    description="Remove an analytics event from the database (admin only)",
)
async def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Delete an analytics event by ID."""
    deleted = analytics_service.delete_event(db, event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Event with ID {event_id} not found")

    return {"success": True, "message": "Event deleted successfully"}


# Dashboard aggregation endpoints


@router.get(
    "/dashboard/summary",
    response_model=dict,
    summary="Get dashboard summary",
    description="Retrieve aggregated metrics for the dashboard including total events, costs, and breakdowns by type",
)
async def get_dashboard_summary(
    start_date: Optional[datetime] = Query(None, description="Start date for metrics (defaults to 30 days ago)"),
    end_date: Optional[datetime] = Query(None, description="End date for metrics (defaults to now)"),
    repository: Optional[str] = Query(None, description="Filter by repository (owner/repo format)"),
    db: Session = Depends(get_db),
):
    """
    Get dashboard summary statistics.

    **Default Period:** Last 30 days if dates not provided

    **Metrics Included:**
    - Total events count
    - Total cost (coins and dollars)
    - Events breakdown by type
    - Average duration
    """
    # Default to last 30 days
    end = end_date or datetime.utcnow()
    start = start_date or (end - timedelta(days=30))

    metrics = aggregation_service.get_dashboard_summary(
        db, start_date=start, end_date=end, repository=repository
    )

    return {
        "success": True,
        "data": {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "metrics": metrics,
        },
    }


@router.get(
    "/dashboard/timeline",
    response_model=dict,
    summary="Get timeline data",
    description="Retrieve time-series data showing events and costs over time",
)
async def get_timeline(
    start_date: Optional[datetime] = Query(None, description="Start date (defaults to 30 days ago)"),
    end_date: Optional[datetime] = Query(None, description="End date (defaults to now)"),
    repository: Optional[str] = Query(None, description="Filter by repository"),
    granularity: str = Query(
        "daily",
        regex="^(daily|weekly|monthly)$",
        description="Time granularity for aggregation",
    ),
    db: Session = Depends(get_db),
):
    """
    Get timeline data for charts.

    **Granularity Options:**
    - `daily`: Group by day
    - `weekly`: Group by week
    - `monthly`: Group by month

    **Returns:** Array of data points with date, event count, cost, and breakdown by type
    """
    # Default to last 30 days
    end = end_date or datetime.utcnow()
    start = start_date or (end - timedelta(days=30))

    timeline = aggregation_service.get_timeline(
        db,
        start_date=start,
        end_date=end,
        repository=repository,
        granularity=granularity,
    )

    return {"success": True, "data": {"timeline": timeline, "granularity": granularity}}


@router.get(
    "/dashboard/repositories",
    response_model=dict,
    summary="Get repository breakdown",
    description="Retrieve metrics grouped by repository",
)
async def get_repository_breakdown(
    start_date: Optional[datetime] = Query(None, description="Start date (defaults to 30 days ago)"),
    end_date: Optional[datetime] = Query(None, description="End date (defaults to now)"),
    db: Session = Depends(get_db),
):
    """
    Get repository breakdown.

    **Returns:** List of repositories with:
    - Event count
    - Total cost
    - Breakdown by event type
    """
    # Default to last 30 days
    end = end_date or datetime.utcnow()
    start = start_date or (end - timedelta(days=30))

    repositories = aggregation_service.get_repository_breakdown(db, start_date=start, end_date=end)

    return {"success": True, "data": {"repositories": repositories}}


@router.get(
    "/dashboard/pull-requests",
    response_model=dict,
    summary="Get recent pull requests",
    description="Retrieve a list of recent pull requests with their analytics",
)
async def get_recent_pull_requests(
    limit: int = Query(10, ge=1, le=50, description="Number of PRs to return"),
    offset: int = Query(0, ge=0, description="Number of PRs to skip"),
    repository: Optional[str] = Query(None, description="Filter by repository"),
    db: Session = Depends(get_db),
):
    """
    Get recent pull requests with analytics.

    **Returns:** List of PRs with:
    - PR number, title, repository, author
    - Event count
    - Total cost
    - Last activity timestamp
    - Review findings summary
    """
    result = aggregation_service.get_recent_pull_requests(
        db, limit=limit, offset=offset, repository=repository
    )

    return {"success": True, "data": result}


# Health check endpoint
@router.get("/health", summary="Health check", description="Check API health status")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

# Made with Bob

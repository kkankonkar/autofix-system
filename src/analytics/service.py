"""
Analytics service for CRUD operations on analytics events.
Migrated from Node.js/MongoDB to Python/MySQL.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid
import logging

from src.analytics.models import (
    AnalyticsEvent,
    ReviewDetails,
    DocumentationDetails,
    ImpactDetails,
    FixDetails,
    EventType
)
from src.analytics.schemas import AnalyticsEventCreate

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for managing analytics events"""

    def create_event(
        self,
        db: Session,
        event_data: AnalyticsEventCreate
    ) -> Dict[str, Any]:
        """
        Create a new analytics event.
        
        Args:
            db: Database session
            event_data: Event data from request
            
        Returns:
            Dict with success status and event details
        """
        try:
            # Generate event ID
            event_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()

            # Create main event record
            event = AnalyticsEvent(
                id=event_id,
                event_type=event_data.eventType,
                timestamp=timestamp,
                github_type=event_data.github.type,
                github_number=event_data.github.number,
                github_title=event_data.github.title,
                github_url=event_data.github.url,
                github_repository=event_data.github.repository,
                github_author=event_data.github.author,
                github_branch=event_data.github.branch,
                github_base_branch=event_data.github.baseBranch,
                github_labels=event_data.github.labels or [],
                cost_coins_used=event_data.cost.coinsUsed,
                cost_dollars_used=event_data.cost.dollarsUsed,
                cost_operation=event_data.cost.operation,
                metadata_triggered_by=event_data.metadata.triggeredBy,
                metadata_duration=event_data.metadata.duration,
                metadata_status=event_data.metadata.status,
                metadata_workflow_run_id=event_data.metadata.workflowRun.id if event_data.metadata.workflowRun else None,
                metadata_workflow_run_url=event_data.metadata.workflowRun.url if event_data.metadata.workflowRun else None,
                metadata_fixium_version=event_data.metadata.fixiumVersion
            )

            db.add(event)

            # Add event-specific details based on event type
            if event_data.eventType == EventType.REVIEW and event_data.review:
                review = ReviewDetails(
                    event_id=event_id,
                    total_findings=event_data.review.totalFindings,
                    critical_count=event_data.review.critical,
                    high_count=event_data.review.high,
                    medium_count=event_data.review.medium,
                    low_count=event_data.review.low,
                    files_reviewed=event_data.review.filesReviewed,
                    lines_reviewed=event_data.review.linesReviewed,
                    findings_by_type=event_data.review.findingsByType,
                    filters=event_data.review.filters
                )
                db.add(review)

            elif event_data.eventType == EventType.UPDATEDOCS and event_data.documentation:
                doc = DocumentationDetails(
                    event_id=event_id,
                    classification_type=event_data.documentation.classification.type,
                    classification_confidence=event_data.documentation.classification.confidence,
                    classification_reasoning=event_data.documentation.classification.reasoning,
                    files_analyzed=event_data.documentation.filesAnalyzed,
                    suggestions_count=event_data.documentation.suggestionsCount,
                    high_priority_count=event_data.documentation.highPriority,
                    medium_priority_count=event_data.documentation.mediumPriority,
                    low_priority_count=event_data.documentation.lowPriority,
                    affected_files=event_data.documentation.affectedFiles or [],
                    forced=event_data.documentation.forced
                )
                db.add(doc)

            elif event_data.eventType == EventType.ANALYZEIMPACT and event_data.impact:
                impact = ImpactDetails(
                    event_id=event_id,
                    risk_score=event_data.impact.riskScore,
                    risk_level=event_data.impact.riskLevel,
                    direct_dependencies=event_data.impact.directDependencies,
                    downstream_impact=event_data.impact.downstreamImpact,
                    test_coverage_status=event_data.impact.testCoverage.status if event_data.impact.testCoverage else None,
                    test_coverage_files_found=event_data.impact.testCoverage.filesFound if event_data.impact.testCoverage else None,
                    test_coverage_needs_update=event_data.impact.testCoverage.needsUpdate if event_data.impact.testCoverage else None,
                    api_endpoints_total=event_data.impact.apiEndpoints.total if event_data.impact.apiEndpoints else None,
                    api_endpoints_new=event_data.impact.apiEndpoints.new if event_data.impact.apiEndpoints else None,
                    api_endpoints_modified=event_data.impact.apiEndpoints.modified if event_data.impact.apiEndpoints else None,
                    api_endpoints_breaking=event_data.impact.apiEndpoints.breaking if event_data.impact.apiEndpoints else None,
                    database_tables_affected=event_data.impact.databaseChanges.tablesAffected if event_data.impact.databaseChanges else None,
                    database_schema_changes=event_data.impact.databaseChanges.schemaChanges if event_data.impact.databaseChanges else None,
                    recommendations_count=event_data.impact.recommendationsCount,
                    high_priority_recommendations=event_data.impact.highPriorityRecommendations,
                    affected_components=event_data.impact.affectedComponents or []
                )
                db.add(impact)

            elif event_data.eventType == EventType.IMPLEMENTFIX and event_data.fix:
                fix = FixDetails(
                    event_id=event_id,
                    files_modified=event_data.fix.filesModified,
                    lines_added=event_data.fix.linesAdded,
                    lines_removed=event_data.fix.linesRemoved,
                    tests_added=event_data.fix.testsAdded,
                    tests_modified=event_data.fix.testsModified,
                    fix_complexity=event_data.fix.fixComplexity,
                    verification_status=event_data.fix.verificationStatus
                )
                db.add(fix)

            # Commit transaction
            db.commit()

            logger.info(f"Analytics event created: {event_id}, type: {event_data.eventType}, repo: {event_data.github.repository}")

            return {
                "success": True,
                "data": {
                    "eventId": event_id,
                    "eventType": event_data.eventType.value,
                    "timestamp": timestamp.isoformat()
                }
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create analytics event: {e}")
            raise

    def get_event_by_id(
        self,
        db: Session,
        event_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single event by ID.
        
        Args:
            db: Database session
            event_id: Event ID
            
        Returns:
            Event dictionary or None if not found
        """
        try:
            event = db.query(AnalyticsEvent).filter(AnalyticsEvent.id == event_id).first()
            return self._event_to_dict(event) if event else None
        except Exception as e:
            logger.error(f"Failed to get event by ID: {e}")
            raise

    def _event_to_dict(self, event: AnalyticsEvent) -> Dict[str, Any]:
        """Convert AnalyticsEvent model to dictionary for JSON serialization."""
        return {
            "id": event.id,
            "event_type": event.event_type.value if hasattr(event.event_type, 'value') else event.event_type,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "github_type": event.github_type.value if hasattr(event.github_type, 'value') else event.github_type,
            "github_number": event.github_number,
            "github_title": event.github_title,
            "github_url": event.github_url,
            "github_repository": event.github_repository,
            "github_author": event.github_author,
            "github_branch": event.github_branch,
            "github_base_branch": event.github_base_branch,
            "github_labels": event.github_labels,
            "cost_coins_used": event.cost_coins_used,
            "cost_dollars_used": float(event.cost_dollars_used) if event.cost_dollars_used else 0.0,
            "cost_operation": event.cost_operation,
            "metadata_triggered_by": event.metadata_triggered_by,
            "metadata_duration": event.metadata_duration,
            "metadata_status": event.metadata_status,
            "metadata_workflow_run_id": event.metadata_workflow_run_id,
            "metadata_workflow_run_url": event.metadata_workflow_run_url,
            "metadata_fixium_version": event.metadata_fixium_version,
        }

    def get_events(
        self,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        repository: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get events with filtering and pagination.
        
        Args:
            db: Database session
            start_date: Filter events after this date
            end_date: Filter events before this date
            repository: Filter by repository
            event_type: Filter by event type
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            List of event dictionaries
        """
        try:
            query = db.query(AnalyticsEvent)

            # Apply filters
            filters = []
            if start_date:
                filters.append(AnalyticsEvent.timestamp >= start_date)
            if end_date:
                filters.append(AnalyticsEvent.timestamp <= end_date)
            if repository:
                filters.append(AnalyticsEvent.github_repository == repository)
            if event_type:
                filters.append(AnalyticsEvent.event_type == event_type)

            if filters:
                query = query.filter(and_(*filters))

            # Apply ordering and pagination
            query = query.order_by(AnalyticsEvent.timestamp.desc())
            query = query.offset(offset).limit(limit)

            events = query.all()
            return [self._event_to_dict(event) for event in events]

        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            raise

    def get_event_count(
        self,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        repository: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> int:
        """
        Get total count of events matching filters.
        
        Args:
            db: Database session
            start_date: Filter events after this date
            end_date: Filter events before this date
            repository: Filter by repository
            event_type: Filter by event type
            
        Returns:
            int: Total count of matching events
        """
        try:
            query = db.query(AnalyticsEvent)

            # Apply filters
            filters = []
            if start_date:
                filters.append(AnalyticsEvent.timestamp >= start_date)
            if end_date:
                filters.append(AnalyticsEvent.timestamp <= end_date)
            if repository:
                filters.append(AnalyticsEvent.github_repository == repository)
            if event_type:
                filters.append(AnalyticsEvent.event_type == event_type)

            if filters:
                query = query.filter(and_(*filters))

            return query.count()

        except Exception as e:
            logger.error(f"Failed to get event count: {e}")
            raise

    def delete_event(
        self,
        db: Session,
        event_id: str
    ) -> bool:
        """
        Delete an event by ID.
        
        Args:
            db: Database session
            event_id: Event ID to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            event = db.query(AnalyticsEvent).filter(AnalyticsEvent.id == event_id).first()
            
            if not event:
                return False
            
            db.delete(event)
            db.commit()
            
            logger.info(f"Analytics event deleted: {event_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete event: {e}")
            raise


# Singleton instance
analytics_service = AnalyticsService()

# Made with Bob

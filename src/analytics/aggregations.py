"""
Analytics aggregation service for dashboard queries.
Migrated from Node.js/MongoDB to Python/MySQL.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import func, case, and_, distinct
from sqlalchemy.orm import Session
from src.analytics.models import (
    AnalyticsEvent,
    ReviewDetails,
    EventType,
    GitHubType
)
import logging

logger = logging.getLogger(__name__)


class AggregationService:
    """Service for aggregating analytics data for dashboard"""

    def get_dashboard_summary(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        repository: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get dashboard summary statistics.
        
        Equivalent to MongoDB aggregation:
        - Total PRs reviewed
        - Total coins used
        - Average coins per PR
        - Active reviewers count
        """
        try:
            # Build base query
            query = db.query(
                # Total PRs reviewed (only review events on PRs)
                func.sum(
                    case(
                        (
                            and_(
                                AnalyticsEvent.github_type == GitHubType.PR,
                                AnalyticsEvent.event_type == EventType.REVIEW
                            ),
                            1
                        ),
                        else_=0
                    )
                ).label('total_prs_reviewed'),
                # Total coins used
                func.sum(AnalyticsEvent.cost_coins_used).label('total_coins_used'),
                # Count distinct reviewers
                func.count(distinct(AnalyticsEvent.metadata_triggered_by)).label('active_reviewers')
            ).filter(
                AnalyticsEvent.timestamp >= start_date,
                AnalyticsEvent.timestamp <= end_date
            )

            # Add repository filter if provided
            if repository:
                query = query.filter(AnalyticsEvent.github_repository == repository)

            result = query.first()

            # Calculate metrics (convert Decimal to native Python types)
            total_prs = int(result.total_prs_reviewed or 0)
            total_coins = float(result.total_coins_used or 0)
            active_reviewers = int(result.active_reviewers or 0)

            # Calculate average coins per PR
            avg_coins_per_pr = round(total_coins / total_prs, 2) if total_prs > 0 else 0.0

            return {
                'totalPRsReviewed': total_prs,
                'totalCoinsUsed': round(total_coins, 2),
                'avgCoinsPerPR': avg_coins_per_pr,
                'activeReviewers': active_reviewers
            }

        except Exception as e:
            logger.error(f"Failed to get dashboard summary: {e}")
            raise

    def get_timeline(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        repository: Optional[str] = None,
        granularity: str = 'daily'
    ) -> List[Dict[str, Any]]:
        """
        Get timeline data for charts.
        
        Groups events by date with specified granularity (daily/weekly/monthly).
        """
        try:
            # Determine date truncation based on granularity
            if granularity == 'daily':
                date_trunc = func.date(AnalyticsEvent.timestamp)
            elif granularity == 'weekly':
                # MySQL: YEARWEEK function
                date_trunc = func.concat(
                    func.year(AnalyticsEvent.timestamp),
                    '-W',
                    func.lpad(func.week(AnalyticsEvent.timestamp), 2, '0')
                )
            elif granularity == 'monthly':
                date_trunc = func.date_format(AnalyticsEvent.timestamp, '%Y-%m')
            else:
                date_trunc = func.date(AnalyticsEvent.timestamp)

            # Build query
            query = db.query(
                date_trunc.label('date'),
                func.sum(AnalyticsEvent.cost_coins_used).label('coins_used'),
                func.sum(
                    case(
                        (
                            and_(
                                AnalyticsEvent.github_type == GitHubType.PR,
                                AnalyticsEvent.event_type == EventType.REVIEW
                            ),
                            1
                        ),
                        else_=0
                    )
                ).label('prs_reviewed')
            ).filter(
                AnalyticsEvent.timestamp >= start_date,
                AnalyticsEvent.timestamp <= end_date
            )

            # Add repository filter if provided
            if repository:
                query = query.filter(AnalyticsEvent.github_repository == repository)

            # Group by date and order
            query = query.group_by('date').order_by('date')

            results = query.all()

            # Format results (convert Decimal to native Python types)
            timeline = []
            for row in results:
                prs_reviewed = int(row.prs_reviewed or 0)
                coins_used = float(row.coins_used or 0)
                avg_coins_per_pr = round(coins_used / prs_reviewed, 2) if prs_reviewed > 0 else 0.0

                timeline.append({
                    'date': str(row.date),
                    'coinsUsed': round(coins_used, 2),
                    'prsReviewed': prs_reviewed,
                    'avgCoinsPerPR': avg_coins_per_pr
                })

            return timeline

        except Exception as e:
            logger.error(f"Failed to get timeline: {e}")
            raise

    def get_repository_breakdown(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get repository breakdown with usage statistics.
        """
        try:
            # Query repository statistics
            query = db.query(
                AnalyticsEvent.github_repository.label('name'),
                func.sum(AnalyticsEvent.cost_coins_used).label('coins_used'),
                func.sum(
                    case(
                        (
                            and_(
                                AnalyticsEvent.github_type == GitHubType.PR,
                                AnalyticsEvent.event_type == EventType.REVIEW
                            ),
                            1
                        ),
                        else_=0
                    )
                ).label('prs_reviewed')
            ).filter(
                AnalyticsEvent.timestamp >= start_date,
                AnalyticsEvent.timestamp <= end_date
            ).group_by(
                AnalyticsEvent.github_repository
            ).order_by(
                func.sum(AnalyticsEvent.cost_coins_used).desc()
            )

            results = query.all()

            # Calculate total coins for percentage
            total_coins = sum(float(row.coins_used or 0) for row in results)

            # Format results with percentages
            repositories = []
            for row in results:
                coins_used = float(row.coins_used or 0)
                percentage = round((coins_used / total_coins * 100), 1) if total_coins > 0 else 0

                repositories.append({
                    'name': row.name,
                    'coinsUsed': round(coins_used, 2),
                    'prsReviewed': row.prs_reviewed or 0,
                    'percentage': percentage
                })

            return repositories

        except Exception as e:
            logger.error(f"Failed to get repository breakdown: {e}")
            raise

    def get_recent_pull_requests(
        self,
        db: Session,
        limit: int = 10,
        offset: int = 0,
        repository: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get recent pull requests with review details.
        """
        try:
            # Build base query for PRs with review events
            query = db.query(
                AnalyticsEvent,
                ReviewDetails
            ).outerjoin(
                ReviewDetails,
                AnalyticsEvent.id == ReviewDetails.event_id
            ).filter(
                AnalyticsEvent.github_type == GitHubType.PR,
                AnalyticsEvent.event_type == EventType.REVIEW
            )

            # Add repository filter if provided
            if repository:
                query = query.filter(AnalyticsEvent.github_repository == repository)

            # Get total count
            total = query.count()

            # Apply pagination and ordering
            query = query.order_by(AnalyticsEvent.timestamp.desc())
            query = query.offset(offset).limit(limit)

            results = query.all()

            # Format results
            pull_requests = []
            for event, review in results:
                # Extract repository name (last part after /)
                repo_parts = event.github_repository.split('/')
                repo_name = repo_parts[-1] if repo_parts else event.github_repository

                pr_data = {
                    'id': f"#{event.github_number}",
                    'title': event.github_title,
                    'repository': repo_name,
                    'author': event.github_author,
                    'reviewers': [event.metadata_triggered_by],
                    'coinsUsed': round(float(event.cost_coins_used), 2),
                    'reviewedAt': event.timestamp.isoformat(),
                    'url': event.github_url,
                    'findings': {
                        'critical': review.critical_count if review else 0,
                        'high': review.high_count if review else 0,
                        'medium': review.medium_count if review else 0,
                        'low': review.low_count if review else 0
                    }
                }
                pull_requests.append(pr_data)

            return {
                'pullRequests': pull_requests,
                'pagination': {
                    'total': total,
                    'limit': limit,
                    'offset': offset,
                    'hasMore': offset + limit < total
                }
            }

        except Exception as e:
            logger.error(f"Failed to get recent pull requests: {e}")
            raise


# Singleton instance
aggregation_service = AggregationService()

# Made with Bob

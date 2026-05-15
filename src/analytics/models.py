"""
SQLAlchemy models for analytics data.
Migrated from MongoDB to MySQL relational schema.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, DateTime, Enum, DECIMAL, Boolean,
    ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import relationship
from src.database import Base
import enum


class EventType(str, enum.Enum):
    """Event type enumeration"""
    REVIEW = "review"
    UPDATEDOCS = "updatedocs"
    ANALYZEIMPACT = "analyzeimpact"
    IMPLEMENTFIX = "implementfix"


class GitHubType(str, enum.Enum):
    """GitHub entity type"""
    PR = "pr"
    ISSUE = "issue"


class Status(str, enum.Enum):
    """Event status"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class RiskLevel(str, enum.Enum):
    """Risk level for impact analysis"""
    LOW = "low"
    MEDIUM = "medium"
    MEDIUM_HIGH = "medium-high"
    HIGH = "high"
    CRITICAL = "critical"


class ClassificationType(str, enum.Enum):
    """Documentation classification type"""
    MAJOR = "major"
    MINOR = "minor"


class Confidence(str, enum.Enum):
    """Confidence level"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestCoverageStatus(str, enum.Enum):
    """Test coverage status"""
    NONE = "none"
    PARTIAL = "partial"
    GOOD = "good"
    EXCELLENT = "excellent"


class FixComplexity(str, enum.Enum):
    """Fix complexity level"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class VerificationStatus(str, enum.Enum):
    """Verification status"""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


class AnalyticsEvent(Base):
    """
    Main analytics events table.
    Stores all types of events (review, updatedocs, analyzeimpact, implementfix).
    """
    __tablename__ = "analytics_events"

    # Primary key
    id = Column(String(36), primary_key=True)
    
    # Event metadata
    event_type = Column(Enum(EventType), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # GitHub context
    github_type = Column(Enum(GitHubType), nullable=False)
    github_number = Column(Integer, nullable=False)
    github_title = Column(String(500), nullable=False)
    github_url = Column(String(500), nullable=False)
    github_repository = Column(String(200), nullable=False, index=True)
    github_author = Column(String(100), nullable=False, index=True)
    github_branch = Column(String(200), nullable=True)
    github_base_branch = Column(String(200), nullable=True)
    github_labels = Column(JSON, nullable=True)  # Array of labels
    
    # Cost information
    cost_coins_used = Column(DECIMAL(10, 2), nullable=False)
    cost_dollars_used = Column(DECIMAL(10, 4), nullable=False)
    cost_operation = Column(String(100), nullable=False)
    
    # Metadata
    metadata_triggered_by = Column(String(100), nullable=False)
    metadata_duration = Column(Integer, nullable=False)  # Duration in seconds
    metadata_status = Column(Enum(Status), nullable=False, index=True)
    metadata_workflow_run_id = Column(String(100), nullable=True)
    metadata_workflow_run_url = Column(String(500), nullable=True)
    metadata_fixium_version = Column(String(50), nullable=True)
    
    # Relationships to detail tables
    review_details = relationship("ReviewDetails", back_populates="event", uselist=False, cascade="all, delete-orphan")
    documentation_details = relationship("DocumentationDetails", back_populates="event", uselist=False, cascade="all, delete-orphan")
    impact_details = relationship("ImpactDetails", back_populates="event", uselist=False, cascade="all, delete-orphan")
    fix_details = relationship("FixDetails", back_populates="event", uselist=False, cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_event_repo_time', 'github_repository', 'timestamp'),
        Index('idx_event_author_time', 'github_author', 'timestamp'),
    )

    def __repr__(self):
        return f"<AnalyticsEvent(id={self.id}, type={self.event_type}, repo={self.github_repository})>"


class ReviewDetails(Base):
    """
    Review-specific details for code review events.
    """
    __tablename__ = "analytics_review_details"

    event_id = Column(String(36), ForeignKey('analytics_events.id', ondelete='CASCADE'), primary_key=True)
    
    # Finding counts
    total_findings = Column(Integer, nullable=False)
    critical_count = Column(Integer, nullable=False, default=0)
    high_count = Column(Integer, nullable=False, default=0)
    medium_count = Column(Integer, nullable=False, default=0)
    low_count = Column(Integer, nullable=False, default=0)
    
    # Review scope
    files_reviewed = Column(Integer, nullable=False)
    lines_reviewed = Column(Integer, nullable=False)
    
    # Findings breakdown
    findings_by_type = Column(JSON, nullable=True)  # {bug: 3, security: 1, ...}
    filters = Column(JSON, nullable=True)  # Applied filters
    
    # Relationship
    event = relationship("AnalyticsEvent", back_populates="review_details")

    def __repr__(self):
        return f"<ReviewDetails(event_id={self.event_id}, findings={self.total_findings})>"


class DocumentationDetails(Base):
    """
    Documentation analysis details for updatedocs events.
    """
    __tablename__ = "analytics_documentation_details"

    event_id = Column(String(36), ForeignKey('analytics_events.id', ondelete='CASCADE'), primary_key=True)
    
    # Classification
    classification_type = Column(Enum(ClassificationType), nullable=False)
    classification_confidence = Column(Enum(Confidence), nullable=False)
    classification_reasoning = Column(Text, nullable=True)
    
    # Analysis results
    files_analyzed = Column(Integer, nullable=False)
    suggestions_count = Column(Integer, nullable=False)
    high_priority_count = Column(Integer, nullable=False)
    medium_priority_count = Column(Integer, nullable=False)
    low_priority_count = Column(Integer, nullable=False)
    
    # Affected files
    affected_files = Column(JSON, nullable=True)  # Array of file paths
    forced = Column(Boolean, default=False)
    
    # Relationship
    event = relationship("AnalyticsEvent", back_populates="documentation_details")

    def __repr__(self):
        return f"<DocumentationDetails(event_id={self.event_id}, type={self.classification_type})>"


class ImpactDetails(Base):
    """
    Impact analysis details for analyzeimpact events.
    """
    __tablename__ = "analytics_impact_details"

    event_id = Column(String(36), ForeignKey('analytics_events.id', ondelete='CASCADE'), primary_key=True)
    
    # Risk assessment
    risk_score = Column(DECIMAL(3, 2), nullable=False)  # 0.00 to 1.00
    risk_level = Column(Enum(RiskLevel), nullable=False)
    
    # Dependencies
    direct_dependencies = Column(Integer, nullable=True)
    downstream_impact = Column(Integer, nullable=True)
    
    # Test coverage
    test_coverage_status = Column(Enum(TestCoverageStatus), nullable=True)
    test_coverage_files_found = Column(Integer, nullable=True)
    test_coverage_needs_update = Column(Integer, nullable=True)
    
    # API changes
    api_endpoints_total = Column(Integer, nullable=True)
    api_endpoints_new = Column(Integer, nullable=True)
    api_endpoints_modified = Column(Integer, nullable=True)
    api_endpoints_breaking = Column(Integer, nullable=True)
    
    # Database changes
    database_tables_affected = Column(Integer, nullable=True)
    database_schema_changes = Column(Integer, nullable=True)
    
    # Recommendations
    recommendations_count = Column(Integer, nullable=True)
    high_priority_recommendations = Column(Integer, nullable=True)
    
    # Affected components
    affected_components = Column(JSON, nullable=True)  # Array of component paths
    
    # Relationship
    event = relationship("AnalyticsEvent", back_populates="impact_details")

    def __repr__(self):
        return f"<ImpactDetails(event_id={self.event_id}, risk={self.risk_level})>"


class FixDetails(Base):
    """
    Fix implementation details for implementfix events.
    """
    __tablename__ = "analytics_fix_details"

    event_id = Column(String(36), ForeignKey('analytics_events.id', ondelete='CASCADE'), primary_key=True)
    
    # Code changes
    files_modified = Column(Integer, nullable=False)
    lines_added = Column(Integer, nullable=False)
    lines_removed = Column(Integer, nullable=False)
    
    # Test changes
    tests_added = Column(Integer, nullable=True)
    tests_modified = Column(Integer, nullable=True)
    
    # Fix metadata
    fix_complexity = Column(Enum(FixComplexity), nullable=False)
    verification_status = Column(Enum(VerificationStatus), nullable=True)
    
    # Relationship
    event = relationship("AnalyticsEvent", back_populates="fix_details")

    def __repr__(self):
        return f"<FixDetails(event_id={self.event_id}, files={self.files_modified})>"

# Made with Bob

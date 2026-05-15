"""
Pydantic schemas for analytics API request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


# Enums matching database models
class EventTypeEnum(str, Enum):
    REVIEW = "review"
    UPDATEDOCS = "updatedocs"
    ANALYZEIMPACT = "analyzeimpact"
    IMPLEMENTFIX = "implementfix"


class GitHubTypeEnum(str, Enum):
    PR = "pr"
    ISSUE = "issue"


class StatusEnum(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class RiskLevelEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    MEDIUM_HIGH = "medium-high"
    HIGH = "high"
    CRITICAL = "critical"


# Request/Response Schemas

class GitHubContext(BaseModel):
    """GitHub context information"""
    type: GitHubTypeEnum
    number: int
    title: str
    url: str
    repository: str
    author: str
    branch: Optional[str] = None
    baseBranch: Optional[str] = Field(None, alias="baseBranch")
    labels: Optional[List[str]] = None

    class Config:
        populate_by_name = True


class CostInfo(BaseModel):
    """Cost information"""
    coinsUsed: float = Field(..., alias="coinsUsed")
    dollarsUsed: float = Field(..., alias="dollarsUsed")
    operation: str

    class Config:
        populate_by_name = True


class TestCoverage(BaseModel):
    """Test coverage information"""
    status: str
    filesFound: int = Field(..., alias="filesFound")
    needsUpdate: int = Field(..., alias="needsUpdate")

    class Config:
        populate_by_name = True


class APIEndpoints(BaseModel):
    """API endpoints information"""
    total: int
    new: int
    modified: int
    breaking: int


class DatabaseChanges(BaseModel):
    """Database changes information"""
    tablesAffected: int = Field(..., alias="tablesAffected")
    schemaChanges: int = Field(..., alias="schemaChanges")

    class Config:
        populate_by_name = True


class ImpactInfo(BaseModel):
    """Impact analysis information"""
    riskScore: float = Field(..., alias="riskScore", ge=0, le=1)
    riskLevel: RiskLevelEnum = Field(..., alias="riskLevel")
    directDependencies: Optional[int] = Field(None, alias="directDependencies")
    downstreamImpact: Optional[int] = Field(None, alias="downstreamImpact")
    testCoverage: Optional[TestCoverage] = Field(None, alias="testCoverage")
    apiEndpoints: Optional[APIEndpoints] = Field(None, alias="apiEndpoints")
    databaseChanges: Optional[DatabaseChanges] = Field(None, alias="databaseChanges")
    recommendationsCount: Optional[int] = Field(None, alias="recommendationsCount")
    highPriorityRecommendations: Optional[int] = Field(None, alias="highPriorityRecommendations")
    affectedComponents: Optional[List[str]] = Field(None, alias="affectedComponents")

    class Config:
        populate_by_name = True


class ReviewInfo(BaseModel):
    """Code review information"""
    totalFindings: int = Field(..., alias="totalFindings")
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    filesReviewed: int = Field(..., alias="filesReviewed")
    linesReviewed: int = Field(..., alias="linesReviewed")
    findingsByType: Optional[Dict[str, int]] = Field(None, alias="findingsByType")
    filters: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True


class Classification(BaseModel):
    """Documentation classification"""
    type: str
    confidence: str
    reasoning: Optional[str] = None


class DocumentationInfo(BaseModel):
    """Documentation analysis information"""
    classification: Classification
    filesAnalyzed: int = Field(..., alias="filesAnalyzed")
    suggestionsCount: int = Field(..., alias="suggestionsCount")
    highPriority: int = Field(..., alias="highPriority")
    mediumPriority: int = Field(..., alias="mediumPriority")
    lowPriority: int = Field(..., alias="lowPriority")
    affectedFiles: Optional[List[str]] = Field(None, alias="affectedFiles")
    forced: bool = False

    class Config:
        populate_by_name = True


class FixInfo(BaseModel):
    """Fix implementation information"""
    filesModified: int = Field(..., alias="filesModified")
    linesAdded: int = Field(..., alias="linesAdded")
    linesRemoved: int = Field(..., alias="linesRemoved")
    testsAdded: Optional[int] = Field(None, alias="testsAdded")
    testsModified: Optional[int] = Field(None, alias="testsModified")
    fixComplexity: str = Field(..., alias="fixComplexity")
    verificationStatus: Optional[str] = Field(None, alias="verificationStatus")

    class Config:
        populate_by_name = True


class WorkflowRun(BaseModel):
    """Workflow run information"""
    id: str
    url: str


class Metadata(BaseModel):
    """Event metadata"""
    triggeredBy: str = Field(..., alias="triggeredBy")
    duration: int  # seconds
    status: StatusEnum
    workflowRun: Optional[WorkflowRun] = Field(None, alias="workflowRun")
    fixiumVersion: Optional[str] = Field(None, alias="fixiumVersion")

    class Config:
        populate_by_name = True


class AnalyticsEventCreate(BaseModel):
    """Schema for creating an analytics event"""
    eventType: EventTypeEnum = Field(..., alias="eventType")
    github: GitHubContext
    cost: CostInfo
    impact: Optional[ImpactInfo] = None
    review: Optional[ReviewInfo] = None
    documentation: Optional[DocumentationInfo] = None
    fix: Optional[FixInfo] = None
    metadata: Metadata

    class Config:
        populate_by_name = True

    @validator('impact')
    def validate_impact(cls, v, values):
        if values.get('eventType') == EventTypeEnum.ANALYZEIMPACT and v is None:
            raise ValueError('impact is required for analyzeimpact events')
        return v

    @validator('review')
    def validate_review(cls, v, values):
        if values.get('eventType') == EventTypeEnum.REVIEW and v is None:
            raise ValueError('review is required for review events')
        return v

    @validator('documentation')
    def validate_documentation(cls, v, values):
        if values.get('eventType') == EventTypeEnum.UPDATEDOCS and v is None:
            raise ValueError('documentation is required for updatedocs events')
        return v

    @validator('fix')
    def validate_fix(cls, v, values):
        if values.get('eventType') == EventTypeEnum.IMPLEMENTFIX and v is None:
            raise ValueError('fix is required for implementfix events')
        return v


class AnalyticsEventResponse(BaseModel):
    """Schema for analytics event response"""
    success: bool
    data: Dict[str, Any]


class DashboardSummary(BaseModel):
    """Dashboard summary statistics"""
    totalEvents: int = Field(..., alias="totalEvents")
    totalCost: Dict[str, float] = Field(..., alias="totalCost")
    eventsByType: Dict[str, int] = Field(..., alias="eventsByType")
    averageDuration: float = Field(..., alias="averageDuration")

    class Config:
        populate_by_name = True


class TimelineDataPoint(BaseModel):
    """Single timeline data point"""
    date: str
    events: int
    cost: float
    eventsByType: Dict[str, int] = Field(..., alias="eventsByType")

    class Config:
        populate_by_name = True


class TimelineData(BaseModel):
    """Timeline data for charts"""
    timeline: List[TimelineDataPoint]
    granularity: str


class RepositoryStats(BaseModel):
    """Repository statistics"""
    repository: str
    events: int
    cost: float
    eventsByType: Dict[str, int] = Field(..., alias="eventsByType")

    class Config:
        populate_by_name = True


class RepositoryBreakdown(BaseModel):
    """Repository breakdown"""
    repositories: List[RepositoryStats]


class PullRequestInfo(BaseModel):
    """Pull request information"""
    number: int
    title: str
    repository: str
    author: str
    events: int
    totalCost: float = Field(..., alias="totalCost")
    lastActivity: datetime = Field(..., alias="lastActivity")

    class Config:
        populate_by_name = True


class PullRequestSummary(BaseModel):
    """Pull request summary with pagination"""
    pullRequests: List[PullRequestInfo] = Field(..., alias="pullRequests")
    pagination: Dict[str, Any]

    class Config:
        populate_by_name = True


class EventListResponse(BaseModel):
    """Response for listing events with pagination"""
    success: bool = True
    data: Dict[str, Any]  # Contains 'events' list and 'pagination' dict

    class Config:
        populate_by_name = True


# Made with Bob

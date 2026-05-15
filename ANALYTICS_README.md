# AutoFix System - Analytics Integration

## Overview

The AutoFix System now includes a comprehensive analytics module that tracks and visualizes metrics from code reviews, documentation analysis, impact analysis, and fix implementations. This replaces the previous standalone Review Analytics Node.js backend with an integrated Python/FastAPI solution using MySQL.

## Architecture

### Technology Stack
- **Backend**: Python/FastAPI (integrated into AutoFix System)
- **Database**: MySQL 8.0 (AWS RDS compatible)
- **ORM**: SQLAlchemy with Alembic migrations
- **Authentication**: Bearer token (API key)

### Database Schema

#### Core Tables

1. **analytics_events** - Main events table
   - Stores common fields for all event types
   - Indexed on: event_type, timestamp, repository, github_number

2. **review_details** - Code review findings
   - Foreign key to analytics_events
   - Stores findings by severity, files reviewed

3. **documentation_details** - Documentation analysis
   - Foreign key to analytics_events
   - Stores suggestions by priority, files analyzed

4. **impact_details** - Impact analysis results
   - Foreign key to analytics_events
   - Stores risk metrics, dependencies, API/DB changes

5. **fix_details** - Fix implementation tracking
   - Foreign key to analytics_events
   - Stores fix success/failure, files modified, PR info

## API Endpoints

### Analytics CRUD

#### POST /api/v1/analytics
Create a new analytics event.

**Authentication**: Bearer token required

**Request Body**:
```json
{
  "eventType": "review",
  "github": {
    "type": "pull_request",
    "number": 123,
    "title": "Add payment feature",
    "url": "https://github.com/owner/repo/pull/123",
    "repository": "owner/repo",
    "author": "developer",
    "labels": ["feature", "backend"]
  },
  "cost": {
    "coinsUsed": 45.2,
    "dollarsUsed": 0.0452,
    "operation": "code review"
  },
  "review": {
    "totalFindings": 12,
    "criticalCount": 1,
    "highCount": 3,
    "mediumCount": 6,
    "lowCount": 2,
    "findingsBySeverity": [...],
    "filesReviewed": ["src/payment.py", "tests/test_payment.py"]
  },
  "metadata": {
    "triggeredBy": "github-actions",
    "duration": 120,
    "status": "success",
    "workflowRun": {
      "id": "1234567890",
      "url": "https://github.com/owner/repo/actions/runs/1234567890"
    },
    "fixiumVersion": "1.0.0"
  }
}
```

**Response** (201):
```json
{
  "success": true,
  "data": {
    "eventId": "42",
    "eventType": "review",
    "timestamp": "2026-05-14T15:30:00Z"
  }
}
```

#### GET /api/v1/analytics/{event_id}
Get a specific analytics event.

**Authentication**: Bearer token required

**Response** (200):
```json
{
  "success": true,
  "data": {
    "id": 42,
    "eventType": "review",
    "timestamp": "2026-05-14T15:30:00Z",
    "github": {...},
    "cost": {...},
    "review": {...},
    "metadata": {...}
  }
}
```

#### GET /api/v1/analytics
List analytics events with filtering and pagination.

**Authentication**: Bearer token required

**Query Parameters**:
- `start_date` (optional): ISO 8601 datetime
- `end_date` (optional): ISO 8601 datetime
- `repository` (optional): Format "owner/repo"
- `event_type` (optional): review, updatedocs, analyzeimpact, implementfix
- `limit` (optional): 1-100, default 50
- `offset` (optional): default 0

**Response** (200):
```json
{
  "success": true,
  "data": {
    "events": [...],
    "pagination": {
      "total": 150,
      "limit": 50,
      "offset": 0,
      "hasMore": true
    }
  }
}
```

#### DELETE /api/v1/analytics/{event_id}
Delete an analytics event.

**Authentication**: Bearer token required

**Response** (200):
```json
{
  "success": true,
  "message": "Event deleted successfully"
}
```

### Dashboard Aggregations

#### GET /api/v1/dashboard/summary
Get dashboard summary statistics.

**Query Parameters**:
- `start_date` (optional): Default 30 days ago
- `end_date` (optional): Default now
- `repository` (optional): Filter by repository

**Response** (200):
```json
{
  "success": true,
  "data": {
    "period": {
      "start": "2026-04-14T00:00:00Z",
      "end": "2026-05-14T23:59:59Z"
    },
    "metrics": {
      "totalEvents": 150,
      "totalCost": {
        "coins": 12450.5,
        "dollars": 124.51
      },
      "eventsByType": {
        "review": 80,
        "updatedocs": 30,
        "analyzeimpact": 25,
        "implementfix": 15
      },
      "averageDuration": 145.5
    }
  }
}
```

#### GET /api/v1/dashboard/timeline
Get time-series data for charts.

**Query Parameters**:
- `start_date` (optional)
- `end_date` (optional)
- `repository` (optional)
- `granularity` (optional): daily, weekly, monthly (default: daily)

**Response** (200):
```json
{
  "success": true,
  "data": {
    "timeline": [
      {
        "date": "2026-05-14",
        "events": 12,
        "cost": 850.5,
        "eventsByType": {
          "review": 8,
          "updatedocs": 2,
          "analyzeimpact": 1,
          "implementfix": 1
        }
      }
    ],
    "granularity": "daily"
  }
}
```

#### GET /api/v1/dashboard/repositories
Get repository breakdown.

**Query Parameters**:
- `start_date` (optional)
- `end_date` (optional)

**Response** (200):
```json
{
  "success": true,
  "data": {
    "repositories": [
      {
        "repository": "owner/backend-api",
        "events": 45,
        "cost": 3250.5,
        "eventsByType": {
          "review": 30,
          "updatedocs": 8,
          "analyzeimpact": 5,
          "implementfix": 2
        }
      }
    ]
  }
}
```

#### GET /api/v1/dashboard/pull-requests
Get recent pull requests with analytics.

**Query Parameters**:
- `limit` (optional): 1-50, default 10
- `offset` (optional): default 0
- `repository` (optional)

**Response** (200):
```json
{
  "success": true,
  "data": {
    "pullRequests": [
      {
        "number": 123,
        "title": "Add payment feature",
        "repository": "owner/backend-api",
        "author": "developer",
        "events": 3,
        "totalCost": 150.5,
        "lastActivity": "2026-05-14T15:30:00Z",
        "findings": {
          "critical": 1,
          "high": 3,
          "medium": 6,
          "low": 2
        }
      }
    ],
    "pagination": {
      "total": 50,
      "limit": 10,
      "offset": 0,
      "hasMore": true
    }
  }
}
```

## Deployment

### Local Development

1. **Start MySQL**:
```bash
docker-compose up mysql -d
```

2. **Set environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run database migrations**:
```bash
alembic upgrade head
```

4. **Start the application**:
```bash
uvicorn src.main:app --reload --port 8000
```

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f autofix-system

# Stop services
docker-compose down
```

### AWS RDS Deployment

1. **Create RDS MySQL instance**:
   - Engine: MySQL 8.0
   - Instance class: db.t3.micro (or larger)
   - Storage: 20 GB (or more)
   - Enable automated backups
   - Enable encryption at rest

2. **Configure security group**:
   - Allow inbound MySQL (3306) from application IP

3. **Update environment variables**:
```bash
DATABASE_URL=mysql+pymysql://admin:password@your-rds-endpoint.region.rds.amazonaws.com:3306/autofix_analytics
MYSQL_HOST=your-rds-endpoint.region.rds.amazonaws.com
MYSQL_PORT=3306
MYSQL_USER=admin
MYSQL_PASSWORD=your-secure-password
MYSQL_DATABASE=autofix_analytics
```

4. **Run migrations**:
```bash
alembic upgrade head
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | Full MySQL connection string | Yes | - |
| `MYSQL_HOST` | MySQL host | Yes | localhost |
| `MYSQL_PORT` | MySQL port | Yes | 3306 |
| `MYSQL_USER` | MySQL username | Yes | - |
| `MYSQL_PASSWORD` | MySQL password | Yes | - |
| `MYSQL_DATABASE` | Database name | Yes | autofix_analytics |
| `ANALYTICS_API_KEY` | API key for authentication | Yes | - |

### Authentication

All analytics endpoints (except health check) require Bearer token authentication:

```bash
curl -H "Authorization: Bearer your-api-key-here" \
  http://localhost:8000/api/v1/analytics
```

Set the API key in your environment:
```bash
ANALYTICS_API_KEY=your-secret-api-key-here
```

## Database Migrations

### Create a new migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Downgrade one revision
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Event Types

### 1. Code Review (`review`)

**Required fields**:
- `review.totalFindings`
- `review.criticalCount`
- `review.highCount`
- `review.mediumCount`
- `review.lowCount`

**Optional fields**:
- `review.findingsBySeverity` (JSON array)
- `review.filesReviewed` (JSON array)

### 2. Documentation Analysis (`updatedocs`)

**Required fields**:
- `documentation.filesAnalyzed`
- `documentation.suggestionsCount`
- `documentation.highPriorityCount`
- `documentation.mediumPriorityCount`
- `documentation.lowPriorityCount`

**Optional fields**:
- `documentation.documentationFiles` (JSON array)
- `documentation.suggestions` (JSON array)

### 3. Impact Analysis (`analyzeimpact`)

**Required fields**:
- `impact.riskScore` (0.0-1.0)
- `impact.riskLevel` (low, medium, medium-high, high, critical)
- `impact.directDependencies`
- `impact.downstreamImpact`
- `impact.recommendationsCount`
- `impact.highPriorityRecommendations`

**Optional fields**:
- `impact.testCoverage` (object)
- `impact.apiEndpoints` (object)
- `impact.databaseChanges` (object)
- `impact.affectedComponents` (JSON array)

### 4. Fix Implementation (`implementfix`)

**Required fields**:
- `fix.totalFixes`
- `fix.successfulFixes`
- `fix.failedFixes`
- `fix.prCreated` (boolean)

**Optional fields**:
- `fix.filesModified` (JSON array)
- `fix.testsAdded`
- `fix.testsUpdated`
- `fix.prUrl`

## Testing

### Run tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src/analytics --cov-report=html

# Specific test file
pytest tests/test_analytics_routes.py
```

### Manual API testing

```bash
# Create event
curl -X POST http://localhost:8000/api/v1/analytics \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d @test_event.json

# Get dashboard summary
curl http://localhost:8000/api/v1/dashboard/summary

# Get timeline
curl "http://localhost:8000/api/v1/dashboard/timeline?granularity=daily"
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Database Metrics

Monitor these MySQL metrics:
- Connection count
- Query performance
- Table sizes
- Index usage
- Slow queries

### Application Metrics

- API response times
- Error rates
- Event creation rate
- Database query performance

## Troubleshooting

### Database connection issues

```bash
# Test MySQL connection
mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE

# Check Docker MySQL logs
docker-compose logs mysql

# Verify environment variables
env | grep MYSQL
```

### Migration issues

```bash
# Check current migration status
alembic current

# Show pending migrations
alembic history

# Reset to specific revision
alembic downgrade <revision_id>
alembic upgrade head
```

### API authentication issues

```bash
# Verify API key is set
echo $ANALYTICS_API_KEY

# Test with curl
curl -v -H "Authorization: Bearer $ANALYTICS_API_KEY" \
  http://localhost:8000/api/v1/analytics
```

## Security Best Practices

1. **API Keys**:
   - Use strong, randomly generated keys
   - Rotate keys regularly
   - Never commit keys to version control

2. **Database**:
   - Use strong passwords
   - Enable SSL/TLS for connections
   - Restrict access by IP
   - Enable encryption at rest (RDS)

3. **Network**:
   - Use VPC for RDS (AWS)
   - Configure security groups properly
   - Use HTTPS in production

4. **Monitoring**:
   - Enable CloudWatch (AWS)
   - Set up alerts for errors
   - Monitor unusual activity

## Migration from Review Analytics (Node.js)

The analytics system has been migrated from a standalone Node.js/Express + MongoDB backend to an integrated Python/FastAPI + MySQL solution. Key changes:

### What Changed
- **Backend**: Node.js/Express → Python/FastAPI
- **Database**: MongoDB → MySQL
- **Deployment**: Separate service → Integrated into AutoFix System
- **Schema**: NoSQL documents → Relational tables

### What Stayed the Same
- **API Endpoints**: Same paths and functionality
- **Event Types**: Same 4 event types
- **Authentication**: Bearer token (API key)
- **Dashboard Features**: All aggregations preserved

### Benefits
- **Unified codebase**: Single Python application
- **Better performance**: MySQL optimizations and indexes
- **Easier deployment**: One Docker Compose setup
- **Type safety**: Pydantic validation
- **AWS RDS ready**: Production-grade database

## Support

For issues or questions:
1. Check this documentation
2. Review error logs
3. Check database connection
4. Verify API authentication
5. Contact development team

---

**Last Updated**: 2026-05-14  
**Version**: 1.0.0  
**Maintainer**: AutoFix System Team

Made with Bob
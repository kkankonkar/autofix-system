# Analytics API Testing - Quick Start Guide

## Prerequisites

- Podman or Docker installed
- `jq` installed (for JSON parsing)
- Port 8000 available

## Step 1: Start the Services

```bash
cd /Users/hrishikeshpai/Documents/git_repos_old/autofix-system

# Start MySQL and AutoFix System
podman-compose up -d

# Wait for services to be ready (about 30 seconds)
sleep 30

# Check if services are running
podman-compose ps
```

## Step 2: Run Database Migrations

```bash
# Run Alembic migrations to create analytics tables
podman-compose exec autofix-system alembic upgrade head

# Or if you prefer to run migrations before starting:
# alembic upgrade head
# podman-compose up -d
```

## Step 3: Verify Services are Running

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Check analytics health
curl -H "Authorization: Bearer test-api-key-12345" \
     http://localhost:8000/api/v1/analytics/health
```

Expected output:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Step 4: Run the Test Script

```bash
# Run all analytics tests
./test_analytics.sh

# Or with custom API key
ANALYTICS_API_KEY="your-api-key" ./test_analytics.sh
```

The script will:
1. ✅ Check if services are running
2. ✅ Test health endpoints
3. ✅ Create 4 sample events (review, docs, impact, fix)
4. ✅ Test GET endpoints (by ID, list, filter)
5. ✅ Test dashboard endpoints (summary, timeline, repos, PRs)
6. ✅ Display results with color-coded output

## Step 5: Explore the API

### Using Swagger UI (Interactive Documentation)

Open in your browser:
```
http://localhost:8000/docs
```

This provides:
- Interactive API testing
- Request/response schemas
- Try-it-out functionality
- Authentication testing

### Using curl (Command Line)

```bash
# Set your API key
export API_KEY="test-api-key-12345"

# Create a review event
curl -X POST http://localhost:8000/api/v1/analytics/events \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "review",
    "github": {
      "type": "pull_request",
      "number": 123,
      "title": "Test PR",
      "url": "https://github.com/org/repo/pull/123",
      "repository": "org/repo",
      "author": "developer",
      "branch": "feature/test",
      "baseBranch": "main",
      "labels": ["test"]
    },
    "cost": {
      "coinsUsed": 1000,
      "dollarsUsed": 0.10,
      "operation": "code-review"
    },
    "metadata": {
      "triggeredBy": "pull_request",
      "duration": 30,
      "status": "success",
      "fixiumVersion": "1.0.0"
    },
    "review": {
      "totalFindings": 5,
      "critical": 1,
      "high": 2,
      "medium": 2,
      "low": 0,
      "filesReviewed": 3,
      "linesReviewed": 150,
      "findingsByType": {"bug": 3, "security": 2},
      "filters": {}
    }
  }' | jq '.'

# List all events
curl -H "Authorization: Bearer $API_KEY" \
     "http://localhost:8000/api/v1/analytics?limit=10" | jq '.'

# Get dashboard summary (last 7 days)
START_DATE=$(date -u -v-7d +"%Y-%m-%dT%H:%M:%SZ")
END_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

curl -H "Authorization: Bearer $API_KEY" \
     "http://localhost:8000/api/v1/analytics/dashboard?start_date=$START_DATE&end_date=$END_DATE" | jq '.'
```

## Step 6: View Logs

```bash
# View all logs
podman-compose logs -f

# View only AutoFix System logs
podman-compose logs -f autofix-system

# View only MySQL logs
podman-compose logs -f mysql
```

## Step 7: Connect React Dashboard

Update the React dashboard configuration:

```javascript
// review-analytics/src/config.js
export const API_BASE_URL = 'http://localhost:8000';
export const API_KEY = 'test-api-key-12345';
```

Then start the dashboard:
```bash
cd /Users/hrishikeshpai/Documents/git_repos_old/review-analytics
npm install
npm start
```

## Troubleshooting

### Services won't start

```bash
# Check if ports are in use
lsof -i :8000
lsof -i :3306

# Stop and remove containers
podman-compose down -v

# Rebuild and start
podman-compose build --no-cache
podman-compose up -d
```

### Database connection errors

```bash
# Check MySQL is running
podman-compose ps mysql

# Check MySQL logs
podman-compose logs mysql

# Verify database exists
podman-compose exec mysql mysql -u root -p -e "SHOW DATABASES;"
```

### Migration errors

```bash
# Check current migration status
alembic current

# View migration history
alembic history

# Downgrade and re-run
alembic downgrade -1
alembic upgrade head

# Or stamp as current version (if tables already exist)
alembic stamp head
```

### API returns 401 Unauthorized

```bash
# Check API key in .env file
cat .env | grep ANALYTICS_API_KEY

# Verify API key in request
curl -v -H "Authorization: Bearer test-api-key-12345" \
     http://localhost:8000/api/v1/analytics/health
```

### No data in dashboard

```bash
# Check if events exist
curl -H "Authorization: Bearer test-api-key-12345" \
     "http://localhost:8000/api/v1/analytics?limit=1" | jq '.data.pagination.total'

# If 0, run the test script to create sample data
./test_analytics.sh
```

## Clean Up

```bash
# Stop services
podman-compose down

# Remove volumes (deletes all data)
podman-compose down -v

# Remove images
podman-compose down --rmi all
```

## Next Steps

1. **Production Deployment**
   - Update `.env` with production credentials
   - Use AWS RDS for MySQL
   - Set strong API keys
   - Enable HTTPS

2. **Integrate with Fixium**
   - Update Fixium workflows to POST analytics data
   - Add analytics payload generation to workflows
   - Test with real PRs

3. **Monitor and Optimize**
   - Set up monitoring (Grafana, DataDog)
   - Add alerting for errors
   - Optimize database queries
   - Add caching layer

## Useful Commands

```bash
# Rebuild after code changes
podman-compose build autofix-system
podman-compose up -d autofix-system

# View database tables
podman-compose exec mysql mysql -u root -p autofix_db -e "SHOW TABLES;"

# Query events directly
podman-compose exec mysql mysql -u root -p autofix_db -e "SELECT id, event_type, github_repository, timestamp FROM analytics_events LIMIT 5;"

# Check API performance
time curl -H "Authorization: Bearer test-api-key-12345" \
     "http://localhost:8000/api/v1/analytics/dashboard?start_date=2026-01-01T00:00:00Z&end_date=2026-12-31T23:59:59Z"

# Export data
curl -H "Authorization: Bearer test-api-key-12345" \
     "http://localhost:8000/api/v1/analytics?limit=1000" | jq '.data.events' > events_export.json
```

## Support

- API Documentation: http://localhost:8000/docs
- Project Documentation: `ANALYTICS_README.md`
- Testing Guide: `TESTING_GUIDE.md`
- Architecture: `REVIEW-ANALYTICS-SUMMARY.md` (in code-review-workflow repo)

---

**Quick Test Command:**
```bash
cd /Users/hrishikeshpai/Documents/git_repos_old/autofix-system && \
podman-compose up -d && \
sleep 30 && \
./test_analytics.sh
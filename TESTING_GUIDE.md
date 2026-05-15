# AutoFix System Analytics - Testing Guide

## Quick Start Testing

### 1. Start the System

```bash
cd /Users/hrishikeshpai/Documents/git_repos_old/autofix-system

# Create .env file
cp .env.example .env

# Edit .env and set at minimum:
# ANALYTICS_API_KEY=test-api-key-12345
# MYSQL_PASSWORD=autofix123

# Start services
docker-compose up -d

# Wait for MySQL to be ready (about 30 seconds)
docker-compose logs -f mysql

# Run database migrations
docker-compose exec autofix-system alembic upgrade head

# Check if system is running
curl http://localhost:8000/health
```

### 2. Test API Endpoints

#### Health Check (No Auth Required)
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

#### Create a Code Review Event
```bash
curl -X POST http://localhost:8000/api/v1/analytics \
  -H "Authorization: Bearer test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "review",
    "github": {
      "type": "pull_request",
      "number": 123,
      "title": "Add payment processing feature",
      "url": "https://github.com/myorg/backend-api/pull/123",
      "repository": "myorg/backend-api",
      "author": "john.doe",
      "labels": ["feature", "backend", "payment"]
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
      "findingsBySeverity": [
        {
          "severity": "critical",
          "count": 1,
          "comments": [
            {
              "file": "src/payment/processor.py",
              "lineNumber": 45,
              "issue": "SQL injection vulnerability",
              "details": "User input not sanitized",
              "suggestion": "Use parameterized queries"
            }
          ]
        }
      ],
      "filesReviewed": ["src/payment/processor.py", "tests/test_payment.py"]
    },
    "metadata": {
      "triggeredBy": "github-actions",
      "duration": 120,
      "status": "success",
      "workflowRun": {
        "id": "1234567890",
        "url": "https://github.com/myorg/backend-api/actions/runs/1234567890"
      },
      "fixiumVersion": "1.0.0"
    }
  }'
```

#### Get Dashboard Summary
```bash
curl http://localhost:8000/api/v1/dashboard/summary
```

#### Get Timeline Data
```bash
curl "http://localhost:8000/api/v1/dashboard/timeline?granularity=daily"
```

#### List All Events
```bash
curl -H "Authorization: Bearer test-api-key-12345" \
  http://localhost:8000/api/v1/analytics
```

### 3. Use the Test Script

I'll create a comprehensive test script for you:

```bash
# Make it executable
chmod +x test_analytics_api.sh

# Run all tests
./test_analytics_api.sh
```

## Detailed Testing Steps

### Step 1: Verify System is Running

```bash
# Check Docker containers
docker-compose ps

# Should show:
# autofix-system   running   0.0.0.0:8000->8000/tcp
# autofix-mysql    running   0.0.0.0:3306->3306/tcp

# Check application logs
docker-compose logs -f autofix-system

# Check MySQL logs
docker-compose logs -f mysql
```

### Step 2: Test Database Connection

```bash
# Connect to MySQL directly
docker-compose exec mysql mysql -u autofix -pautofix123 autofix_analytics

# Run queries
mysql> SHOW TABLES;
mysql> SELECT COUNT(*) FROM analytics_events;
mysql> exit
```

### Step 3: Test Each Event Type

#### A. Code Review Event
```bash
curl -X POST http://localhost:8000/api/v1/analytics \
  -H "Authorization: Bearer test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d @test_data/review_event.json
```

#### B. Documentation Analysis Event
```bash
curl -X POST http://localhost:8000/api/v1/analytics \
  -H "Authorization: Bearer test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d @test_data/docs_event.json
```

#### C. Impact Analysis Event
```bash
curl -X POST http://localhost:8000/api/v1/analytics \
  -H "Authorization: Bearer test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d @test_data/impact_event.json
```

#### D. Fix Implementation Event
```bash
curl -X POST http://localhost:8000/api/v1/analytics \
  -H "Authorization: Bearer test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d @test_data/fix_event.json
```

### Step 4: Test Dashboard Endpoints

```bash
# Summary
curl http://localhost:8000/api/v1/dashboard/summary | jq

# Timeline (daily)
curl "http://localhost:8000/api/v1/dashboard/timeline?granularity=daily" | jq

# Timeline (weekly)
curl "http://localhost:8000/api/v1/dashboard/timeline?granularity=weekly" | jq

# Repositories
curl http://localhost:8000/api/v1/dashboard/repositories | jq

# Pull Requests
curl http://localhost:8000/api/v1/dashboard/pull-requests | jq
```

### Step 5: Test Filtering and Pagination

```bash
# Filter by repository
curl -H "Authorization: Bearer test-api-key-12345" \
  "http://localhost:8000/api/v1/analytics?repository=myorg/backend-api" | jq

# Filter by event type
curl -H "Authorization: Bearer test-api-key-12345" \
  "http://localhost:8000/api/v1/analytics?event_type=review" | jq

# Pagination
curl -H "Authorization: Bearer test-api-key-12345" \
  "http://localhost:8000/api/v1/analytics?limit=10&offset=0" | jq

# Date range
curl -H "Authorization: Bearer test-api-key-12345" \
  "http://localhost:8000/api/v1/analytics?start_date=2026-05-01T00:00:00Z&end_date=2026-05-14T23:59:59Z" | jq
```

### Step 6: Test CRUD Operations

```bash
# Create event and save ID
EVENT_ID=$(curl -X POST http://localhost:8000/api/v1/analytics \
  -H "Authorization: Bearer test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d @test_data/review_event.json | jq -r '.data.eventId')

echo "Created event ID: $EVENT_ID"

# Get specific event
curl -H "Authorization: Bearer test-api-key-12345" \
  "http://localhost:8000/api/v1/analytics/$EVENT_ID" | jq

# Delete event
curl -X DELETE \
  -H "Authorization: Bearer test-api-key-12345" \
  "http://localhost:8000/api/v1/analytics/$EVENT_ID" | jq
```

## Test Data Files

Create these test data files in `test_data/` directory:

### test_data/review_event.json
```json
{
  "eventType": "review",
  "github": {
    "type": "pull_request",
    "number": 123,
    "title": "Add payment processing",
    "url": "https://github.com/myorg/backend-api/pull/123",
    "repository": "myorg/backend-api",
    "author": "john.doe",
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
    "findingsBySeverity": [],
    "filesReviewed": ["src/payment.py"]
  },
  "metadata": {
    "triggeredBy": "github-actions",
    "duration": 120,
    "status": "success",
    "fixiumVersion": "1.0.0"
  }
}
```

### test_data/docs_event.json
```json
{
  "eventType": "updatedocs",
  "github": {
    "type": "pull_request",
    "number": 124,
    "title": "Update API documentation",
    "url": "https://github.com/myorg/backend-api/pull/124",
    "repository": "myorg/backend-api",
    "author": "jane.smith",
    "labels": ["documentation"]
  },
  "cost": {
    "coinsUsed": 30.5,
    "dollarsUsed": 0.0305,
    "operation": "documentation analysis"
  },
  "documentation": {
    "filesAnalyzed": 5,
    "suggestionsCount": 8,
    "highPriorityCount": 2,
    "mediumPriorityCount": 4,
    "lowPriorityCount": 2,
    "documentationFiles": ["README.md", "API.md"],
    "suggestions": []
  },
  "metadata": {
    "triggeredBy": "github-actions",
    "duration": 90,
    "status": "success",
    "fixiumVersion": "1.0.0"
  }
}
```

### test_data/impact_event.json
```json
{
  "eventType": "analyzeimpact",
  "github": {
    "type": "issue",
    "number": 125,
    "title": "Add refund functionality",
    "url": "https://github.com/myorg/backend-api/issues/125",
    "repository": "myorg/backend-api",
    "author": "bob.wilson",
    "labels": ["enhancement"]
  },
  "cost": {
    "coinsUsed": 87.3,
    "dollarsUsed": 0.0873,
    "operation": "impact analysis"
  },
  "impact": {
    "riskScore": 0.65,
    "riskLevel": "medium-high",
    "directDependencies": 5,
    "downstreamImpact": 12,
    "testCoverage": {
      "status": "partial",
      "filesFound": 3,
      "needsUpdate": 2
    },
    "apiEndpoints": {
      "total": 3,
      "new": 1,
      "modified": 2,
      "breaking": 0
    },
    "databaseChanges": {
      "tablesAffected": 2,
      "schemaChanges": 0
    },
    "recommendationsCount": 6,
    "highPriorityRecommendations": 2,
    "affectedComponents": ["src/payment/processor.py"]
  },
  "metadata": {
    "triggeredBy": "alice.dev",
    "duration": 180,
    "status": "success",
    "fixiumVersion": "1.0.0"
  }
}
```

### test_data/fix_event.json
```json
{
  "eventType": "implementfix",
  "github": {
    "type": "pull_request",
    "number": 126,
    "title": "Fix SQL injection vulnerability",
    "url": "https://github.com/myorg/backend-api/pull/126",
    "repository": "myorg/backend-api",
    "author": "autofix-bot",
    "labels": ["automated-fix", "security"]
  },
  "cost": {
    "coinsUsed": 95.8,
    "dollarsUsed": 0.0958,
    "operation": "fix implementation"
  },
  "fix": {
    "totalFixes": 3,
    "successfulFixes": 3,
    "failedFixes": 0,
    "filesModified": ["src/payment/processor.py", "tests/test_payment.py"],
    "testsAdded": 2,
    "testsUpdated": 1,
    "prCreated": true,
    "prUrl": "https://github.com/myorg/backend-api/pull/126"
  },
  "metadata": {
    "triggeredBy": "autofix-system",
    "duration": 240,
    "status": "success",
    "fixiumVersion": "1.0.0"
  }
}
```

## Automated Test Script

Save this as `test_analytics_api.sh`:

```bash
#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_KEY="test-api-key-12345"
BASE_URL="http://localhost:8000"

echo "🧪 AutoFix Analytics API Test Suite"
echo "===================================="
echo ""

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check${NC}"
RESPONSE=$(curl -s "$BASE_URL/api/v1/health")
if echo "$RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo "$RESPONSE"
fi
echo ""

# Test 2: Create Review Event
echo -e "${YELLOW}Test 2: Create Review Event${NC}"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/analytics" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d @test_data/review_event.json)

if echo "$RESPONSE" | grep -q "success"; then
    EVENT_ID=$(echo "$RESPONSE" | jq -r '.data.eventId')
    echo -e "${GREEN}✓ Review event created (ID: $EVENT_ID)${NC}"
else
    echo -e "${RED}✗ Failed to create review event${NC}"
    echo "$RESPONSE"
fi
echo ""

# Test 3: Get Event by ID
echo -e "${YELLOW}Test 3: Get Event by ID${NC}"
RESPONSE=$(curl -s -H "Authorization: Bearer $API_KEY" \
  "$BASE_URL/api/v1/analytics/$EVENT_ID")

if echo "$RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✓ Retrieved event successfully${NC}"
else
    echo -e "${RED}✗ Failed to retrieve event${NC}"
fi
echo ""

# Test 4: List Events
echo -e "${YELLOW}Test 4: List Events${NC}"
RESPONSE=$(curl -s -H "Authorization: Bearer $API_KEY" \
  "$BASE_URL/api/v1/analytics")

if echo "$RESPONSE" | grep -q "success"; then
    COUNT=$(echo "$RESPONSE" | jq '.data.pagination.total')
    echo -e "${GREEN}✓ Listed events (Total: $COUNT)${NC}"
else
    echo -e "${RED}✗ Failed to list events${NC}"
fi
echo ""

# Test 5: Dashboard Summary
echo -e "${YELLOW}Test 5: Dashboard Summary${NC}"
RESPONSE=$(curl -s "$BASE_URL/api/v1/dashboard/summary")

if echo "$RESPONSE" | grep -q "success"; then
    TOTAL=$(echo "$RESPONSE" | jq '.data.metrics.totalEvents')
    echo -e "${GREEN}✓ Dashboard summary retrieved (Events: $TOTAL)${NC}"
else
    echo -e "${RED}✗ Failed to get dashboard summary${NC}"
fi
echo ""

# Test 6: Timeline
echo -e "${YELLOW}Test 6: Timeline Data${NC}"
RESPONSE=$(curl -s "$BASE_URL/api/v1/dashboard/timeline?granularity=daily")

if echo "$RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✓ Timeline data retrieved${NC}"
else
    echo -e "${RED}✗ Failed to get timeline${NC}"
fi
echo ""

# Test 7: Delete Event
echo -e "${YELLOW}Test 7: Delete Event${NC}"
RESPONSE=$(curl -s -X DELETE \
  -H "Authorization: Bearer $API_KEY" \
  "$BASE_URL/api/v1/analytics/$EVENT_ID")

if echo "$RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✓ Event deleted successfully${NC}"
else
    echo -e "${RED}✗ Failed to delete event${NC}"
fi
echo ""

echo "===================================="
echo "✅ Test suite completed!"
```

## Troubleshooting

### Issue: Connection Refused
```bash
# Check if containers are running
docker-compose ps

# Restart services
docker-compose restart

# Check logs
docker-compose logs -f
```

### Issue: Database Not Ready
```bash
# Wait for MySQL to be fully ready
docker-compose logs mysql | grep "ready for connections"

# Manually run migrations
docker-compose exec autofix-system alembic upgrade head
```

### Issue: Authentication Failed
```bash
# Verify API key in .env
cat .env | grep ANALYTICS_API_KEY

# Use correct API key in requests
curl -H "Authorization: Bearer your-actual-api-key" ...
```

### Issue: Import Errors
```bash
# Rebuild the container
docker-compose build autofix-system
docker-compose up -d autofix-system
```

## Next Steps

1. Run the test script
2. Verify all tests pass
3. Check database has data
4. Test with frontend dashboard
5. Deploy to production

---

**Happy Testing!** 🚀
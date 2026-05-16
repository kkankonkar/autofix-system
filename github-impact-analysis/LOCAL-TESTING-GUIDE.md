# Local Testing Guide - Analytics Integration

This guide explains how to test the Analytics API integration locally with your AutoFix System instance.

---

## Prerequisites

### 1. AutoFix System Running Locally

Ensure your AutoFix System is running on your local machine:

```bash
cd /Users/hrishikeshpai/Documents/git_repos_old/autofix-system

# Start the system
podman-compose up -d

# Wait for services to be ready
sleep 30

# Check health
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-05-15T07:30:00Z"
}
```

### 2. Verify Analytics API Endpoint

Test the analytics endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/analytics \
  -H "Authorization: Bearer test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "review",
    "github": {
      "type": "pr",
      "number": 1,
      "title": "Test",
      "url": "https://github.com/test/test/pull/1",
      "repository": "test/test",
      "author": "test",
      "branch": "test",
      "baseBranch": "main",
      "labels": []
    },
    "cost": {
      "coinsUsed": 100,
      "dollarsUsed": 0.01,
      "operation": "test"
    },
    "metadata": {
      "triggeredBy": "test",
      "duration": 1,
      "status": "success",
      "fixiumVersion": "1.0.0"
    },
    "review": {
      "totalFindings": 0,
      "critical": 0,
      "high": 0,
      "medium": 0,
      "low": 0,
      "filesReviewed": 0
    }
  }'
```

Expected response:
```json
{
  "id": "uuid-here",
  "message": "Analytics event created successfully"
}
```

---

## Method 1: Automated Test Script

### Step 1: Configure Environment

```bash
cd /Users/hrishikeshpai/Documents/git_repos_old/code-review-workflow

# Set analytics configuration
export ANALYTICS_API_URL="http://localhost:8000"
export ANALYTICS_API_KEY="test-api-key-12345"
export ANALYTICS_ENABLED="true"
```

### Step 2: Run Test Script

```bash
# Make script executable
chmod +x test_analytics_integration.py

# Run tests
python test_analytics_integration.py
```

### Expected Output

```
======================================================================
  Analytics Integration Test Suite
======================================================================

Timestamp: 2026-05-15T07:30:00.000000

======================================================================
  Test 1: Configuration Check
======================================================================
ANALYTICS_API_URL: http://localhost:8000
ANALYTICS_API_KEY: ***2345
ANALYTICS_ENABLED: True
✅ Configuration complete

======================================================================
  Test 2: Code Review Event
======================================================================
Building review event...
Event type: review
PR: #123 - Test PR: Add payment feature
Findings: 15
Cost: 2500.0 coins ($0.25)

Posting to Analytics API...
✅ Analytics event posted successfully
✅ Review event posted

======================================================================
  Test 3: Documentation Event
======================================================================
Building documentation event...
Event type: updatedocs
PR: #123 - Test PR: Add payment feature
Gaps found: 5
Should update: True

Posting to Analytics API...
✅ Analytics event posted successfully
✅ Documentation event posted

======================================================================
  Test 4: Impact Analysis Event
======================================================================
Building impact analysis event...
Event type: analyzeimpact
Issue: #45 - Test Issue: Fix payment validation bug
Risk: high (0.75)
Dependencies: 2 direct, 2 downstream

Posting to Analytics API...
✅ Analytics event posted successfully
✅ Impact event posted

======================================================================
  Test 5: Implement Fix Event
======================================================================
Building implement fix event...
Event type: implementfix
Issue: #45 - Test Issue: Fix payment validation bug
PR: #150 - Fix: Payment validation bug (#45)
Files changed: 3
Tests added: 2

Posting to Analytics API...
✅ Analytics event posted successfully
✅ Fix event posted

======================================================================
  Test Summary
======================================================================
✅ Review event
✅ Documentation event
✅ Impact event
✅ Fix event

Total: 4/4 tests passed

✅ All tests passed!
```

---

## Method 2: Manual Testing with curl

### Test 1: Code Review Event

```bash
curl -X POST http://localhost:8000/api/v1/analytics \
  -H "Authorization: Bearer test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "review",
    "github": {
      "type": "pr",
      "number": 123,
      "title": "Add payment feature",
      "url": "https://github.com/test-org/test-repo/pull/123",
      "repository": "test-org/test-repo",
      "author": "developer",
      "branch": "feature/payment",
      "baseBranch": "main",
      "labels": ["enhancement", "backend"]
    },
    "cost": {
      "coinsUsed": 2500,
      "dollarsUsed": 0.25,
      "operation": "code-review"
    },
    "metadata": {
      "triggeredBy": "pull_request",
      "duration": 120,
      "status": "success",
      "fixiumVersion": "1.0.0"
    },
    "review": {
      "totalFindings": 15,
      "critical": 2,
      "high": 4,
      "medium": 6,
      "low": 3,
      "filesReviewed": 8,
      "linesReviewed": 800
    }
  }' | jq '.'
```

**Note**: `linesReviewed` is required. The analytics_client automatically estimates this as `filesReviewed × 100`.

### Test 2: Documentation Event

```bash
curl -X POST http://localhost:8000/api/v1/analytics \
  -H "Authorization: Bearer test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "updatedocs",
    "github": {
      "type": "pr",
      "number": 123,
      "title": "Add payment feature",
      "url": "https://github.com/test-org/test-repo/pull/123",
      "repository": "test-org/test-repo",
      "author": "developer",
      "branch": "feature/payment",
      "baseBranch": "main",
      "labels": ["enhancement"]
    },
    "cost": {
      "coinsUsed": 1500,
      "dollarsUsed": 0.15,
      "operation": "doc-analysis"
    },
    "metadata": {
      "triggeredBy": "pull_request",
      "duration": 90,
      "status": "success",
      "fixiumVersion": "1.0.0"
    },
    "documentation": {
      "classification": {
        "type": "major",
        "confidence": "high",
        "reasoning": "New feature with multiple new files"
      },
      "filesAnalyzed": 12,
      "suggestionsCount": 5,
      "highPriority": 3,
      "mediumPriority": 1,
      "lowPriority": 1,
      "affectedFiles": ["README.md", "API.md", "SETUP.md"],
      "forced": false
    }
  }' | jq '.'
```

**Note**: Documentation schema requires:
- `classification` object (type, confidence, reasoning)
- `filesAnalyzed` (not `totalDocsAnalyzed`)
- `suggestionsCount`, `highPriority`, `mediumPriority`, `lowPriority`
- The analytics_client automatically formats this correctly.

### Test 3: Impact Analysis Event

```bash
curl -X POST http://localhost:8000/api/v1/analytics \
  -H "Authorization: Bearer test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "analyzeimpact",
    "github": {
      "type": "issue",
      "number": 45,
      "title": "Refactor payment processor",
      "url": "https://github.com/test-org/test-repo/issues/45",
      "repository": "test-org/test-repo",
      "author": "developer",
      "branch": "",
      "baseBranch": "",
      "labels": ["refactor", "high-priority"]
    },
    "cost": {
      "coinsUsed": 3000,
      "dollarsUsed": 0.30,
      "operation": "impact-analysis"
    },
    "metadata": {
      "triggeredBy": "issue_comment",
      "duration": 180,
      "status": "success",
      "fixiumVersion": "1.0.0"
    },
    "impact": {
      "riskScore": 0.75,
      "riskLevel": "high",
      "directDependencies": 15,
      "downstreamImpact": 32,
      "testCoverage": {
        "status": "partial",
        "filesFound": 12,
        "needsUpdate": true
      },
      "apiEndpoints": {
        "total": 20,
        "new": 3,
        "modified": 8,
        "breaking": 2
      },
      "databaseChanges": {
        "tablesAffected": 5,
        "schemaChanges": true
      },
      "recommendationsCount": 15,
      "highPriorityRecommendations": 6,
      "affectedComponents": ["payment-processor", "billing-service"]
    }
  }' | jq '.'
```

### Test 4: Implement Fix Event

```bash
curl -X POST http://localhost:8000/api/v1/analytics \
  -H "Authorization: Bearer test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "implementfix",
    "github": {
      "type": "issue",
      "number": 45,
      "title": "Fix payment validation bug",
      "url": "https://github.com/test-org/test-repo/issues/45",
      "repository": "test-org/test-repo",
      "author": "developer",
      "branch": "",
      "baseBranch": "",
      "labels": ["bug", "payment"]
    },
    "cost": {
      "coinsUsed": 4000,
      "dollarsUsed": 0.40,
      "operation": "implement-fix"
    },
    "metadata": {
      "triggeredBy": "issue_comment",
      "duration": 240,
      "status": "success",
      "fixiumVersion": "1.0.0"
    },
    "fix": {
      "prNumber": 150,
      "prUrl": "https://github.com/test-org/test-repo/pull/150",
      "prTitle": "Fix: Payment validation bug (#45)",
      "branch": "fixium/issue-45-payment-validation",
      "filesModified": 5,
      "linesAdded": 250,
      "linesRemoved": 100,
      "testsAdded": 3,
      "fixComplexity": "moderate",
      "validationStatus": "passed",
      "implementationType": "bug-fix"
    }
  }' | jq '.'
```

**Note**: Fix schema requires:
- `filesModified` (not `filesChanged`)
- `linesAdded` and `linesRemoved` (auto-estimated)
- `fixComplexity` (low/medium/high based on files modified)
- The analytics_client automatically calculates these fields.

---

## Method 3: Test with Python Interactive Shell

```bash
cd /Users/hrishikeshpai/Documents/git_repos_old/code-review-workflow

# Set environment
export ANALYTICS_API_URL="http://localhost:8000"
export ANALYTICS_API_KEY="test-api-key-12345"
export ANALYTICS_ENABLED="true"

# Start Python
python3
```

```python
# In Python shell
from fixium.analytics_client import post_analytics_event

# Test simple event
event = {
    "eventType": "review",
    "github": {
        "type": "pr",
        "number": 1,
        "title": "Test",
        "url": "https://github.com/test/test/pull/1",
        "repository": "test/test",
        "author": "test",
        "branch": "test",
        "baseBranch": "main",
        "labels": []
    },
    "cost": {
        "coinsUsed": 100,
        "dollarsUsed": 0.01,
        "operation": "test"
    },
    "metadata": {
        "triggeredBy": "test",
        "duration": 1,
        "status": "success",
        "fixiumVersion": "1.0.0"
    },
    "review": {
        "totalFindings": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "filesReviewed": 0
    }
}

# Post event
result = post_analytics_event(event)
print(f"Success: {result}")
```

---

## Verify Events in Database

### Check MySQL Database

```bash
# Connect to MySQL container
podman exec -it autofix-system-mysql-1 mysql -u root -p

# Enter password: rootpassword

# In MySQL shell:
USE autofix_db;

# View all events
SELECT 
    id,
    event_type,
    github_type,
    github_number,
    github_title,
    cost_coins_used,
    cost_dollars_used,
    created_at
FROM analytics_events
ORDER BY created_at DESC
LIMIT 10;

# View review details
SELECT 
    e.id,
    e.github_number,
    r.total_findings,
    r.critical,
    r.high,
    r.medium,
    r.low,
    r.files_reviewed
FROM analytics_events e
JOIN review_details r ON e.id = r.event_id
ORDER BY e.created_at DESC
LIMIT 5;

# View documentation details
SELECT 
    e.id,
    e.github_number,
    d.should_update,
    d.total_gaps,
    d.change_type,
    d.confidence
FROM analytics_events e
JOIN documentation_details d ON e.id = d.event_id
ORDER BY e.created_at DESC
LIMIT 5;

# View impact details
SELECT 
    e.id,
    e.github_number,
    i.risk_score,
    i.risk_level,
    i.direct_dependencies,
    i.downstream_impact
FROM analytics_events e
JOIN impact_details i ON e.id = i.event_id
ORDER BY e.created_at DESC
LIMIT 5;

# Exit MySQL
exit;
```

### Check via API

```bash
# Get recent events
curl -H "Authorization: Bearer test-api-key-12345" \
  "http://localhost:8000/api/v1/analytics?limit=10" | jq '.'

# Get specific event by ID
EVENT_ID="uuid-from-previous-response"
curl -H "Authorization: Bearer test-api-key-12345" \
  "http://localhost:8000/api/v1/analytics/$EVENT_ID" | jq '.'

# Get dashboard summary
curl -H "Authorization: Bearer test-api-key-12345" \
  "http://localhost:8000/api/v1/analytics/dashboard/summary" | jq '.'
```

---

## Troubleshooting

### Issue 1: Connection Refused

**Error**: `⚠️  Analytics network error (non-critical): Connection refused`

**Solution**:
```bash
# Check if AutoFix System is running
podman ps | grep autofix

# If not running, start it
cd /Users/hrishikeshpai/Documents/git_repos_old/autofix-system
podman-compose up -d

# Wait for services
sleep 30

# Test health
curl http://localhost:8000/health
```

### Issue 2: Authentication Failed

**Error**: `⚠️  Analytics API returned 401`

**Solution**:
```bash
# Check API key in AutoFix System .env file
cd /Users/hrishikeshpai/Documents/git_repos_old/autofix-system
cat .env | grep ANALYTICS_API_KEY

# Update your environment to match
export ANALYTICS_API_KEY="the-actual-key-from-env-file"
```

### Issue 3: Timeout

**Error**: `⚠️  Analytics API timeout (skipping)`

**Solution**:
```bash
# Check AutoFix System logs
cd /Users/hrishikeshpai/Documents/git_repos_old/autofix-system
podman-compose logs -f autofix-system

# Check MySQL is responding
podman exec autofix-system-mysql-1 mysqladmin ping -h localhost -u root -p
```

### Issue 4: Invalid Event Data

**Error**: `⚠️  Analytics API returned 422`

**Solution**:
```bash
# Get detailed error
curl -X POST http://localhost:8000/api/v1/analytics \
  -H "Authorization: Bearer test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{ your event data }' \
  -v

# Check the response body for validation errors

# Common validation issues:
# - fixComplexity must be: "simple", "moderate", or "complex" (not "low", "medium", "high")
# - riskLevel must be: "low", "medium", "medium-high", "high", or "critical"
# - classificationType must be: "major" or "minor"
# Common issues:
# - github.type must be "pr" or "issue" (not "pull_request")
# - impact.riskScore must be 0.0-1.0 (not percentage)
# - review.linesReviewed is required (added in latest version)
# - All required fields must be present
```

**Recent Fixes**:

1. **Review events**: Added `linesReviewed` field (auto-calculated as filesReviewed × 100)

2. **Documentation events**: Restructured to match schema:
   - Added `classification` object with type, confidence, reasoning
   - Renamed `totalDocsAnalyzed` → `filesAnalyzed`
   - Added `suggestionsCount`, `highPriority`, `mediumPriority`, `lowPriority`
   - Added `affectedFiles` list and `forced` flag

3. **Implement fix events**: Added required fields:
   - Renamed `filesChanged` → `filesModified`
   - Added `linesAdded` (estimated as filesModified × 50)
   - Added `linesRemoved` (estimated as filesModified × 20)
   - Added `fixComplexity` (low/medium/high based on files modified)

The `analytics_client.py` has been updated to handle all required fields automatically.

---

## Quick Test Commands

### One-Line Test

```bash
cd /Users/hrishikeshpai/Documents/git_repos_old/code-review-workflow && \
export ANALYTICS_API_URL="http://localhost:8000" && \
export ANALYTICS_API_KEY="test-api-key-12345" && \
export ANALYTICS_ENABLED="true" && \
python test_analytics_integration.py
```

### Test Specific Event Type

```bash
# Test only review events
python -c "
import os
os.environ['ANALYTICS_API_URL'] = 'http://localhost:8000'
os.environ['ANALYTICS_API_KEY'] = 'test-api-key-12345'
from test_analytics_integration import test_review_event
test_review_event()
"
```

---

## Next Steps

After successful local testing:

1. **Commit changes**:
```bash
git add .
git commit -m "feat: Add analytics integration with local testing"
git push
```

2. **Configure GitHub Secrets** for production:
   - Go to repository Settings → Secrets and variables → Actions
   - Add `ANALYTICS_API_URL` (production URL)
   - Add `ANALYTICS_API_KEY` (production key)

3. **Test in GitHub Actions**:
   - Create a test PR
   - Comment: `Fixium:review`
   - Check Actions logs for analytics posting

4. **Monitor production**:
   - Check AutoFix System logs
   - Query analytics database
   - View dashboard metrics

---

**Last Updated**: 2026-05-15  
**Status**: Ready for Testing
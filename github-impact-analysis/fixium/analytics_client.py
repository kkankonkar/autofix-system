"""Analytics client for posting events to AutoFix System Analytics API."""
import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime


# Configuration from environment variables
ANALYTICS_API_URL = os.getenv('ANALYTICS_API_URL', '')
ANALYTICS_API_KEY = os.getenv('ANALYTICS_API_KEY', '')
ANALYTICS_ENABLED = os.getenv('ANALYTICS_ENABLED', 'true').lower() == 'true'
ANALYTICS_TIMEOUT = 5  # seconds


def post_analytics_event(event_data: Dict[str, Any]) -> bool:
    """
    Post analytics event to AutoFix System (non-blocking, never raises exceptions).
    
    Args:
        event_data: Event payload dictionary
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not ANALYTICS_ENABLED:
            return False
        
        if not ANALYTICS_API_URL or not ANALYTICS_API_KEY:
            print("⚠️  Analytics not configured (skipping)")
            return False
        
        # POST with timeout
        response = requests.post(
            f"{ANALYTICS_API_URL}/api/v1/analytics",
            json=event_data,
            headers={
                "Authorization": f"Bearer {ANALYTICS_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=ANALYTICS_TIMEOUT
        )
        
        if response.status_code == 201:
            print("✅ Analytics event posted successfully")
            return True
        else:
            print(f"⚠️  Analytics API returned {response.status_code}")
            return False
            
    except requests.Timeout:
        print("⚠️  Analytics API timeout (skipping)")
        return False
    except requests.RequestException as e:
        print(f"⚠️  Analytics network error (non-critical): {e}")
        return False
    except Exception as e:
        print(f"⚠️  Analytics error (non-critical): {e}")
        return False


def build_review_event(
    pr_info: Any,
    cost_info: Any,
    review_data: Dict[str, Any],
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build event payload for code review.
    
    Args:
        pr_info: GitHub PR object
        cost_info: CostInfo object
        review_data: Review results dictionary
        metadata: Workflow metadata
        
    Returns:
        Event payload dictionary
    """
    # Extract review summary
    summary = review_data.get('summary', {})
    
    # Count files reviewed
    files_reviewed = set()
    for finding in review_data.get('findings', []):
        for comment in finding.get('comments', []):
            if 'file' in comment:
                files_reviewed.add(comment['file'])
    
    # Estimate lines reviewed (rough estimate: 100 lines per file)
    lines_reviewed = len(files_reviewed) * 100
    
    return {
        "eventType": "review",
        "github": {
            "type": "pr",
            "number": pr_info.number,
            "title": pr_info.title,
            "url": pr_info.html_url,
            "repository": pr_info.base.repo.full_name,
            "author": pr_info.user.login,
            "branch": pr_info.head.ref,
            "baseBranch": pr_info.base.ref,
            "labels": [label.name for label in pr_info.labels]
        },
        "cost": {
            "coinsUsed": float(cost_info.coins_used) if cost_info else 0.0,
            "dollarsUsed": float(cost_info.dollars_used) if cost_info else 0.0,
            "operation": cost_info.operation if cost_info else "code-review"
        },
        "metadata": {
            "triggeredBy": metadata.get('triggeredBy', 'pull_request'),
            "duration": metadata.get('duration', 0),
            "status": metadata.get('status', 'success'),
            "fixiumVersion": metadata.get('fixiumVersion', '1.0.0')
        },
        "review": {
            "totalFindings": summary.get('totalFindings', 0),
            "critical": summary.get('critical', 0),
            "high": summary.get('high', 0),
            "medium": summary.get('medium', 0),
            "low": summary.get('low', 0),
            "filesReviewed": len(files_reviewed),
            "linesReviewed": lines_reviewed
        }
    }


def build_docs_event(
    pr_info: Any,
    cost_info: Any,
    docs_data: Dict[str, Any],
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build event payload for documentation analysis.
    
    Args:
        pr_info: GitHub PR object
        cost_info: CostInfo object
        docs_data: Documentation analysis results
        metadata: Workflow metadata
        
    Returns:
        Event payload dictionary
    """
    summary = docs_data.get('summary', {})
    classification = docs_data.get('changeClassification', {})
    
    # Count gaps by priority
    gaps_by_priority = {
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0
    }
    for gap in docs_data.get('documentationGaps', []):
        priority = gap.get('priority', 'low')
        if priority in gaps_by_priority:
            gaps_by_priority[priority] += 1
    
    # Total suggestions count
    total_suggestions = summary.get('totalGaps', 0)
    
    return {
        "eventType": "updatedocs",
        "github": {
            "type": "pr",
            "number": pr_info.number,
            "title": pr_info.title,
            "url": pr_info.html_url,
            "repository": pr_info.base.repo.full_name,
            "author": pr_info.user.login,
            "branch": pr_info.head.ref,
            "baseBranch": pr_info.base.ref,
            "labels": [label.name for label in pr_info.labels]
        },
        "cost": {
            "coinsUsed": float(cost_info.coins_used) if cost_info else 0.0,
            "dollarsUsed": float(cost_info.dollars_used) if cost_info else 0.0,
            "operation": cost_info.operation if cost_info else "doc-analysis"
        },
        "metadata": {
            "triggeredBy": metadata.get('triggeredBy', 'pull_request'),
            "duration": metadata.get('duration', 0),
            "status": metadata.get('status', 'success'),
            "fixiumVersion": metadata.get('fixiumVersion', '1.0.0')
        },
        "documentation": {
            "classification": {
                "type": classification.get('type', 'unknown'),
                "confidence": classification.get('confidence', 'unknown'),
                "reasoning": classification.get('reasoning', '')
            },
            "filesAnalyzed": summary.get('totalDocsDiscovered', 0),
            "suggestionsCount": total_suggestions,
            "highPriority": gaps_by_priority['critical'] + gaps_by_priority['high'],
            "mediumPriority": gaps_by_priority['medium'],
            "lowPriority": gaps_by_priority['low'],
            "affectedFiles": [gap.get('file', '') for gap in docs_data.get('documentationGaps', [])[:10]],
            "forced": False
        }
    }


def build_impact_event(
    issue_info: Any,
    cost_info: Any,
    impact_data: Dict[str, Any],
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build event payload for impact analysis.
    
    Args:
        issue_info: GitHub Issue object
        cost_info: CostInfo object
        impact_data: Impact analysis results
        metadata: Workflow metadata
        
    Returns:
        Event payload dictionary
    """
    impact = impact_data.get('impactAnalysis', {})
    risk = impact_data.get('riskAssessment', {})
    summary = impact_data.get('summary', {})
    
    # Extract test coverage info
    test_coverage_info = {
        "status": "unknown",
        "filesFound": 0,
        "needsUpdate": False
    }
    test_coverage = impact.get('testCoverage', [])
    if test_coverage:
        test_coverage_info['filesFound'] = len(test_coverage)
        test_coverage_info['needsUpdate'] = any(t.get('needsUpdate', False) for t in test_coverage)
        statuses = [t.get('status', 'unknown') for t in test_coverage]
        if 'missing' in statuses:
            test_coverage_info['status'] = 'missing'
        elif 'partial' in statuses or any(t.get('needsUpdate') for t in test_coverage):
            test_coverage_info['status'] = 'partial'
        else:
            test_coverage_info['status'] = 'complete'
    
    # Extract API endpoints info
    api_endpoints = impact.get('apiEndpoints', [])
    api_info = {
        "total": len(api_endpoints),
        "new": len([a for a in api_endpoints if a.get('status') == 'new']),
        "modified": len([a for a in api_endpoints if a.get('status') == 'modified']),
        "breaking": len([a for a in api_endpoints if a.get('breaking', False)])
    }
    
    # Extract database changes info
    db_impact = impact.get('databaseImpact', [])
    db_info = {
        "tablesAffected": len(db_impact),
        "schemaChanges": any(d.get('schemaChange', False) for d in db_impact)
    }
    
    # Extract affected components
    affected_components = [
        comp.get('component', comp.get('path', 'unknown'))
        for comp in impact_data.get('affectedComponents', [])
    ]
    
    # Count recommendations by priority
    recommendations = impact_data.get('recommendations', [])
    high_priority_recs = len([r for r in recommendations if r.get('priority') == 'high'])
    
    return {
        "eventType": "analyzeimpact",
        "github": {
            "type": "issue",
            "number": issue_info.number,
            "title": issue_info.title,
            "url": issue_info.html_url,
            "repository": issue_info.repository.full_name,
            "author": issue_info.user.login,
            "branch": "",
            "baseBranch": "",
            "labels": [label.name for label in issue_info.labels]
        },
        "cost": {
            "coinsUsed": float(cost_info.coins_used) if cost_info else 0.0,
            "dollarsUsed": float(cost_info.dollars_used) if cost_info else 0.0,
            "operation": cost_info.operation if cost_info else "impact-analysis"
        },
        "metadata": {
            "triggeredBy": metadata.get('triggeredBy', 'issue_comment'),
            "duration": metadata.get('duration', 0),
            "status": metadata.get('status', 'success'),
            "fixiumVersion": metadata.get('fixiumVersion', '1.0.0')
        },
        "impact": {
            "riskScore": float(risk.get('score', 0.0)),
            "riskLevel": risk.get('level', 'unknown'),
            "directDependencies": len(impact.get('directDependencies', [])),
            "downstreamImpact": len(impact.get('downstreamImpact', [])),
            "testCoverage": test_coverage_info,
            "apiEndpoints": api_info,
            "databaseChanges": db_info,
            "recommendationsCount": len(recommendations),
            "highPriorityRecommendations": high_priority_recs,
            "affectedComponents": affected_components[:10]  # Limit to 10
        }
    }


def build_fix_event(
    issue_info: Any,
    pr_info: Any,
    cost_info: Any,
    fix_data: Dict[str, Any],
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build event payload for implement fix.
    
    Args:
        issue_info: GitHub Issue object
        pr_info: GitHub PR object (created)
        cost_info: CostInfo object
        fix_data: Code changes/fix data
        metadata: Workflow metadata
        
    Returns:
        Event payload dictionary
    """
    changes = fix_data.get('changes', [])
    tests_added = fix_data.get('tests_added', [])
    validation_status = fix_data.get('validation_status', 'unknown')
    
    # Determine implementation type from issue labels or title
    implementation_type = 'feature'
    if issue_info.labels:
        label_names = [label.name.lower() for label in issue_info.labels]
        if 'bug' in label_names:
            implementation_type = 'bug-fix'
        elif 'refactor' in label_names or 'refactoring' in label_names:
            implementation_type = 'refactor'
        elif 'enhancement' in label_names:
            implementation_type = 'enhancement'
    
    # Estimate lines added/removed (rough estimate: 50 lines per file)
    files_modified = len(changes)
    lines_added = files_modified * 50
    lines_removed = files_modified * 20
    
    # Determine fix complexity based on files changed
    # Must match AutoFix System FixComplexity enum: simple, moderate, complex
    if files_modified <= 2:
        fix_complexity = "simple"
    elif files_modified <= 5:
        fix_complexity = "moderate"
    else:
        fix_complexity = "complex"
    
    return {
        "eventType": "implementfix",
        "github": {
            "type": "issue",
            "number": issue_info.number,
            "title": issue_info.title,
            "url": issue_info.html_url,
            "repository": issue_info.repository.full_name,
            "author": issue_info.user.login,
            "branch": "",
            "baseBranch": "",
            "labels": [label.name for label in issue_info.labels]
        },
        "cost": {
            "coinsUsed": float(cost_info.coins_used) if cost_info else 0.0,
            "dollarsUsed": float(cost_info.dollars_used) if cost_info else 0.0,
            "operation": cost_info.operation if cost_info else "implement-fix"
        },
        "metadata": {
            "triggeredBy": metadata.get('triggeredBy', 'issue_comment'),
            "duration": metadata.get('duration', 0),
            "status": metadata.get('status', 'success'),
            "fixiumVersion": metadata.get('fixiumVersion', '1.0.0')
        },
        "fix": {
            "prNumber": pr_info.number,
            "prUrl": pr_info.html_url,
            "prTitle": pr_info.title,
            "branch": pr_info.head.ref,
            "filesModified": files_modified,
            "linesAdded": lines_added,
            "linesRemoved": lines_removed,
            "testsAdded": len(tests_added),
            "fixComplexity": fix_complexity,
            "validationStatus": validation_status,
            "implementationType": implementation_type
        }
    }


# Made with Bob
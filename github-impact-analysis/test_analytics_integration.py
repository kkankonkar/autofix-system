#!/usr/bin/env python3
"""
Test script for Analytics API integration.

This script tests the analytics_client module by posting test events
to a local AutoFix System instance.

Usage:
    python test_analytics_integration.py
"""

import os
import sys
from datetime import datetime

# Add fixium to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fixium.analytics_client import (
    post_analytics_event,
    build_review_event,
    build_docs_event,
    build_impact_event,
    build_fix_event
)
from fixium.cost_tracker import CostInfo


class MockPRInfo:
    """Mock GitHub PR object for testing."""
    def __init__(self):
        self.number = 123
        self.title = "Test PR: Add payment feature"
        self.html_url = "https://github.com/test-org/test-repo/pull/123"
        self.user = type('obj', (object,), {'login': 'test-developer'})()
        self.head = type('obj', (object,), {'ref': 'feature/payment'})()
        self.base = type('obj', (object,), {
            'ref': 'main',
            'repo': type('obj', (object,), {'full_name': 'test-org/test-repo'})()
        })()
        self.labels = [
            type('obj', (object,), {'name': 'enhancement'})(),
            type('obj', (object,), {'name': 'backend'})()
        ]


class MockIssueInfo:
    """Mock GitHub Issue object for testing."""
    def __init__(self):
        self.number = 45
        self.title = "Test Issue: Fix payment validation bug"
        self.html_url = "https://github.com/test-org/test-repo/issues/45"
        self.user = type('obj', (object,), {'login': 'test-developer'})()
        self.repository = type('obj', (object,), {'full_name': 'test-org/test-repo'})()
        self.labels = [
            type('obj', (object,), {'name': 'bug'})(),
            type('obj', (object,), {'name': 'payment'})()
        ]


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(success, message):
    """Print a formatted result."""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")


def test_configuration():
    """Test 1: Verify configuration."""
    print_header("Test 1: Configuration Check")
    
    api_url = os.getenv('ANALYTICS_API_URL', '')
    api_key = os.getenv('ANALYTICS_API_KEY', '')
    enabled = os.getenv('ANALYTICS_ENABLED', 'true').lower() == 'true'
    
    print(f"ANALYTICS_API_URL: {api_url or '(not set)'}")
    print(f"ANALYTICS_API_KEY: {'***' + api_key[-4:] if api_key else '(not set)'}")
    print(f"ANALYTICS_ENABLED: {enabled}")
    
    if not api_url or not api_key:
        print_result(False, "Configuration incomplete")
        print("\nTo configure, run:")
        print("  export ANALYTICS_API_URL='http://localhost:8000'")
        print("  export ANALYTICS_API_KEY='test-api-key-12345'")
        return False
    
    print_result(True, "Configuration complete")
    return True


def test_review_event():
    """Test 2: Post code review event."""
    print_header("Test 2: Code Review Event")
    
    # Create mock data
    pr_info = MockPRInfo()
    cost_info = CostInfo(coins_used=2500.0, dollars_used=0.25, operation="code-review")
    review_data = {
        'summary': {
            'totalFindings': 15,
            'critical': 2,
            'high': 4,
            'medium': 6,
            'low': 3
        },
        'findings': [
            {
                'severity': 'high',
                'comments': [
                    {'file': 'src/payment.py'},
                    {'file': 'src/validator.py'}
                ]
            },
            {
                'severity': 'medium',
                'comments': [
                    {'file': 'src/utils.py'}
                ]
            }
        ]
    }
    metadata = {
        'triggeredBy': 'pull_request',
        'duration': 120,
        'status': 'success',
        'fixiumVersion': '1.0.0'
    }
    
    # Build event
    print("Building review event...")
    event_data = build_review_event(pr_info, cost_info, review_data, metadata)
    
    print(f"Event type: {event_data['eventType']}")
    print(f"PR: #{event_data['github']['number']} - {event_data['github']['title']}")
    print(f"Findings: {event_data['review']['totalFindings']}")
    print(f"Files reviewed: {event_data['review']['filesReviewed']}")
    print(f"Lines reviewed: {event_data['review']['linesReviewed']}")
    print(f"Cost: {event_data['cost']['coinsUsed']} coins (${event_data['cost']['dollarsUsed']})")
    
    # Post event
    print("\nPosting to Analytics API...")
    success = post_analytics_event(event_data)
    
    print_result(success, "Review event posted" if success else "Failed to post review event")
    return success


def test_docs_event():
    """Test 3: Post documentation event."""
    print_header("Test 3: Documentation Event")
    
    # Create mock data
    pr_info = MockPRInfo()
    cost_info = CostInfo(coins_used=1500.0, dollars_used=0.15, operation="doc-analysis")
    docs_data = {
        'shouldUpdateDocs': True,
        'summary': {
            'totalGaps': 5,
            'totalDocsDiscovered': 12
        },
        'changeClassification': {
            'type': 'major',
            'confidence': 'high',
            'reasoning': 'New feature with multiple new files'
        },
        'documentationGaps': [
            {'priority': 'critical', 'file': 'README.md'},
            {'priority': 'high', 'file': 'API.md'},
            {'priority': 'high', 'file': 'SETUP.md'},
            {'priority': 'medium', 'file': 'CONTRIBUTING.md'},
            {'priority': 'low', 'file': 'FAQ.md'}
        ]
    }
    metadata = {
        'triggeredBy': 'pull_request',
        'duration': 90,
        'status': 'success',
        'fixiumVersion': '1.0.0'
    }
    
    # Build event
    print("Building documentation event...")
    event_data = build_docs_event(pr_info, cost_info, docs_data, metadata)
    
    print(f"Event type: {event_data['eventType']}")
    print(f"PR: #{event_data['github']['number']} - {event_data['github']['title']}")
    print(f"Files analyzed: {event_data['documentation']['filesAnalyzed']}")
    print(f"Suggestions: {event_data['documentation']['suggestionsCount']}")
    print(f"High priority: {event_data['documentation']['highPriority']}")
    
    # Post event
    print("\nPosting to Analytics API...")
    success = post_analytics_event(event_data)
    
    print_result(success, "Documentation event posted" if success else "Failed to post documentation event")
    return success


def test_impact_event():
    """Test 4: Post impact analysis event."""
    print_header("Test 4: Impact Analysis Event")
    
    # Create mock data
    issue_info = MockIssueInfo()
    cost_info = CostInfo(coins_used=3000.0, dollars_used=0.30, operation="impact-analysis")
    impact_data = {
        'impactAnalysis': {
            'directDependencies': [
                {'path': 'src/payment.py', 'relationship': 'imports'},
                {'path': 'src/billing.py', 'relationship': 'imports'}
            ],
            'downstreamImpact': [
                {'path': 'src/api.py', 'relationship': 'uses'},
                {'path': 'src/service.py', 'relationship': 'uses'}
            ],
            'testCoverage': [
                {'path': 'tests/test_payment.py', 'status': 'exists', 'needsUpdate': True}
            ],
            'apiEndpoints': [
                {'endpoint': '/api/payment', 'method': 'POST', 'status': 'modified', 'breaking': True}
            ],
            'databaseImpact': [
                {'table': 'payments', 'operation': 'ALTER', 'schemaChange': True}
            ]
        },
        'riskAssessment': {
            'score': 0.75,
            'level': 'high'
        },
        'summary': {},
        'affectedComponents': [
            {'component': 'payment-processor', 'path': 'src/payment.py'},
            {'component': 'billing-service', 'path': 'src/billing.py'}
        ],
        'recommendations': [
            {'priority': 'high', 'action': 'Update tests'},
            {'priority': 'high', 'action': 'Review API changes'},
            {'priority': 'medium', 'action': 'Update documentation'}
        ]
    }
    metadata = {
        'triggeredBy': 'issue_comment',
        'duration': 180,
        'status': 'success',
        'fixiumVersion': '1.0.0'
    }
    
    # Build event
    print("Building impact analysis event...")
    event_data = build_impact_event(issue_info, cost_info, impact_data, metadata)
    
    print(f"Event type: {event_data['eventType']}")
    print(f"Issue: #{event_data['github']['number']} - {event_data['github']['title']}")
    print(f"Risk: {event_data['impact']['riskLevel']} ({event_data['impact']['riskScore']})")
    print(f"Dependencies: {event_data['impact']['directDependencies']} direct, {event_data['impact']['downstreamImpact']} downstream")
    
    # Post event
    print("\nPosting to Analytics API...")
    success = post_analytics_event(event_data)
    
    print_result(success, "Impact event posted" if success else "Failed to post impact event")
    return success


def test_fix_event():
    """Test 5: Post implement fix event."""
    print_header("Test 5: Implement Fix Event")
    
    # Create mock data
    issue_info = MockIssueInfo()
    pr_info = MockPRInfo()
    pr_info.number = 150
    pr_info.title = "Fix: Payment validation bug (#45)"
    pr_info.html_url = "https://github.com/test-org/test-repo/pull/150"
    pr_info.head.ref = "fixium/issue-45-payment-validation"
    
    cost_info = CostInfo(coins_used=4000.0, dollars_used=0.40, operation="implement-fix")
    fix_data = {
        'changes': [
            {'file': 'src/payment.py'},
            {'file': 'src/validator.py'},
            {'file': 'src/utils.py'}
        ],
        'tests_added': [
            {'file': 'tests/test_payment.py'},
            {'file': 'tests/test_validator.py'}
        ],
        'validation_status': 'passed'
    }
    metadata = {
        'triggeredBy': 'issue_comment',
        'duration': 240,
        'status': 'success',
        'fixiumVersion': '1.0.0'
    }
    
    # Build event
    print("Building implement fix event...")
    event_data = build_fix_event(issue_info, pr_info, cost_info, fix_data, metadata)
    
    print(f"Event type: {event_data['eventType']}")
    print(f"Issue: #{event_data['github']['number']} - {event_data['github']['title']}")
    print(f"PR: #{event_data['fix']['prNumber']} - {event_data['fix']['prTitle']}")
    print(f"Files modified: {event_data['fix']['filesModified']}")
    print(f"Lines: +{event_data['fix']['linesAdded']} -{event_data['fix']['linesRemoved']}")
    print(f"Tests added: {event_data['fix']['testsAdded']}")
    print(f"Complexity: {event_data['fix']['fixComplexity']}")
    
    # Post event
    print("\nPosting to Analytics API...")
    success = post_analytics_event(event_data)
    
    print_result(success, "Fix event posted" if success else "Failed to post fix event")
    return success


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  Analytics Integration Test Suite")
    print("=" * 70)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    
    # Test 1: Configuration
    if not test_configuration():
        print("\n❌ Tests aborted: Configuration incomplete")
        sys.exit(1)
    
    # Run all event tests
    results = {
        'review': test_review_event(),
        'docs': test_docs_event(),
        'impact': test_impact_event(),
        'fix': test_fix_event()
    }
    
    # Summary
    print_header("Test Summary")
    total = len(results)
    passed = sum(1 for success in results.values() if success)
    
    for event_type, success in results.items():
        print_result(success, f"{event_type.capitalize()} event")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == '__main__':
    main()

# Made with Bob

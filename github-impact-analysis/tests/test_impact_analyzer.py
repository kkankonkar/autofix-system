"""Tests for impact analyzer module."""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from fixium.impact_analyzer import (
    ImpactAnalyzer,
    ImpactAnalysis,
    Dependency,
    TestCoverage,
    APIEndpoint,
    DatabaseImpact,
    RiskFactor,
    Recommendation
)


@pytest.fixture
def mock_github():
    """Create mock GitHub client."""
    github = Mock()
    repo = Mock()
    github.get_repo.return_value = repo
    return github


@pytest.fixture
def mock_issue():
    """Create mock GitHub issue."""
    issue = Mock()
    issue.number = 123
    issue.title = "Add payment refund functionality"
    issue.body = """
    Add refund capability to PaymentProcessor class.
    
    Affected files:
    - src/payment/processor.py
    - src/api/payment_routes.py
    
    Requirements:
    - Support full and partial refunds
    - Update payment status
    - Send notification on refund
    """
    issue.labels = []
    return issue


@pytest.fixture
def analyzer(mock_github):
    """Create ImpactAnalyzer instance."""
    return ImpactAnalyzer(mock_github, "owner/repo", "/tmp/workspace")


def test_extract_component_name(analyzer):
    """Test component name extraction from file path."""
    assert analyzer._extract_component_name("src/payment/processor.py") == "Processor"
    assert analyzer._extract_component_name("src/api/payment_routes.py") == "PaymentRoutes"
    assert analyzer._extract_component_name("src/models/user.py") == "User"


def test_infer_components_from_text(analyzer):
    """Test component inference from text."""
    title = "Add payment processing"
    body = "Implement payment gateway integration"
    
    components = analyzer._infer_components_from_text(title, body)
    
    assert len(components) > 0
    assert any(c['component'] == 'Payment' for c in components)


def test_calculate_risk_score_high_risk(analyzer):
    """Test risk score calculation for high-risk changes."""
    analysis = ImpactAnalysis(
        issue_number=123,
        issue_title="Test",
        affected_components=[{'path': 'src/payment/processor.py', 'component': 'Payment'}],
        downstream_impact=[Dependency("file.py", "file", "USES") for _ in range(15)],
        test_coverage=[],
        api_endpoints=[APIEndpoint("/api/payment", "POST", "new", breaking=True)]
    )
    
    score, factors = analyzer._calculate_risk_score(analysis)
    
    assert score > 0.6  # High risk
    assert len(factors) > 0
    assert any(f.impact == "high" for f in factors)


def test_calculate_risk_score_low_risk(analyzer):
    """Test risk score calculation for low-risk changes."""
    analysis = ImpactAnalysis(
        issue_number=123,
        issue_title="Test",
        affected_components=[{'path': 'src/utils/helper.py', 'component': 'Helper'}],
        downstream_impact=[Dependency("file.py", "file", "USES")],
        test_coverage=[TestCoverage("tests/test_helper.py", "exists", False)],
        api_endpoints=[]
    )
    
    score, factors = analyzer._calculate_risk_score(analysis)
    
    assert score < 0.4  # Low risk
    assert any(f.impact == "positive" for f in factors)


def test_get_risk_level(analyzer):
    """Test risk level categorization."""
    assert analyzer._get_risk_level(0.8) == "high"
    assert analyzer._get_risk_level(0.5) == "medium"
    assert analyzer._get_risk_level(0.2) == "low"


def test_generate_recommendations_no_tests(analyzer):
    """Test recommendations when tests are missing."""
    analysis = ImpactAnalysis(
        issue_number=123,
        issue_title="Test",
        affected_components=[],
        test_coverage=[],
        risk_score=0.5
    )
    
    issue_analysis = Mock()
    recommendations = analyzer._generate_recommendations(analysis, issue_analysis)
    
    assert len(recommendations) > 0
    assert any(r.category == "testing" for r in recommendations)
    assert any(r.priority == "high" for r in recommendations)


def test_generate_recommendations_api_changes(analyzer):
    """Test recommendations for API changes."""
    analysis = ImpactAnalysis(
        issue_number=123,
        issue_title="Test",
        affected_components=[],
        api_endpoints=[APIEndpoint("/api/test", "POST", "new", False)],
        risk_score=0.5
    )
    
    issue_analysis = Mock()
    recommendations = analyzer._generate_recommendations(analysis, issue_analysis)
    
    assert any(r.category == "documentation" for r in recommendations)
    assert any("API" in r.action for r in recommendations)


def test_generate_recommendations_critical_component(analyzer):
    """Test recommendations for critical components."""
    analysis = ImpactAnalysis(
        issue_number=123,
        issue_title="Test",
        affected_components=[{'path': 'src/payment/processor.py', 'component': 'Payment'}],
        risk_score=0.7
    )
    
    issue_analysis = Mock()
    recommendations = analyzer._generate_recommendations(analysis, issue_analysis)
    
    assert any(r.category == "security" for r in recommendations)


def test_assess_test_coverage(analyzer):
    """Test test coverage assessment."""
    # No coverage
    assert analyzer._assess_test_coverage([]) == "none"
    
    # Good coverage
    good_tests = [
        TestCoverage("test1.py", "exists", False),
        TestCoverage("test2.py", "exists", False)
    ]
    assert analyzer._assess_test_coverage(good_tests) == "good"
    
    # Partial coverage
    partial_tests = [
        TestCoverage("test1.py", "exists", True),
        TestCoverage("test2.py", "missing", False)
    ]
    assert analyzer._assess_test_coverage(partial_tests) == "partial"


def test_estimate_effort(analyzer):
    """Test effort estimation."""
    high_risk = ImpactAnalysis(
        issue_number=123,
        issue_title="Test",
        affected_components=[],
        risk_score=0.8
    )
    assert analyzer._estimate_effort(high_risk) == "high"
    
    medium_risk = ImpactAnalysis(
        issue_number=123,
        issue_title="Test",
        affected_components=[],
        risk_score=0.5
    )
    assert analyzer._estimate_effort(medium_risk) == "medium"
    
    low_risk = ImpactAnalysis(
        issue_number=123,
        issue_title="Test",
        affected_components=[],
        risk_score=0.2
    )
    assert analyzer._estimate_effort(low_risk) == "low"


def test_recommend_approach(analyzer):
    """Test approach recommendation."""
    high_risk = ImpactAnalysis(
        issue_number=123,
        issue_title="Test",
        affected_components=[],
        risk_score=0.8
    )
    approach = analyzer._recommend_approach(high_risk)
    assert "feature flag" in approach.lower()
    
    low_risk = ImpactAnalysis(
        issue_number=123,
        issue_title="Test",
        affected_components=[],
        risk_score=0.2
    )
    approach = analyzer._recommend_approach(low_risk)
    assert "standard" in approach.lower()


def test_build_summary(analyzer):
    """Test summary building."""
    analysis = ImpactAnalysis(
        issue_number=123,
        issue_title="Test",
        affected_components=[],
        direct_dependencies=[Dependency("f1.py", "file", "IMPORTS")],
        downstream_impact=[Dependency("f2.py", "file", "USES"), Dependency("f3.py", "file", "USES")],
        test_coverage=[TestCoverage("test.py", "exists", False)],
        api_endpoints=[APIEndpoint("/api/test", "GET", "new")],
        risk_score=0.5
    )
    
    summary = analyzer._build_summary(analysis)
    
    assert summary['totalDirectDependencies'] == 1
    assert summary['totalDownstreamImpact'] == 2
    assert summary['testCoverageStatus'] == 'good'
    assert summary['apiChanges'] == 1
    assert summary['estimatedEffort'] == 'medium'
    assert 'recommendedApproach' in summary


def test_fallback_analysis(analyzer):
    """Test fallback analysis when Neo4j fails."""
    components = [
        {'path': 'src/payment/processor.py', 'component': 'Payment'},
        {'path': 'src/api/routes.py', 'component': 'Routes'}
    ]
    
    result = analyzer._fallback_analysis(components)
    
    assert 'test_coverage' in result
    assert len(result['test_coverage']) > 0
    assert all(isinstance(t, TestCoverage) for t in result['test_coverage'])


def test_impact_analysis_to_dict():
    """Test ImpactAnalysis to_dict conversion."""
    analysis = ImpactAnalysis(
        issue_number=123,
        issue_title="Test Issue",
        affected_components=[{'path': 'test.py', 'component': 'Test'}],
        direct_dependencies=[Dependency("dep.py", "file", "IMPORTS", "Test dependency")],
        risk_score=0.5,
        risk_level="medium",
        risk_factors=[RiskFactor("Test factor", "medium", 0.2)],
        recommendations=[Recommendation("high", "testing", "Add tests", "Need coverage")]
    )
    
    result = analysis.to_dict()
    
    assert result['issueNumber'] == 123
    assert result['issueTitle'] == "Test Issue"
    assert 'impactAnalysis' in result
    assert 'riskAssessment' in result
    assert 'recommendations' in result
    assert result['riskAssessment']['score'] == 0.5
    assert result['riskAssessment']['level'] == "medium"


@patch('subprocess.run')
def test_query_neo4j_impact_success(mock_run, analyzer, mock_issue):
    """Test successful Neo4j query via Bob CLI."""
    # Mock successful Bob CLI response
    mock_response = {
        'impactAnalysis': {
            'directDependencies': [
                {'path': 'dep.py', 'type': 'file', 'relationship': 'IMPORTS', 'description': 'Test'}
            ],
            'downstreamImpact': [],
            'testCoverage': [],
            'apiEndpoints': [],
            'databaseImpact': []
        }
    }
    mock_run.return_value = Mock(
        returncode=0,
        stdout=json.dumps(mock_response)
    )
    
    components = [{'path': 'test.py', 'component': 'Test'}]
    result = analyzer._query_neo4j_impact(components, mock_issue)
    
    assert 'direct_dependencies' in result
    assert len(result['direct_dependencies']) == 1
    assert isinstance(result['direct_dependencies'][0], Dependency)


@patch('subprocess.run')
def test_query_neo4j_impact_failure(mock_run, analyzer, mock_issue):
    """Test Neo4j query failure fallback."""
    # Mock failed Bob CLI response
    mock_run.return_value = Mock(
        returncode=1,
        stderr="Connection error"
    )
    
    components = [{'path': 'test.py', 'component': 'Test'}]
    result = analyzer._query_neo4j_impact(components, mock_issue)
    
    # Should return fallback analysis
    assert 'test_coverage' in result
    assert isinstance(result, dict)


def test_parse_bob_response_complete(analyzer):
    """Test parsing complete Bob response."""
    response = {
        'impactAnalysis': {
            'directDependencies': [
                {'path': 'dep1.py', 'type': 'file', 'relationship': 'IMPORTS', 'description': 'Dep 1'}
            ],
            'downstreamImpact': [
                {'path': 'down1.py', 'type': 'file', 'relationship': 'USES', 'description': 'Down 1', 'depth': 2}
            ],
            'testCoverage': [
                {'path': 'test1.py', 'status': 'exists', 'needsUpdate': True}
            ],
            'apiEndpoints': [
                {'endpoint': '/api/test', 'method': 'POST', 'status': 'new', 'breaking': False}
            ],
            'databaseImpact': [
                {'table': 'users', 'operation': 'read/write', 'schemaChange': True}
            ]
        }
    }
    
    result = analyzer._parse_bob_response(response)
    
    assert len(result['direct_dependencies']) == 1
    assert len(result['downstream_impact']) == 1
    assert len(result['test_coverage']) == 1
    assert len(result['api_endpoints']) == 1
    assert len(result['database_impact']) == 1
    
    # Verify types
    assert isinstance(result['direct_dependencies'][0], Dependency)
    assert isinstance(result['downstream_impact'][0], Dependency)
    assert isinstance(result['test_coverage'][0], TestCoverage)
    assert isinstance(result['api_endpoints'][0], APIEndpoint)
    assert isinstance(result['database_impact'][0], DatabaseImpact)


def test_parse_bob_response_empty(analyzer):
    """Test parsing empty Bob response."""
    response = {}
    
    result = analyzer._parse_bob_response(response)
    
    assert result['direct_dependencies'] == []
    assert result['downstream_impact'] == []
    assert result['test_coverage'] == []
    assert result['api_endpoints'] == []
    assert result['database_impact'] == []


# Made with Bob
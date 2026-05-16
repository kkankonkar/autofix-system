"""Analyze code impact using Neo4j graph database via MCP."""
import os
import json
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from github import Github
from github.Issue import Issue

from .issue_analyzer import IssueAnalyzer
from .cost_tracker import CostTracker, CostInfo


@dataclass
class Dependency:
    """A code dependency."""
    path: str
    type: str
    relationship: str
    description: str = ""
    depth: int = 1


@dataclass
class TestCoverage:
    """Test coverage information."""
    path: str
    status: str  # exists, missing, needs_update
    needs_update: bool = False


@dataclass
class APIEndpoint:
    """API endpoint information."""
    endpoint: str
    method: str
    status: str  # new, modified, existing
    breaking: bool = False


@dataclass
class DatabaseImpact:
    """Database impact information."""
    table: str
    operation: str  # read, write, read/write
    schema_change: bool = False


@dataclass
class RiskFactor:
    """Risk assessment factor."""
    factor: str
    impact: str  # high, medium, low, positive
    weight: float


@dataclass
class Recommendation:
    """Action recommendation."""
    priority: str  # high, medium, low
    category: str  # testing, documentation, review, security, performance
    action: str
    rationale: str


@dataclass
class ImpactAnalysis:
    """Complete impact analysis result."""
    issue_number: int
    issue_title: str
    affected_components: List[Dict[str, Any]]
    direct_dependencies: List[Dependency] = field(default_factory=list)
    downstream_impact: List[Dependency] = field(default_factory=list)
    test_coverage: List[TestCoverage] = field(default_factory=list)
    api_endpoints: List[APIEndpoint] = field(default_factory=list)
    database_impact: List[DatabaseImpact] = field(default_factory=list)
    risk_score: float = 0.0
    risk_level: str = "low"
    risk_factors: List[RiskFactor] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)
    neo4j_queries: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    cost_info: CostInfo = field(default_factory=lambda: CostInfo(operation="impact analysis"))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'issueNumber': self.issue_number,
            'issueTitle': self.issue_title,
            'affectedComponents': self.affected_components,
            'impactAnalysis': {
                'directDependencies': [asdict(d) for d in self.direct_dependencies],
                'downstreamImpact': [asdict(d) for d in self.downstream_impact],
                'testCoverage': [asdict(t) for t in self.test_coverage],
                'apiEndpoints': [asdict(a) for a in self.api_endpoints],
                'databaseImpact': [asdict(d) for d in self.database_impact]
            },
            'riskAssessment': {
                'score': self.risk_score,
                'level': self.risk_level,
                'factors': [asdict(f) for f in self.risk_factors]
            },
            'recommendations': [asdict(r) for r in self.recommendations],
            'summary': self.summary,
            'neo4jQueries': self.neo4j_queries,
            'costInfo': self.cost_info.to_dict()
        }


class ImpactAnalyzer:
    """Analyze code impact using Neo4j graph database."""
    
    def __init__(self, github_client: Github, repo_name: str, workspace_dir: str):
        """
        Initialize impact analyzer.
        
        Args:
            github_client: PyGithub client instance
            repo_name: Repository name (owner/repo)
            workspace_dir: Workspace directory path
        """
        self.client = github_client
        self.repo = github_client.get_repo(repo_name)
        self.repo_name = repo_name
        self.workspace_dir = workspace_dir
        self.issue_analyzer = IssueAnalyzer(github_client, repo_name)
    
    def analyze_issue_impact(self, issue_number: int) -> ImpactAnalysis:
        """
        Analyze impact of changes described in an issue.
        
        Args:
            issue_number: GitHub issue number
            
        Returns:
            ImpactAnalysis object with complete analysis
        """
        # Get issue details
        issue = self.repo.get_issue(issue_number)
        
        # Analyze issue to extract affected components
        issue_analysis = self.issue_analyzer.analyze_issue(issue_number)
        
        # Build affected components list
        affected_components = []
        for file_path in issue_analysis.affected_files:
            affected_components.append({
                'path': file_path,
                'type': 'file',
                'component': self._extract_component_name(file_path),
                'confidence': 'high'
            })
        
        # If no explicit files, use issue title/body to infer components
        if not affected_components:
            inferred = self._infer_components_from_text(
                issue_analysis.title,
                issue_analysis.body
            )
            affected_components.extend(inferred)
        
        # Query Neo4j for impact analysis
        impact_data = self._query_neo4j_impact(affected_components, issue)
        
        # Build impact analysis
        analysis = ImpactAnalysis(
            issue_number=issue_number,
            issue_title=issue.title,
            affected_components=affected_components,
            direct_dependencies=impact_data.get('direct_dependencies', []),
            downstream_impact=impact_data.get('downstream_impact', []),
            test_coverage=impact_data.get('test_coverage', []),
            api_endpoints=impact_data.get('api_endpoints', []),
            database_impact=impact_data.get('database_impact', []),
            cost_info=impact_data.get('cost_info', CostInfo(operation="impact analysis"))
        )
        
        # Calculate risk score
        analysis.risk_score, analysis.risk_factors = self._calculate_risk_score(analysis)
        analysis.risk_level = self._get_risk_level(analysis.risk_score)
        
        # Generate recommendations
        analysis.recommendations = self._generate_recommendations(analysis, issue_analysis)
        
        # Build summary
        analysis.summary = self._build_summary(analysis)
        
        return analysis
    
    def _extract_component_name(self, file_path: str) -> str:
        """Extract component name from file path."""
        # Get filename without extension
        filename = os.path.basename(file_path)
        name = os.path.splitext(filename)[0]
        
        # Convert to PascalCase for class names
        parts = name.replace('_', ' ').replace('-', ' ').split()
        return ''.join(word.capitalize() for word in parts)
    
    def _infer_components_from_text(self, title: str, body: str) -> List[Dict[str, Any]]:
        """Infer affected components from issue text."""
        components = []
        text = f"{title} {body}".lower()
        
        # Common component patterns
        patterns = {
            'payment': {'path': 'src/payment/', 'type': 'module'},
            'auth': {'path': 'src/auth/', 'type': 'module'},
            'api': {'path': 'src/api/', 'type': 'module'},
            'database': {'path': 'src/models/', 'type': 'module'},
            'user': {'path': 'src/user/', 'type': 'module'},
        }
        
        for keyword, info in patterns.items():
            if keyword in text:
                components.append({
                    'path': info['path'],
                    'type': info['type'],
                    'component': keyword.capitalize(),
                    'confidence': 'medium'
                })
        
        return components
    
    def _query_neo4j_impact(
        self,
        affected_components: List[Dict[str, Any]],
        issue: Issue
    ) -> Dict[str, Any]:
        """
        Query Neo4j via Bob CLI MCP to get impact data.
        
        This method invokes Bob CLI with the analyze-impact prompt
        to query Neo4j and analyze the impact.
        
        Args:
            affected_components: List of affected components
            issue: GitHub Issue object
            
        Returns:
            Dictionary with impact data
        """
        # Prepare context for Bob CLI
        context = {
            'issue_number': issue.number,
            'issue_title': issue.title,
            'issue_body': issue.body or "",
            'affected_components': affected_components,
            'repository': self.repo_name
        }
        
        # Create temporary context file
        context_file = os.path.join(self.workspace_dir, f'impact_context_{issue.number}.json')
        with open(context_file, 'w') as f:
            json.dump(context, f, indent=2)
        
        try:
            # Read the analyze-impact prompt
            prompt_file = os.path.join(
                os.path.dirname(__file__),
                '..',
                'prompts',
                'analyze-impact.md'
            )
            
            with open(prompt_file, 'r') as f:
                prompt_template = f.read()
            
            # Build the complete prompt with context
            full_prompt = f"""{prompt_template}

## Issue Context

**Issue Number**: {context['issue_number']}
**Issue Title**: {context['issue_title']}
**Repository**: {context['repository']}

**Issue Description**:
{context['issue_body']}

**Affected Components**:
{json.dumps(context['affected_components'], indent=2)}

## Task

Analyze the impact of this issue using the Neo4j MCP server. Query the graph database to find:
1. Direct dependencies
2. Downstream impact (components that depend on affected files)
3. Test coverage
4. API endpoints affected
5. Database schema impact

Return the analysis in JSON format as specified in the prompt template above.
"""
            
            # Build Bob CLI command with prompt via stdin
            cmd = ['bob', '-p', full_prompt]
            
            # Execute Bob CLI
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.workspace_dir,
                timeout=300  # 5 minute timeout
            )
            
            # Extract cost information from output
            combined_output = result.stdout + result.stderr
            cost_info = CostTracker.extract_costs(combined_output, "impact analysis")
            
            if result.returncode == 0:
                # Try to parse Bob's response as JSON
                try:
                    # Bob might return markdown with JSON, extract it
                    output = result.stdout
                    # Look for JSON in the output
                    json_start = output.find('{')
                    json_end = output.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = output[json_start:json_end]
                        response = json.loads(json_str)
                        impact_data = self._parse_bob_response(response)
                        impact_data['cost_info'] = cost_info
                        return impact_data
                    else:
                        print(f"⚠️  Could not find JSON in Bob's response")
                        fallback = self._fallback_analysis(affected_components)
                        fallback['cost_info'] = cost_info
                        return fallback
                except json.JSONDecodeError as e:
                    print(f"⚠️  Failed to parse Bob's response as JSON: {e}")
                    fallback = self._fallback_analysis(affected_components)
                    fallback['cost_info'] = cost_info
                    return fallback
            else:
                print(f"⚠️  Bob CLI error: {result.stderr}")
                fallback = self._fallback_analysis(affected_components)
                fallback['cost_info'] = cost_info
                return fallback
                
        except subprocess.TimeoutExpired:
            print("⚠️  Bob CLI timeout - using fallback analysis")
            return self._fallback_analysis(affected_components)
        except Exception as e:
            print(f"⚠️  Error querying Neo4j: {e}")
            return self._fallback_analysis(affected_components)
        finally:
            # Cleanup context file
            if os.path.exists(context_file):
                os.remove(context_file)
    
    def _parse_bob_response(self, response: Dict) -> Dict[str, Any]:
        """Parse Bob CLI response into impact data."""
        impact_data = {
            'direct_dependencies': [],
            'downstream_impact': [],
            'test_coverage': [],
            'api_endpoints': [],
            'database_impact': [],
            'cost_info': CostInfo(operation="impact analysis")
        }
        
        # Extract impact analysis from response
        if 'impactAnalysis' in response:
            analysis = response['impactAnalysis']
            
            # Parse direct dependencies
            for dep in analysis.get('directDependencies', []):
                impact_data['direct_dependencies'].append(Dependency(
                    path=dep.get('path', ''),
                    type=dep.get('type', 'unknown'),
                    relationship=dep.get('relationship', 'DEPENDS_ON'),
                    description=dep.get('description', '')
                ))
            
            # Parse downstream impact
            for dep in analysis.get('downstreamImpact', []):
                impact_data['downstream_impact'].append(Dependency(
                    path=dep.get('path', ''),
                    type=dep.get('type', 'unknown'),
                    relationship=dep.get('relationship', 'USES'),
                    description=dep.get('description', ''),
                    depth=dep.get('depth', 1)
                ))
            
            # Parse test coverage
            for test in analysis.get('testCoverage', []):
                impact_data['test_coverage'].append(TestCoverage(
                    path=test.get('path', ''),
                    status=test.get('status', 'unknown'),
                    needs_update=test.get('needsUpdate', False)
                ))
            
            # Parse API endpoints
            for api in analysis.get('apiEndpoints', []):
                impact_data['api_endpoints'].append(APIEndpoint(
                    endpoint=api.get('endpoint', ''),
                    method=api.get('method', 'GET'),
                    status=api.get('status', 'existing'),
                    breaking=api.get('breaking', False)
                ))
            
            # Parse database impact
            for db in analysis.get('databaseImpact', []):
                impact_data['database_impact'].append(DatabaseImpact(
                    table=db.get('table', ''),
                    operation=db.get('operation', 'read'),
                    schema_change=db.get('schemaChange', False)
                ))
        
        return impact_data
    
    def _fallback_analysis(self, affected_components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Provide fallback analysis when Neo4j query fails."""
        return {
            'direct_dependencies': [],
            'downstream_impact': [],
            'test_coverage': [
                TestCoverage(
                    path=f"tests/test_{comp['component'].lower()}.py",
                    status='unknown',
                    needs_update=True
                )
                for comp in affected_components[:3]
            ],
            'api_endpoints': [],
            'database_impact': [],
            'cost_info': CostInfo(operation="impact analysis (fallback)")
        }
    
    def _calculate_risk_score(self, analysis: ImpactAnalysis) -> tuple[float, List[RiskFactor]]:
        """
        Calculate risk score based on impact analysis.
        
        Returns:
            Tuple of (risk_score, risk_factors)
        """
        factors = []
        score = 0.0
        
        # Factor 1: Downstream dependencies
        downstream_count = len(analysis.downstream_impact)
        if downstream_count > 10:
            weight = 0.30
            factors.append(RiskFactor(
                factor="Many downstream dependencies",
                impact="high",
                weight=weight
            ))
            score += weight
        elif downstream_count > 5:
            weight = 0.20
            factors.append(RiskFactor(
                factor="Moderate downstream dependencies",
                impact="medium",
                weight=weight
            ))
            score += weight
        elif downstream_count > 0:
            weight = 0.10
            factors.append(RiskFactor(
                factor="Few downstream dependencies",
                impact="low",
                weight=weight
            ))
            score += weight
        
        # Factor 2: Test coverage
        has_tests = len(analysis.test_coverage) > 0
        tests_need_update = any(t.needs_update for t in analysis.test_coverage)
        
        if not has_tests:
            weight = 0.30
            factors.append(RiskFactor(
                factor="No test coverage found",
                impact="high",
                weight=weight
            ))
            score += weight
        elif tests_need_update:
            weight = 0.15
            factors.append(RiskFactor(
                factor="Tests need updates",
                impact="medium",
                weight=weight
            ))
            score += weight
        else:
            weight = -0.15
            factors.append(RiskFactor(
                factor="Good test coverage",
                impact="positive",
                weight=weight
            ))
            score += weight
        
        # Factor 3: API changes
        api_changes = len(analysis.api_endpoints)
        breaking_changes = any(a.breaking for a in analysis.api_endpoints)
        
        if breaking_changes:
            weight = 0.25
            factors.append(RiskFactor(
                factor="Breaking API changes",
                impact="high",
                weight=weight
            ))
            score += weight
        elif api_changes > 0:
            weight = 0.15
            factors.append(RiskFactor(
                factor="API changes required",
                impact="medium",
                weight=weight
            ))
            score += weight
        
        # Factor 4: Database changes
        db_schema_changes = any(d.schema_change for d in analysis.database_impact)
        if db_schema_changes:
            weight = 0.20
            factors.append(RiskFactor(
                factor="Database schema changes",
                impact="high",
                weight=weight
            ))
            score += weight
        
        # Factor 5: Critical components (inferred from paths)
        critical_keywords = ['payment', 'auth', 'security', 'billing']
        has_critical = any(
            any(keyword in comp['path'].lower() for keyword in critical_keywords)
            for comp in analysis.affected_components
        )
        if has_critical:
            weight = 0.25
            factors.append(RiskFactor(
                factor="Critical component affected",
                impact="high",
                weight=weight
            ))
            score += weight
        
        # Clamp score to [0.0, 1.0]
        score = max(0.0, min(1.0, score))
        
        return score, factors
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to risk level."""
        if score >= 0.7:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(
        self,
        analysis: ImpactAnalysis,
        issue_analysis
    ) -> List[Recommendation]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Test coverage recommendations
        if not analysis.test_coverage or any(t.needs_update for t in analysis.test_coverage):
            recommendations.append(Recommendation(
                priority="high",
                category="testing",
                action="Add or update test coverage",
                rationale="Changes require comprehensive testing to prevent regressions"
            ))
        
        # API documentation recommendations
        if analysis.api_endpoints:
            recommendations.append(Recommendation(
                priority="high" if any(a.breaking for a in analysis.api_endpoints) else "medium",
                category="documentation",
                action="Update API documentation",
                rationale=f"{'Breaking changes' if any(a.breaking for a in analysis.api_endpoints) else 'New endpoints'} require documentation updates"
            ))
        
        # Downstream impact recommendations
        if len(analysis.downstream_impact) > 5:
            recommendations.append(Recommendation(
                priority="medium",
                category="review",
                action="Review downstream services for compatibility",
                rationale=f"{len(analysis.downstream_impact)} components depend on this change"
            ))
        
        # Database migration recommendations
        if any(d.schema_change for d in analysis.database_impact):
            recommendations.append(Recommendation(
                priority="high",
                category="database",
                action="Create database migration scripts",
                rationale="Schema changes require careful migration planning"
            ))
        
        # Security review for critical components
        critical_keywords = ['payment', 'auth', 'security']
        if any(
            any(keyword in comp['path'].lower() for keyword in critical_keywords)
            for comp in analysis.affected_components
        ):
            recommendations.append(Recommendation(
                priority="high",
                category="security",
                action="Conduct security review",
                rationale="Changes affect security-critical components"
            ))
        
        # Integration testing for complex changes
        if analysis.risk_score >= 0.6:
            recommendations.append(Recommendation(
                priority="medium",
                category="testing",
                action="Add integration tests",
                rationale="Complex changes benefit from end-to-end testing"
            ))
        
        return recommendations
    
    def _build_summary(self, analysis: ImpactAnalysis) -> Dict[str, Any]:
        """Build summary statistics."""
        return {
            'totalDirectDependencies': len(analysis.direct_dependencies),
            'totalDownstreamImpact': len(analysis.downstream_impact),
            'testCoverageStatus': self._assess_test_coverage(analysis.test_coverage),
            'apiChanges': len(analysis.api_endpoints),
            'databaseChanges': len(analysis.database_impact),
            'estimatedEffort': self._estimate_effort(analysis),
            'recommendedApproach': self._recommend_approach(analysis)
        }
    
    def _assess_test_coverage(self, test_coverage: List[TestCoverage]) -> str:
        """Assess overall test coverage status."""
        if not test_coverage:
            return "none"
        if all(t.status == "exists" and not t.needs_update for t in test_coverage):
            return "good"
        if any(t.status == "exists" for t in test_coverage):
            return "partial"
        return "missing"
    
    def _estimate_effort(self, analysis: ImpactAnalysis) -> str:
        """Estimate implementation effort."""
        if analysis.risk_score >= 0.7:
            return "high"
        elif analysis.risk_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _recommend_approach(self, analysis: ImpactAnalysis) -> str:
        """Recommend implementation approach."""
        if analysis.risk_score >= 0.7:
            return "Implement with feature flag, comprehensive testing, and staged rollout"
        elif analysis.risk_score >= 0.4:
            return "Implement with thorough testing and code review"
        else:
            return "Standard implementation with unit tests"


# Made with Bob
"""Main entry point for Fixium impact analysis."""
import os
import sys
import json
import time
from typing import Optional
from github import Github

from .impact_analyzer import ImpactAnalyzer
from .github_client import GitHubClient
from .access_control import AccessControl


def format_impact_comment(analysis_dict: dict) -> str:
    """
    Format impact analysis as GitHub comment markdown.
    
    Args:
        analysis_dict: Impact analysis dictionary
        
    Returns:
        Formatted markdown string
    """
    impact = analysis_dict.get('impactAnalysis', {})
    risk = analysis_dict.get('riskAssessment', {})
    recommendations = analysis_dict.get('recommendations', [])
    summary = analysis_dict.get('summary', {})
    cost_info_dict = analysis_dict.get('costInfo', {})
    
    # Build comment
    lines = [
        "## 🔍 Impact Analysis Results",
        "",
        f"**Issue**: #{analysis_dict['issueNumber']} - {analysis_dict['issueTitle']}",
        "",
        "### 📊 Summary",
        f"- **Risk Score**: {risk['score']:.2f} ({risk['level'].replace('-', ' ').title()})",
        f"- **Direct Dependencies**: {summary.get('totalDirectDependencies', 0)} files",
        f"- **Indirect Dependencies**: {summary.get('totalDownstreamImpact', 0)} files",
        f"- **Test Coverage**: {summary.get('testCoverageStatus', 'unknown').title()}",
        f"- **API Changes**: {summary.get('apiChanges', 0)} endpoints",
        ""
    ]
    
    # Affected Components
    if analysis_dict.get('affectedComponents'):
        lines.extend([
            "### 🎯 Affected Components",
            ""
        ])
        for comp in analysis_dict['affectedComponents'][:10]:
            confidence = comp.get('confidence', 'unknown')
            emoji = "🎯" if confidence == "high" else "📍" if confidence == "medium" else "❓"
            lines.append(f"- {emoji} `{comp['path']}` - {comp.get('component', 'Unknown')}")
        lines.append("")
    
    # Direct Dependencies
    if impact.get('directDependencies'):
        lines.extend([
            "### 📦 Direct Dependencies",
            ""
        ])
        for dep in impact['directDependencies'][:10]:
            lines.append(f"- `{dep['path']}` ({dep['relationship']})")
            if dep.get('description'):
                lines.append(f"  - {dep['description']}")
        if len(impact['directDependencies']) > 10:
            lines.append(f"- ... and {len(impact['directDependencies']) - 10} more")
        lines.append("")
    
    # Downstream Impact
    if impact.get('downstreamImpact'):
        lines.extend([
            "### 🌊 Downstream Impact",
            ""
        ])
        for dep in impact['downstreamImpact'][:15]:
            depth_indicator = "  " * (dep.get('depth', 1) - 1)
            lines.append(f"- {depth_indicator}`{dep['path']}` ({dep['relationship']})")
            if dep.get('description'):
                lines.append(f"  {depth_indicator}- {dep['description']}")
        if len(impact['downstreamImpact']) > 15:
            lines.append(f"- ... and {len(impact['downstreamImpact']) - 15} more")
        lines.append("")
    
    # Test Coverage
    if impact.get('testCoverage'):
        lines.extend([
            "### 🧪 Test Coverage",
            ""
        ])
        for test in impact['testCoverage']:
            status_emoji = "✅" if test['status'] == "exists" else "❌" if test['status'] == "missing" else "⚠️"
            update_note = " ⚠️ Needs update" if test.get('needsUpdate') else ""
            lines.append(f"- {status_emoji} `{test['path']}`{update_note}")
        lines.append("")
    
    # API Endpoints
    if impact.get('apiEndpoints'):
        lines.extend([
            "### 🌐 API Endpoints Affected",
            ""
        ])
        for api in impact['apiEndpoints']:
            status_emoji = "🆕" if api['status'] == "new" else "🔄" if api['status'] == "modified" else "✅"
            breaking_note = " ⚠️ **BREAKING**" if api.get('breaking') else ""
            lines.append(f"- {status_emoji} `{api['method']} {api['endpoint']}`{breaking_note}")
        lines.append("")
    
    # Database Impact
    if impact.get('databaseImpact'):
        lines.extend([
            "### 💾 Database Impact",
            ""
        ])
        for db in impact['databaseImpact']:
            schema_note = " ⚠️ **Schema Change**" if db.get('schemaChange') else ""
            lines.append(f"- Table: `{db['table']}` ({db['operation']}){schema_note}")
        lines.append("")
    
    # Recommendations
    if recommendations:
        lines.extend([
            "### ⚠️ Recommendations",
            ""
        ])
        
        # Group by priority
        high_priority = [r for r in recommendations if r['priority'] == 'high']
        medium_priority = [r for r in recommendations if r['priority'] == 'medium']
        low_priority = [r for r in recommendations if r['priority'] == 'low']
        
        if high_priority:
            lines.append("**High Priority:**")
            for rec in high_priority:
                lines.append(f"- 🔴 **{rec['action']}**")
                lines.append(f"  - {rec['rationale']}")
            lines.append("")
        
        if medium_priority:
            lines.append("**Medium Priority:**")
            for rec in medium_priority:
                lines.append(f"- 🟡 **{rec['action']}**")
                lines.append(f"  - {rec['rationale']}")
            lines.append("")
        
        if low_priority:
            lines.append("**Low Priority:**")
            for rec in low_priority:
                lines.append(f"- 🔵 **{rec['action']}**")
                lines.append(f"  - {rec['rationale']}")
            lines.append("")
    
    # Risk Assessment
    lines.extend([
        "### 📈 Risk Assessment",
        f"**{risk['level'].replace('-', ' ').title()} Risk ({risk['score']:.2f}/1.0)**",
        ""
    ])
    
    if risk.get('factors'):
        lines.append("**Factors:**")
        for factor in risk['factors']:
            impact_emoji = "⚠️" if factor['impact'] == 'high' else "🟡" if factor['impact'] == 'medium' else "✅" if factor['impact'] == 'positive' else "🔵"
            weight_str = f"+{factor['weight']:.2f}" if factor['weight'] > 0 else f"{factor['weight']:.2f}"
            lines.append(f"- {impact_emoji} {factor['factor']} ({weight_str})")
        lines.append("")
    
    # Recommended Approach
    if summary.get('recommendedApproach'):
        lines.extend([
            "**Recommended Approach:**",
            summary['recommendedApproach'],
            ""
        ])
    
    # Cost Information
    if cost_info_dict and (cost_info_dict.get('coins_used', 0) > 0 or cost_info_dict.get('dollars_used', 0) > 0):
        lines.extend([
            "### 💰 Cost Information",
            "",
            f"**Bob Coins Used**: {cost_info_dict.get('coins_used', 0):,.2f} coins",
            f"**Estimated Cost**: ${cost_info_dict.get('dollars_used', 0):.4f}",
            ""
        ])
    
    # Footer
    lines.extend([
        "---",
        "*🤖 Generated by Fixium Impact Analyzer using Neo4j graph analysis*"
    ])
    
    return "\n".join(lines)


def main():
    """Main entry point for impact analysis workflow."""
    # Track start time for analytics
    start_time = time.time()
    
    # Get environment variables
    github_token = os.getenv('GITHUB_TOKEN')
    repo_name = os.getenv('GITHUB_REPOSITORY')
    issue_number = int(os.getenv('ISSUE_NUMBER', '0'))
    comment_user = os.getenv('COMMENT_USER', '')
    workspace_dir = os.getenv('GITHUB_WORKSPACE', os.getcwd())
    
    # Validate required environment variables
    if not github_token:
        print("❌ Error: GITHUB_TOKEN not set")
        sys.exit(1)
    
    if not repo_name:
        print("❌ Error: GITHUB_REPOSITORY not set")
        sys.exit(1)
    
    if not issue_number:
        print("❌ Error: ISSUE_NUMBER not set")
        sys.exit(1)
    
    # Validate Neo4j configuration
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_username = os.getenv('NEO4J_USERNAME')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    
    if not all([neo4j_uri, neo4j_username, neo4j_password]):
        print("⚠️  Warning: Neo4j credentials not fully configured")
        print("   Impact analysis will use fallback mode")
    
    print(f"🤖 Fixium Impact Analysis")
    print(f"📋 Repository: {repo_name}")
    print(f"🎫 Issue: #{issue_number}")
    print(f"👤 Triggered by: {comment_user}")
    print()
    
    try:
        # Initialize GitHub client
        print("🔌 Connecting to GitHub...")
        github_client = GitHubClient(token=github_token, repository=repo_name)
        github = Github(github_token)
        
        # Check authorization
        print(f"🔐 Checking authorization for {comment_user}...")
        access_control = AccessControl()
        if not access_control.is_authorized(comment_user):
            error_msg = f"❌ User {comment_user} is not authorized to use Fixium:analyzeimpact"
            print(error_msg)
            
            # Comment on issue
            github_client.post_issue_comment(
                issue_number,
                f"⚠️ **Authorization Failed**\n\n{error_msg}\n\n"
                f"Please contact a repository administrator to be added to the authorized users list."
            )
            sys.exit(1)
        
        print(f"✅ User {comment_user} is authorized")
        print()
        
        # Post initial comment
        initial_comment = github_client.post_issue_comment(
            issue_number,
            "🤖 **Fixium Impact Analysis Started**\n\n"
            "I'm analyzing the potential impact of this issue using Neo4j graph database.\n\n"
            "**Status**: Analyzing issue and querying code graph..."
        )
        comment_id = initial_comment.id
        
        # Perform Impact Analysis
        print("📊 Analyzing Impact")
        print("-" * 50)
        
        analyzer = ImpactAnalyzer(github, repo_name, workspace_dir)
        analysis = analyzer.analyze_issue_impact(issue_number)
        
        # Save analysis
        analysis_file = f"impact_analysis_issue{issue_number}.json"
        analysis_path = os.path.join(workspace_dir, analysis_file)
        with open(analysis_path, 'w') as f:
            json.dump(analysis.to_dict(), f, indent=2)
        
        print(f"   Risk Score: {analysis.risk_score:.2f} ({analysis.risk_level})")
        print(f"   Direct Dependencies: {len(analysis.direct_dependencies)}")
        print(f"   Downstream Impact: {len(analysis.downstream_impact)}")
        print(f"   Test Coverage: {len(analysis.test_coverage)}")
        print(f"   Recommendations: {len(analysis.recommendations)}")
        
        # Print cost information
        if analysis.cost_info and (analysis.cost_info.coins_used > 0 or analysis.cost_info.dollars_used > 0):
            print(f"   💰 Cost: {analysis.cost_info.coins_used:.2f} coins (${analysis.cost_info.dollars_used:.4f})")
        
        print()
        
        # Format and post results
        print("💬 Posting Impact Analysis")
        print("-" * 50)
        
        impact_comment = format_impact_comment(analysis.to_dict())
        github_client.update_comment(comment_id, impact_comment)
        
        print("✅ Impact Analysis Complete!")
        print(f"   Analysis saved to: {analysis_file}")
        print()
        
        # Post analytics event (non-blocking)
        try:
            from .analytics_client import build_impact_event, post_analytics_event
            
            issue = github_client.get_issue(issue_number)
            event_data = build_impact_event(
                issue_info=issue,
                cost_info=analysis.cost_info,
                impact_data=analysis.to_dict(),
                metadata={
                    'triggeredBy': 'issue_comment',
                    'duration': int(time.time() - start_time),
                    'status': 'success',
                    'fixiumVersion': '1.0.0'
                }
            )
            post_analytics_event(event_data)
        except Exception as e:
            print(f"⚠️  Analytics posting failed (non-critical): {e}")
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error: {error_msg}")
        
        # Try to update comment if we have comment_id
        try:
            if 'comment_id' in locals():
                github_client.update_comment(
                    comment_id,
                    f"❌ **Impact Analysis Failed**\n\n"
                    f"An error occurred while analyzing the impact:\n\n"
                    f"```\n{error_msg}\n```\n\n"
                    f"This could be due to:\n"
                    f"- Neo4j connection issues\n"
                    f"- Missing graph data\n"
                    f"- Insufficient issue context\n\n"
                    f"Please check the configuration and try again."
                )
        except:
            pass
        
        sys.exit(1)


if __name__ == '__main__':
    main()


# Made with Bob
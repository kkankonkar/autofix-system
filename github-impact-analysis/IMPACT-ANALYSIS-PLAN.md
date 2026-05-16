# Impact Analysis Feature - Implementation Plan

## Overview
Add impact analysis capability to Fixium that uses Neo4j MCP server to analyze the downstream impact of changes described in GitHub issues.

## Feature Trigger
Users comment `Fixium:analyzeimpact` on a GitHub issue to trigger impact analysis.

## Architecture

### High-Level Flow
```
GitHub Issue Comment (Fixium:analyzeimpact)
    ↓
GitHub Actions Workflow (fixium-impact job)
    ↓
fixium/impact_main.py
    ↓
1. Parse issue details (fixium/issue_analyzer.py)
2. Extract affected components
3. Query Neo4j via MCP (fixium/impact_analyzer.py)
    ↓
Bob CLI with Neo4j MCP Server
    ↓
Neo4j Aura Database (code graph)
    ↓
4. Analyze impact results
5. Format impact report
6. Post comment to issue
```

### Components to Create

#### 1. Prompt Template: `prompts/analyze-impact.md`
**Purpose**: Guide Bob AI to perform impact analysis using Neo4j MCP

**Key Sections**:
- Issue context extraction
- Neo4j query strategy
- Impact analysis methodology
- Output format (JSON)

**Neo4j Query Types**:
- Find dependent files/modules
- Find affected functions/classes
- Find downstream API consumers
- Find test coverage gaps
- Find related database schemas

#### 2. Impact Analyzer: `fixium/impact_analyzer.py`
**Purpose**: Core logic for impact analysis

**Key Classes**:
```python
class ImpactAnalyzer:
    """Analyze code impact using Neo4j graph database."""
    
    def __init__(self, github_client, repo_name, neo4j_config)
    def analyze_issue_impact(self, issue_number) -> ImpactAnalysis
    def _build_neo4j_queries(self, affected_components) -> List[str]
    def _execute_mcp_query(self, cypher_query) -> Dict
    def _analyze_dependencies(self, query_results) -> List[Dependency]
    def _calculate_risk_score(self, dependencies) -> float
    def _generate_recommendations(self, analysis) -> List[str]

@dataclass
class ImpactAnalysis:
    issue_number: int
    affected_components: List[str]
    direct_dependencies: List[Dependency]
    indirect_dependencies: List[Dependency]
    affected_tests: List[str]
    risk_score: float  # 0.0 to 1.0
    recommendations: List[str]
    query_results: Dict
```

**Neo4j MCP Integration**:
- Use Bob CLI's `use_mcp_tool` with neo4j server
- Tools available: `get-schema`, `read-cypher`, `write-cypher`
- Query strategy: read-only queries via `read-cypher`

#### 3. Main Entry Point: `fixium/impact_main.py`
**Purpose**: Orchestrate impact analysis workflow

**Flow**:
```python
def main():
    # 1. Get environment variables
    # 2. Validate authorization
    # 3. Post initial comment
    # 4. Analyze issue (extract affected components)
    # 5. Query Neo4j via MCP
    # 6. Analyze impact
    # 7. Format results
    # 8. Post impact report comment
    # 9. Handle errors gracefully
```

#### 4. Comment Parser Update: `fixium/comment_parser.py`
**Changes**:
```python
class FixiumCommand:
    def is_valid(self) -> bool:
        return self.command in ['review', 'updatedocs', 'implementfix', 'analyzeimpact']

class CommentParser:
    # Add parsing for analyzeimpact command
    # No special options needed initially
```

#### 5. Config Update: `fixium/config.py`
**Add Neo4j Configuration**:
```python
class Config:
    def __init__(self):
        # ... existing config ...
        
        # Neo4j configuration (from environment/secrets)
        self.neo4j_uri = os.getenv('NEO4J_URI')
        self.neo4j_username = os.getenv('NEO4J_USERNAME')
        self.neo4j_password = os.getenv('NEO4J_PASSWORD')
        self.neo4j_database = os.getenv('NEO4J_DATABASE', 'neo4j')
    
    def validate_neo4j(self) -> list[str]:
        """Validate Neo4j configuration."""
        errors = []
        if not self.neo4j_uri:
            errors.append("NEO4J_URI is required")
        if not self.neo4j_username:
            errors.append("NEO4J_USERNAME is required")
        if not self.neo4j_password:
            errors.append("NEO4J_PASSWORD is required")
        return errors
```

#### 6. GitHub Actions Workflow: `.github/workflows/fixium.yml`
**Add New Job**:
```yaml
fixium-impact:
  # Only run on issue comments (not PR) that contain "Fixium:analyzeimpact"
  if: |
    !github.event.issue.pull_request &&
    contains(github.event.comment.body, 'Fixium:analyzeimpact')
  
  runs-on: ubuntu-latest
  
  concurrency:
    group: fixium-impact-${{ github.event.issue.number }}
    cancel-in-progress: false
  
  steps:
    - name: Checkout repository
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Install Bob CLI
      run: |
        # TODO: Add actual Bob CLI installation
        echo "Bob CLI installation placeholder"
    
    - name: Configure Bob MCP for Neo4j
      run: |
        mkdir -p ~/.config/bob
        cat > ~/.config/bob/mcp.json << 'EOF'
        {
          "mcpServers": {
            "neo4j": {
              "command": "python3",
              "args": ["-m", "neo4j_mcp_server"],
              "env": {
                "NEO4J_URI": "${{ secrets.NEO4J_URI }}",
                "NEO4J_USERNAME": "${{ secrets.NEO4J_USERNAME }}",
                "NEO4J_PASSWORD": "${{ secrets.NEO4J_PASSWORD }}",
                "NEO4J_DATABASE": "${{ secrets.NEO4J_DATABASE }}"
              }
            }
          }
        }
        EOF
    
    - name: Run Impact Analysis
      run: |
        python -m fixium.impact_main
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        BOBSHELL_API_KEY: ${{ secrets.BOBSHELL_API_KEY }}
        FIXIUM_AUTHORIZED_USERS: ${{ secrets.FIXIUM_AUTHORIZED_USERS }}
        GITHUB_REPOSITORY: ${{ github.repository }}
        GITHUB_OWNER: ${{ github.repository_owner }}
        GITHUB_REPO: ${{ github.event.repository.name }}
        ISSUE_NUMBER: ${{ github.event.issue.number }}
        COMMENT_BODY: ${{ github.event.comment.body }}
        COMMENT_USER: ${{ github.event.comment.user.login }}
        GITHUB_WORKSPACE: ${{ github.workspace }}
        NEO4J_URI: ${{ secrets.NEO4J_URI }}
        NEO4J_USERNAME: ${{ secrets.NEO4J_USERNAME }}
        NEO4J_PASSWORD: ${{ secrets.NEO4J_PASSWORD }}
        NEO4J_DATABASE: ${{ secrets.NEO4J_DATABASE }}
    
    - name: Upload analysis artifacts
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: fixium-impact-${{ github.event.issue.number }}
        path: |
          impact_analysis_issue${{ github.event.issue.number }}.json
        retention-days: 30
        if-no-files-found: ignore
```

## Neo4j Graph Schema Assumptions

Since we don't have the exact schema, we'll design queries to be flexible:

### Expected Node Types
- `File` - Source code files
- `Function` - Functions/methods
- `Class` - Classes/types
- `Module` - Modules/packages
- `API` - API endpoints
- `Test` - Test files/cases

### Expected Relationships
- `DEPENDS_ON` - Dependency relationship
- `CALLS` - Function call relationship
- `IMPORTS` - Import relationship
- `TESTS` - Test coverage relationship
- `IMPLEMENTS` - Implementation relationship

### Sample Queries

**Find Direct Dependencies**:
```cypher
MATCH (source:File {path: $file_path})-[:DEPENDS_ON]->(dep:File)
RETURN dep.path, dep.type
```

**Find Downstream Impact**:
```cypher
MATCH (source:File {path: $file_path})<-[:DEPENDS_ON*1..3]-(dependent:File)
RETURN DISTINCT dependent.path, dependent.type
ORDER BY dependent.path
```

**Find Affected Tests**:
```cypher
MATCH (source:File {path: $file_path})<-[:TESTS]-(test:Test)
RETURN test.path, test.name
```

**Find API Endpoints**:
```cypher
MATCH (source:File {path: $file_path})-[:CONTAINS]->(api:API)
RETURN api.endpoint, api.method
```

## Output Format

### Impact Analysis Comment
```markdown
## 🔍 Impact Analysis Results

**Issue**: #123 - Add payment processing feature

### 📊 Summary
- **Risk Score**: 0.65 (Medium-High)
- **Direct Dependencies**: 5 files
- **Indirect Dependencies**: 12 files
- **Affected Tests**: 8 test files
- **API Endpoints Affected**: 3 endpoints

### 🎯 Affected Components

#### Direct Dependencies
- `src/payment/processor.py` - Payment processing logic
- `src/api/payment_routes.py` - Payment API endpoints
- `src/models/transaction.py` - Transaction data model
- `src/services/notification.py` - Notification service
- `src/utils/validation.py` - Input validation

#### Indirect Dependencies (Downstream Impact)
- `src/api/order_routes.py` - Order management (uses payment)
- `src/services/billing.py` - Billing service
- `src/reports/financial.py` - Financial reporting
- ... (9 more files)

### 🧪 Test Coverage
- `tests/test_payment_processor.py` ⚠️ Needs update
- `tests/test_payment_api.py` ⚠️ Needs update
- `tests/integration/test_checkout.py` ⚠️ May need update
- ... (5 more test files)

### 🌐 API Endpoints Affected
- `POST /api/v1/payments` - Create payment
- `GET /api/v1/payments/{id}` - Get payment status
- `POST /api/v1/payments/{id}/refund` - Process refund

### ⚠️ Recommendations
1. **High Priority**: Update payment processor tests before implementation
2. **Medium Priority**: Review downstream services for compatibility
3. **Medium Priority**: Update API documentation for new endpoints
4. **Low Priority**: Consider adding integration tests for checkout flow

### 📈 Risk Assessment
**Medium-High Risk (0.65/1.0)**

**Factors**:
- ✅ Well-defined requirements
- ⚠️ Multiple downstream dependencies
- ⚠️ Critical payment functionality
- ✅ Existing test coverage
- ⚠️ API changes required

**Mitigation**:
- Implement comprehensive unit tests
- Add integration tests for payment flow
- Perform thorough code review
- Consider feature flag for gradual rollout

---
*🤖 Generated by Fixium Impact Analyzer using Neo4j graph analysis*
```

## Testing Strategy

### Unit Tests: `tests/test_impact_analyzer.py`
```python
def test_analyze_issue_impact()
def test_build_neo4j_queries()
def test_parse_query_results()
def test_calculate_risk_score()
def test_generate_recommendations()
def test_handle_missing_neo4j_data()
def test_handle_neo4j_connection_error()
```

### Integration Tests
- Test with mock Neo4j responses
- Test MCP tool invocation
- Test comment posting

## Documentation Updates

### 1. README.md
Add section:
```markdown
### 🔍 Impact Analysis (`Fixium:analyzeimpact`)
- **Graph-Based Analysis**: Uses Neo4j to analyze code dependencies
- **Risk Assessment**: Calculates impact risk score
- **Comprehensive Coverage**: Identifies affected files, tests, and APIs
- **Actionable Recommendations**: Provides prioritized action items
```

### 2. agents.md
Add section documenting:
- Impact analyzer architecture
- Neo4j MCP integration
- Query strategies
- Output format

### 3. COMMENT-TRIGGER-EXPLAINED.md
Add `Fixium:analyzeimpact` command documentation

### 4. New: NEO4J-SETUP.md
Create guide for:
- Setting up Neo4j Aura instance
- Populating code graph
- Configuring GitHub secrets (reference only, no actual values)
- Testing MCP connection

## GitHub Secrets Configuration

The following secrets must be configured in the GitHub repository settings:

- `NEO4J_URI` - Neo4j connection URI
- `NEO4J_USERNAME` - Neo4j username
- `NEO4J_PASSWORD` - Neo4j password
- `NEO4J_DATABASE` - Neo4j database name (optional, defaults to 'neo4j')

**Note**: Never commit actual credentials to the repository. All sensitive values must be stored as GitHub repository secrets.

## Implementation Order

1. **Phase 1: Core Infrastructure**
   - Create prompt template
   - Update comment parser
   - Update config.py
   - Add workflow job

2. **Phase 2: Impact Analyzer**
   - Implement ImpactAnalyzer class
   - Build Neo4j query logic
   - Implement MCP integration
   - Add risk scoring

3. **Phase 3: Main Entry Point**
   - Create impact_main.py
   - Integrate with GitHub
   - Add error handling
   - Format output

4. **Phase 4: Testing & Documentation**
   - Write unit tests
   - Test with real Neo4j
   - Update documentation
   - Create setup guide

## Success Criteria

- [ ] User can trigger impact analysis with `Fixium:analyzeimpact` comment
- [ ] System queries Neo4j via MCP successfully
- [ ] Impact report posted to issue with all sections
- [ ] Risk score calculated accurately
- [ ] Recommendations are actionable
- [ ] Error handling works gracefully
- [ ] Documentation is complete
- [ ] Tests pass
- [ ] No secrets exposed in code or documentation

## Future Enhancements

1. **Visual Impact Graph**: Generate Mermaid diagram of dependencies
2. **Historical Analysis**: Compare with previous impact analyses
3. **Auto-Labeling**: Automatically add labels based on risk score
4. **Integration with Review**: Link impact analysis to code review
5. **Custom Queries**: Allow users to specify custom Neo4j queries
6. **Impact Prediction**: ML-based prediction of change impact

---

**Status**: Planning Complete  
**Next Step**: Begin Phase 1 implementation  
**Estimated Effort**: 2-3 days
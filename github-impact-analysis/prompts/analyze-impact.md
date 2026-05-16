# GitHub Issue Impact Analysis Using Neo4j

## Objective
Analyze the downstream impact of changes described in a GitHub issue by querying a Neo4j graph database that represents the codebase structure and dependencies.

## Context
You have access to a Neo4j graph database via MCP (Model Context Protocol) that contains:
- Code structure (files, classes, functions, modules)
- Dependencies between components
- Test coverage relationships
- API endpoint definitions
- Database schema relationships

## Analysis Process

### Step 1: Extract Affected Components from Issue

Parse the GitHub issue to identify:
1. **Explicitly Mentioned Files**: Look for file paths in backticks or code blocks
2. **Component Names**: Classes, functions, modules mentioned
3. **Feature Areas**: High-level features or services affected
4. **API Endpoints**: REST endpoints or GraphQL queries mentioned

**Example Extraction**:
```
Issue: "Add payment refund functionality to PaymentProcessor"
Affected Components:
- src/payment/processor.py (PaymentProcessor class)
- POST /api/v1/payments/{id}/refund (new endpoint)
- payment service
```

### Step 2: Query Neo4j Graph Database

Use the Neo4j MCP server to execute Cypher queries. Available MCP tools:
- `get-schema` - Get database schema information
- `read-cypher` - Execute read-only Cypher queries
- `write-cypher` - Execute write queries (avoid unless necessary)

#### Query Strategy

**A. Discover Schema First** (if unknown):
```cypher
CALL db.labels()
CALL db.relationshipTypes()
```

**B. Find Direct Dependencies**:
```cypher
// For a specific file
MATCH (source {path: $file_path})-[r:DEPENDS_ON|IMPORTS|USES]->(dep)
RETURN dep.path, dep.type, type(r) as relationship
LIMIT 50

// For a component/class
MATCH (source {name: $component_name})-[r]->(dep)
WHERE type(r) IN ['DEPENDS_ON', 'CALLS', 'USES', 'IMPORTS']
RETURN dep.name, dep.type, type(r) as relationship
LIMIT 50
```

**C. Find Downstream Impact** (who depends on this):
```cypher
// Files that depend on the changed file
MATCH (source {path: $file_path})<-[r:DEPENDS_ON|IMPORTS|USES*1..3]-(dependent)
RETURN DISTINCT dependent.path, dependent.type, length(r) as depth
ORDER BY depth, dependent.path
LIMIT 100

// Components that call this function/class
MATCH (source {name: $component_name})<-[r:CALLS|USES*1..2]-(caller)
RETURN DISTINCT caller.name, caller.type, caller.path
LIMIT 50
```

**D. Find Test Coverage**:
```cypher
// Tests for the component
MATCH (source {path: $file_path})<-[:TESTS|COVERS]-(test)
RETURN test.path, test.name, test.type
LIMIT 50

// Or find test files
MATCH (source {path: $file_path})<-[:TESTS*1..2]-(test)
WHERE test.path CONTAINS 'test'
RETURN DISTINCT test.path
LIMIT 50
```

**E. Find API Endpoints**:
```cypher
// APIs defined in or using this file
MATCH (source {path: $file_path})-[:DEFINES|CONTAINS]->(api:API)
RETURN api.endpoint, api.method, api.path
LIMIT 50

// Or find route handlers
MATCH (source {path: $file_path})-[:CONTAINS]->(handler)
WHERE handler.type = 'route_handler' OR handler.decorator CONTAINS 'route'
RETURN handler.name, handler.path
LIMIT 50
```

**F. Find Database Schema Impact**:
```cypher
// Database models/tables used
MATCH (source {path: $file_path})-[:USES|ACCESSES]->(model:Model)
RETURN model.name, model.table, model.schema
LIMIT 50
```

#### Adaptive Querying

If the exact schema is unknown, use flexible queries:

```cypher
// Generic dependency query
MATCH (source)-[r]->(target)
WHERE source.path = $file_path OR source.name = $component_name
RETURN target, type(r) as relationship, labels(target) as labels
LIMIT 100

// Generic reverse dependency query
MATCH (source)<-[r]-(dependent)
WHERE source.path = $file_path OR source.name = $component_name
RETURN dependent, type(r) as relationship, labels(dependent) as labels
LIMIT 100
```

### Step 3: Analyze Query Results

For each query result, categorize the impact:

#### Direct Dependencies
Components that the changed code directly uses or imports.

**Risk Factors**:
- Breaking changes to interfaces
- Changed function signatures
- Removed functionality

#### Indirect Dependencies (Downstream Impact)
Components that depend on the changed code (1-3 levels deep).

**Risk Factors**:
- Behavior changes affecting callers
- Performance changes
- Error handling changes

#### Test Coverage
Test files that cover the changed components.

**Assessment**:
- ✅ Good: Multiple test files covering the component
- ⚠️ Moderate: Some test coverage but gaps exist
- ❌ Poor: No test coverage found

#### API Impact
REST endpoints, GraphQL queries, or public APIs affected.

**Risk Factors**:
- Breaking API changes
- New endpoints requiring documentation
- Changed response formats

### Step 4: Calculate Risk Score

Assign a risk score (0.0 to 1.0) based on:

**High Risk Factors** (0.7-1.0):
- Changes to critical payment/auth/security code
- Breaking API changes
- No test coverage
- Many downstream dependencies (>10)
- Database schema changes

**Medium Risk Factors** (0.4-0.6):
- Moderate downstream impact (5-10 dependencies)
- Some test coverage
- Non-breaking API changes
- Well-defined requirements

**Low Risk Factors** (0.0-0.3):
- Isolated changes
- Comprehensive test coverage
- No API changes
- Few dependencies (<5)
- Clear implementation path

**Formula**:
```
risk_score = (
    downstream_count * 0.05 +
    (1.0 if no_tests else 0.0) * 0.3 +
    (1.0 if api_changes else 0.0) * 0.2 +
    (1.0 if critical_component else 0.0) * 0.3 +
    (1.0 if db_changes else 0.0) * 0.15
)
# Clamp to [0.0, 1.0]
```

### Step 5: Generate Recommendations

Based on the analysis, provide actionable recommendations:

**High Priority**:
- Add missing test coverage
- Update API documentation
- Review breaking changes with team
- Add integration tests
- Consider feature flags

**Medium Priority**:
- Update affected downstream components
- Review error handling
- Performance testing
- Security review

**Low Priority**:
- Code cleanup
- Documentation updates
- Refactoring opportunities

## Output Format

Generate a JSON file with the following structure:

```json
{
  "issueNumber": 123,
  "issueTitle": "Add payment refund functionality",
  "affectedComponents": [
    {
      "path": "src/payment/processor.py",
      "type": "file",
      "component": "PaymentProcessor",
      "confidence": "high"
    }
  ],
  "impactAnalysis": {
    "directDependencies": [
      {
        "path": "src/payment/models.py",
        "type": "file",
        "relationship": "IMPORTS",
        "description": "Payment data models"
      }
    ],
    "downstreamImpact": [
      {
        "path": "src/api/payment_routes.py",
        "type": "file",
        "relationship": "USES",
        "depth": 1,
        "description": "Payment API endpoints"
      },
      {
        "path": "src/services/billing.py",
        "type": "file",
        "relationship": "CALLS",
        "depth": 2,
        "description": "Billing service"
      }
    ],
    "testCoverage": [
      {
        "path": "tests/test_payment_processor.py",
        "status": "exists",
        "needsUpdate": true
      },
      {
        "path": "tests/integration/test_payment_flow.py",
        "status": "missing",
        "needsUpdate": false
      }
    ],
    "apiEndpoints": [
      {
        "endpoint": "POST /api/v1/payments/{id}/refund",
        "method": "POST",
        "status": "new",
        "breaking": false
      }
    ],
    "databaseImpact": [
      {
        "table": "payments",
        "operation": "read/write",
        "schemaChange": false
      }
    ]
  },
  "riskAssessment": {
    "score": 0.65,
    "level": "medium-high",
    "factors": [
      {
        "factor": "Multiple downstream dependencies",
        "impact": "high",
        "weight": 0.25
      },
      {
        "factor": "Critical payment functionality",
        "impact": "high",
        "weight": 0.30
      },
      {
        "factor": "Existing test coverage",
        "impact": "positive",
        "weight": -0.15
      }
    ]
  },
  "recommendations": [
    {
      "priority": "high",
      "category": "testing",
      "action": "Add integration tests for refund flow",
      "rationale": "New functionality requires comprehensive testing"
    },
    {
      "priority": "high",
      "category": "documentation",
      "action": "Document new refund API endpoint",
      "rationale": "New public API requires documentation"
    },
    {
      "priority": "medium",
      "category": "review",
      "action": "Review downstream services for compatibility",
      "rationale": "Multiple services depend on PaymentProcessor"
    }
  ],
  "summary": {
    "totalDirectDependencies": 3,
    "totalDownstreamImpact": 8,
    "testCoverageStatus": "partial",
    "apiChanges": 1,
    "databaseChanges": 0,
    "estimatedEffort": "medium",
    "recommendedApproach": "Implement with feature flag, comprehensive testing, and staged rollout"
  },
  "neo4jQueries": [
    {
      "purpose": "Find direct dependencies",
      "query": "MATCH (source {path: 'src/payment/processor.py'})-[r:DEPENDS_ON|IMPORTS]->(dep) RETURN dep",
      "resultCount": 3
    }
  ]
}
```

## Error Handling

If Neo4j queries fail or return no results:

1. **Schema Unknown**: Use `get-schema` to discover available node types and relationships
2. **No Results**: Try broader queries or different relationship types
3. **Connection Error**: Report error and provide manual analysis based on issue content
4. **Partial Results**: Proceed with available data and note limitations

## Best Practices

1. **Start Broad**: Begin with schema discovery if structure is unknown
2. **Iterate Queries**: Refine queries based on initial results
3. **Limit Results**: Use LIMIT to avoid overwhelming responses
4. **Multiple Queries**: Run several targeted queries rather than one complex query
5. **Document Queries**: Include executed queries in output for transparency
6. **Graceful Degradation**: Provide useful analysis even with limited graph data

## Example Workflow

```
1. Parse issue → Extract "src/payment/processor.py"
2. Query Neo4j → Find 3 direct dependencies
3. Query Neo4j → Find 8 downstream dependents
4. Query Neo4j → Find 2 test files
5. Query Neo4j → Find 1 API endpoint
6. Calculate risk → 0.65 (medium-high)
7. Generate recommendations → 5 actionable items
8. Format output → Post to GitHub issue
```

---

**Generated by Fixium Impact Analyzer**
# Neo4j Setup Guide for Fixium Impact Analysis

This guide explains how to set up Neo4j for Fixium's impact analysis feature.

## Overview

Fixium's impact analysis uses Neo4j graph database to analyze code dependencies and relationships. The system queries Neo4j via the Model Context Protocol (MCP) to understand the downstream impact of code changes.

## Prerequisites

- Neo4j Aura account (free tier available)
- GitHub repository with admin access
- Bob CLI with MCP support
- Code graph data populated in Neo4j

## Step 1: Create Neo4j Aura Instance

1. Go to [Neo4j Aura](https://console.neo4j.io)
2. Sign up or log in
3. Click "Create Instance"
4. Select "Free" tier
5. Choose a region close to your GitHub Actions runners
6. Wait for instance to be created (60 seconds)
7. **Save the credentials** - they are shown only once!

You will receive:
- `NEO4J_URI` - Connection URI (e.g., `neo4j+s://xxxxx.databases.neo4j.io`)
- `NEO4J_USERNAME` - Username (usually the instance ID)
- `NEO4J_PASSWORD` - Auto-generated password
- `NEO4J_DATABASE` - Database name (usually same as username)

## Step 2: Populate Code Graph

You need to populate your Neo4j database with your codebase structure. There are several approaches:

### Option A: Use jQAssistant (Recommended for Java/JVM)

```bash
# Install jQAssistant
wget https://jqassistant.org/get/cli/latest

# Scan your codebase
./jqassistant.sh scan -f .

# Export to Neo4j
./jqassistant.sh analyze -storeUri bolt://your-neo4j-uri
```

### Option B: Use Code2Graph (Python/JavaScript)

```bash
# Install code2graph
pip install code2graph

# Generate graph
code2graph analyze ./src --output neo4j --uri $NEO4J_URI
```

### Option C: Custom Script

Create a custom script to parse your codebase and create nodes/relationships:

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(uri, auth=(username, password))

with driver.session() as session:
    # Create file nodes
    session.run("""
        CREATE (f:File {
            path: $path,
            type: $type,
            language: $language
        })
    """, path="src/payment/processor.py", type="file", language="python")
    
    # Create dependency relationships
    session.run("""
        MATCH (source:File {path: $source_path})
        MATCH (target:File {path: $target_path})
        CREATE (source)-[:DEPENDS_ON]->(target)
    """, source_path="src/api/routes.py", target_path="src/payment/processor.py")
```

### Expected Graph Schema

Your Neo4j database should contain:

**Node Types:**
- `File` - Source code files
  - Properties: `path`, `type`, `language`
- `Function` - Functions/methods
  - Properties: `name`, `signature`, `file`
- `Class` - Classes/types
  - Properties: `name`, `file`
- `Module` - Modules/packages
  - Properties: `name`, `path`
- `API` - API endpoints (optional)
  - Properties: `endpoint`, `method`, `handler`
- `Test` - Test files (optional)
  - Properties: `path`, `name`

**Relationship Types:**
- `DEPENDS_ON` - Dependency between files/modules
- `IMPORTS` - Import relationship
- `CALLS` - Function call relationship
- `USES` - General usage relationship
- `TESTS` - Test coverage relationship
- `CONTAINS` - Containment (file contains class/function)

## Step 3: Configure GitHub Secrets

Add the following secrets to your GitHub repository:

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `NEO4J_URI` | Neo4j connection URI | `neo4j+s://xxxxxxx.databases.neo4j.io` |
| `NEO4J_USERNAME` | Neo4j username | `neo4j` or instance ID |
| `NEO4J_PASSWORD` | Neo4j password | Auto-generated password |
| `NEO4J_DATABASE` | Database name | `neo4j` or instance ID |

**⚠️ Security Notes:**
- Never commit credentials to your repository
- Use GitHub Secrets for all sensitive values
- Rotate passwords regularly
- Use read-only credentials if possible

## Step 4: Test Connection

Test your Neo4j connection locally before using in GitHub Actions:

```bash
# Set environment variables
export NEO4J_URI="neo4j+s://xxxxx.databases.neo4j.io"
export NEO4J_USERNAME="your-username"
export NEO4J_PASSWORD="your-password"
export NEO4J_DATABASE="neo4j"

# Test with cypher-shell
cypher-shell -a $NEO4J_URI -u $NEO4J_USERNAME -p $NEO4J_PASSWORD

# Run a test query
MATCH (n) RETURN count(n) as node_count;
```

## Step 5: Configure Bob CLI MCP

The GitHub Actions workflow automatically configures Bob CLI to use Neo4j MCP. The configuration is created in `~/.config/bob/mcp.json`:

```json
{
  "mcpServers": {
    "neo4j": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-neo4j"],
      "env": {
        "NEO4J_URI": "from-github-secrets",
        "NEO4J_USERNAME": "from-github-secrets",
        "NEO4J_PASSWORD": "from-github-secrets",
        "NEO4J_DATABASE": "from-github-secrets"
      }
    }
  }
}
```

## Step 6: Verify Setup

1. Create a test issue in your repository
2. Add comment: `Fixium:analyzeimpact`
3. Check GitHub Actions logs for:
   - ✅ Neo4j connection successful
   - ✅ MCP server initialized
   - ✅ Queries executed
   - ✅ Impact analysis posted

## Troubleshooting

### Connection Errors

**Problem**: `Unable to connect to Neo4j`

**Solutions**:
- Verify URI format includes `neo4j+s://` prefix
- Check firewall/network settings
- Ensure instance is running (not paused)
- Verify credentials are correct

### Empty Results

**Problem**: Impact analysis returns no dependencies

**Solutions**:
- Verify graph data is populated
- Check node/relationship types match expected schema
- Run test queries manually to verify data
- Review Cypher queries in analysis output

### MCP Server Errors

**Problem**: `MCP server failed to start`

**Solutions**:
- Ensure Node.js is available in GitHub Actions
- Check MCP server package is accessible
- Verify environment variables are set
- Review GitHub Actions logs for details

### Authentication Failures

**Problem**: `Authentication failed`

**Solutions**:
- Verify secrets are set correctly in GitHub
- Check for typos in secret names
- Ensure password hasn't expired
- Try regenerating credentials in Neo4j Aura

## Sample Queries

Here are some useful queries to test your graph:

### Count Nodes by Type
```cypher
MATCH (n)
RETURN labels(n) as type, count(n) as count
ORDER BY count DESC
```

### Find Files with Most Dependencies
```cypher
MATCH (f:File)-[:DEPENDS_ON]->(dep)
RETURN f.path, count(dep) as dependency_count
ORDER BY dependency_count DESC
LIMIT 10
```

### Find Files with Most Dependents
```cypher
MATCH (f:File)<-[:DEPENDS_ON]-(dependent)
RETURN f.path, count(dependent) as dependent_count
ORDER BY dependent_count DESC
LIMIT 10
```

### Find Test Coverage
```cypher
MATCH (f:File)<-[:TESTS]-(test:Test)
RETURN f.path, collect(test.path) as tests
```

## Best Practices

1. **Keep Graph Updated**: Regularly update your code graph as the codebase changes
2. **Index Key Properties**: Create indexes on frequently queried properties
3. **Monitor Query Performance**: Review slow queries and optimize
4. **Backup Regularly**: Export graph data periodically
5. **Document Schema**: Maintain documentation of your graph schema
6. **Test Locally First**: Verify queries work before deploying to CI/CD

## Advanced Configuration

### Custom Relationship Types

Add custom relationships for your specific needs:

```cypher
// Add API endpoint relationships
MATCH (f:File {path: 'src/api/routes.py'})
CREATE (api:API {endpoint: '/api/payment', method: 'POST'})
CREATE (f)-[:DEFINES]->(api)
```

### Performance Optimization

Create indexes for better query performance:

```cypher
CREATE INDEX file_path FOR (f:File) ON (f.path)
CREATE INDEX function_name FOR (fn:Function) ON (fn.name)
```

### Graph Maintenance

Regularly clean up and update your graph:

```cypher
// Remove orphaned nodes
MATCH (n)
WHERE NOT (n)--()
DELETE n

// Update file metadata
MATCH (f:File {path: 'old/path.py'})
SET f.path = 'new/path.py'
```

## Resources

- [Neo4j Aura Documentation](https://neo4j.com/docs/aura/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Bob CLI Documentation](https://ibm.github.io/bob/)
- [jQAssistant](https://jqassistant.org/)

## Support

For issues or questions:
1. Check GitHub Actions logs
2. Review Neo4j Aura console
3. Test queries manually
4. Check this documentation
5. Open an issue in the repository

---

**Last Updated**: 2026-05-13  
**Version**: 1.0.0
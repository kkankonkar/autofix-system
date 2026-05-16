# Bob CLI MCP Configuration for Neo4j

This document explains how Bob CLI is configured to use the Neo4j MCP (Model Context Protocol) server for impact analysis.

## Overview

The impact analysis feature uses Bob CLI to query Neo4j graph database via the Model Context Protocol (MCP). This requires:

1. **Neo4j MCP Server** - NPM package that provides Neo4j access via MCP
2. **Bob CLI Configuration** - JSON config file telling Bob how to connect to MCP servers
3. **Environment Variables** - Neo4j credentials passed securely

## Architecture

```
GitHub Actions Workflow
    ↓
Environment Variables (Secrets)
    ↓
configure_bob_mcp.sh Script
    ↓
~/.config/bob/mcp.json
    ↓
Bob CLI
    ↓
Neo4j MCP Server (npx @modelcontextprotocol/server-neo4j)
    ↓
Neo4j Aura Database
```

## Components

### 1. Neo4j MCP Server

**Package**: `@modelcontextprotocol/server-neo4j`

**Installation**:
```bash
# In Dockerfile
npm install -g @modelcontextprotocol/server-neo4j

# Or in GitHub Actions
npm install -g @modelcontextprotocol/server-neo4j
```

**Purpose**: Provides MCP interface to Neo4j database

**Tools Provided**:
- `get-schema` - Get database schema
- `read-cypher` - Execute read-only Cypher queries
- `write-cypher` - Execute write Cypher queries

### 2. Bob CLI Configuration File

**Location**: `~/.config/bob/mcp.json`

**Format**:
```json
{
  "mcpServers": {
    "neo4j": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-neo4j"],
      "env": {
        "NEO4J_URI": "neo4j+s://xxxxx.databases.neo4j.io",
        "NEO4J_USERNAME": "username",
        "NEO4J_PASSWORD": "password",
        "NEO4J_DATABASE": "neo4j"
      }
    }
  }
}
```

**Fields**:
- `mcpServers` - Object containing MCP server configurations
- `neo4j` - Server name (can be any identifier)
- `command` - Command to run the MCP server (`npx`)
- `args` - Arguments to pass to command
- `env` - Environment variables for the MCP server

### 3. Configuration Script

**File**: `scripts/configure_bob_mcp.sh`

**Purpose**: Creates Bob MCP configuration at runtime with secrets

**Key Features**:
- Creates `~/.config/bob/` directory
- Generates `mcp.json` with environment variables
- Validates Neo4j credentials are present
- Checks MCP server availability
- Provides fallback if credentials missing

**Usage**:
```bash
# Set environment variables
export NEO4J_URI="neo4j+s://xxxxx.databases.neo4j.io"
export NEO4J_USERNAME="username"
export NEO4J_PASSWORD="password"
export NEO4J_DATABASE="neo4j"

# Run configuration script
bash scripts/configure_bob_mcp.sh
```

## Workflow Integration

### Docker-Based Execution (mobile-usage-platform)

```yaml
- name: Run Fixium Impact Analysis (Docker)
  run: |
    docker run --rm \
      --entrypoint /bin/bash \
      -v ${{ github.workspace }}:/workspace \
      -w /workspace \
      -e NEO4J_URI="${{ secrets.NEO4J_URI }}" \
      -e NEO4J_USERNAME="${{ secrets.NEO4J_USERNAME }}" \
      -e NEO4J_PASSWORD="${{ secrets.NEO4J_PASSWORD }}" \
      -e NEO4J_DATABASE="${{ secrets.NEO4J_DATABASE }}" \
      ghcr.io/hpai1990/fixium:latest \
      -c "/fixium/scripts/configure_bob_mcp.sh && python -m fixium.impact_main"
```

**Flow**:
1. Docker container starts with bash entrypoint
2. Environment variables passed from GitHub Secrets
3. Configuration script runs first
4. Creates `~/.config/bob/mcp.json` inside container
5. Python script executes impact analysis
6. Bob CLI reads MCP config and connects to Neo4j

### Direct Execution (code-review-workflow)

```yaml
- name: Install Neo4j MCP Server
  run: npm install -g @modelcontextprotocol/server-neo4j

- name: Configure Bob MCP for Neo4j
  run: bash scripts/configure_bob_mcp.sh
  env:
    NEO4J_URI: ${{ secrets.NEO4J_URI }}
    NEO4J_USERNAME: ${{ secrets.NEO4J_USERNAME }}
    NEO4J_PASSWORD: ${{ secrets.NEO4J_PASSWORD }}
    NEO4J_DATABASE: ${{ secrets.NEO4J_DATABASE }}

- name: Run Impact Analysis
  run: python -m fixium.impact_main
  env:
    # ... other env vars ...
    NEO4J_URI: ${{ secrets.NEO4J_URI }}
    NEO4J_USERNAME: ${{ secrets.NEO4J_USERNAME }}
    NEO4J_PASSWORD: ${{ secrets.NEO4J_PASSWORD }}
    NEO4J_DATABASE: ${{ secrets.NEO4J_DATABASE }}
```

**Flow**:
1. Install MCP server globally
2. Run configuration script with secrets
3. Script creates `~/.config/bob/mcp.json`
4. Python script executes with Neo4j env vars
5. Bob CLI uses MCP config to query Neo4j

## How Bob CLI Uses MCP

When Bob CLI encounters a prompt that requires Neo4j data:

1. **Reads MCP Config**: Bob reads `~/.config/bob/mcp.json`
2. **Starts MCP Server**: Executes `npx -y @modelcontextprotocol/server-neo4j`
3. **Passes Environment**: Neo4j credentials from `env` section
4. **Establishes Connection**: MCP server connects to Neo4j
5. **Executes Tools**: Bob can call `read-cypher`, `get-schema`, etc.
6. **Returns Results**: MCP server returns query results to Bob
7. **Processes Data**: Bob analyzes results and generates response

## Security Considerations

### ✅ Secure Practices

1. **GitHub Secrets**: All credentials stored as repository secrets
2. **Environment Variables**: Passed at runtime, never committed
3. **Temporary Config**: MCP config created at runtime, not persisted
4. **Docker Isolation**: Container-based execution isolates credentials
5. **No Logging**: Credentials not logged in workflow output

### ❌ Avoid These

1. **Hardcoding**: Never hardcode credentials in config files
2. **Committing Secrets**: Never commit `mcp.json` with real credentials
3. **Logging Secrets**: Don't echo or print credential values
4. **Public Repos**: Be extra careful with public repositories

## Troubleshooting

### MCP Server Not Found

**Error**: `Command not found: npx`

**Solution**:
```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Verify
node --version
npm --version
```

### MCP Server Package Not Available

**Error**: `Package @modelcontextprotocol/server-neo4j not found`

**Solution**:
```bash
# Install globally
npm install -g @modelcontextprotocol/server-neo4j

# Or use npx with -y flag (auto-install)
npx -y @modelcontextprotocol/server-neo4j --version
```

### Neo4j Connection Failed

**Error**: `Unable to connect to Neo4j`

**Check**:
1. Verify secrets are set in GitHub repository
2. Check Neo4j instance is running (not paused)
3. Verify URI format: `neo4j+s://xxxxx.databases.neo4j.io`
4. Test credentials manually with cypher-shell

### Bob CLI Can't Find MCP Config

**Error**: `MCP server 'neo4j' not configured`

**Check**:
1. Verify `~/.config/bob/mcp.json` exists
2. Check file permissions (should be readable)
3. Verify JSON syntax is valid
4. Ensure configuration script ran successfully

### Environment Variables Not Passed

**Error**: `NEO4J_URI is required`

**Check**:
1. Secrets are set in GitHub repository settings
2. Environment variables passed to Docker container
3. Variable names match exactly (case-sensitive)
4. No typos in secret names

## Testing MCP Configuration

### Test Locally

```bash
# Set environment variables
export NEO4J_URI="your-uri"
export NEO4J_USERNAME="your-username"
export NEO4J_PASSWORD="your-password"
export NEO4J_DATABASE="neo4j"

# Run configuration script
bash scripts/configure_bob_mcp.sh

# Verify config file
cat ~/.config/bob/mcp.json

# Test MCP server
npx -y @modelcontextprotocol/server-neo4j --version
```

### Test in Docker

```bash
# Build image
docker build -t fixium:test .

# Run with environment variables
docker run --rm \
  -e NEO4J_URI="your-uri" \
  -e NEO4J_USERNAME="your-username" \
  -e NEO4J_PASSWORD="your-password" \
  --entrypoint /bin/bash \
  fixium:test \
  -c "/fixium/scripts/configure_bob_mcp.sh && cat ~/.config/bob/mcp.json"
```

## Example MCP Query

When Bob CLI executes impact analysis, it might run queries like:

```cypher
// Find direct dependencies
MATCH (source:File {path: 'src/payment/processor.py'})-[:DEPENDS_ON]->(dep:File)
RETURN dep.path, dep.type

// Find downstream impact
MATCH (source:File {path: 'src/payment/processor.py'})<-[:DEPENDS_ON*1..3]-(dependent:File)
RETURN DISTINCT dependent.path, dependent.type
```

Bob CLI sends these via MCP:
```json
{
  "tool": "read-cypher",
  "arguments": {
    "query": "MATCH (source:File {path: $path})-[:DEPENDS_ON]->(dep:File) RETURN dep.path, dep.type",
    "parameters": {
      "path": "src/payment/processor.py"
    }
  }
}
```

## References

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Neo4j MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/neo4j)
- [Bob CLI Documentation](https://ibm.github.io/bob/)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)

---

**Last Updated**: 2026-05-13  
**Version**: 1.0.0
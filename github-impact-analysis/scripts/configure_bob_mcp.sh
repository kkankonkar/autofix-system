#!/bin/bash
# Configure Bob CLI MCP for Neo4j at runtime
# This script creates the MCP configuration file with environment variables

set -e

echo "🔧 Configuring Bob CLI MCP for Neo4j..."

# Create Bob config directory
mkdir -p ~/.config/bob

# Check if Neo4j credentials are provided
if [ -z "$NEO4J_URI" ] || [ -z "$NEO4J_USERNAME" ] || [ -z "$NEO4J_PASSWORD" ]; then
    echo "⚠️  Warning: Neo4j credentials not fully configured"
    echo "   Impact analysis will use fallback mode"
    echo "   Required: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD"
    exit 0
fi

# Create MCP configuration file
cat > ~/.config/bob/mcp.json << EOF
{
  "mcpServers": {
    "neo4j": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-neo4j"],
      "env": {
        "NEO4J_URI": "${NEO4J_URI}",
        "NEO4J_USERNAME": "${NEO4J_USERNAME}",
        "NEO4J_PASSWORD": "${NEO4J_PASSWORD}",
        "NEO4J_DATABASE": "${NEO4J_DATABASE:-neo4j}"
      }
    }
  }
}
EOF

echo "✅ Bob MCP configuration created at ~/.config/bob/mcp.json"
echo "   Neo4j URI: ${NEO4J_URI}"
echo "   Neo4j Database: ${NEO4J_DATABASE:-neo4j}"

# Verify MCP server is available
if command -v npx &> /dev/null; then
    echo "✅ npx is available"
else
    echo "❌ Error: npx not found"
    exit 1
fi

# Note: Neo4j MCP server will be auto-installed by npx on first use
# The -y flag in the MCP config tells npx to auto-install if needed
echo "ℹ️  Neo4j MCP server will be installed on-demand via npx"
echo "🎉 Bob MCP configuration complete!"

# Made with Bob

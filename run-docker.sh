#!/bin/bash

# CodeMedic AutoFix System - Docker Run Script
# Quick start script for running with Docker

set -e

echo "🏥 CodeMedic AutoFix System - Docker Deployment"
echo "================================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo ""
    echo "Please create .env file from template:"
    echo "  cp .env.example .env"
    echo ""
    echo "Then edit .env and add your API keys:"
    echo "  - GITHUB_TOKEN"
    echo "  - BOBSHELL_API_KEY"
    echo "  - OPENAI_API_KEY (optional)"
    echo ""
    exit 1
fi

# Source environment variables
echo "📋 Loading environment variables from .env..."
set -a
source .env
set +a

# Check required variables
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Error: GITHUB_TOKEN not set in .env file"
    exit 1
fi

if [ -z "$BOBSHELL_API_KEY" ]; then
    echo "⚠️  Warning: BOBSHELL_API_KEY not set. Bob CLI will not work."
    echo "   Set it in .env file or use OpenAI as primary agent."
fi

echo "✅ Environment variables loaded"
echo ""

# Create logs directory if it doesn't exist
echo "📁 Creating logs directory..."
mkdir -p logs
echo "✅ Logs directory ready"
echo ""

# Build image for current platform
echo "🔨 Building Docker image..."
PLATFORM=$(uname -m)
if [ "$PLATFORM" = "arm64" ] || [ "$PLATFORM" = "aarch64" ]; then
    echo "   Detected ARM64 platform, building for linux/arm64..."
    docker build --platform linux/arm64 -t codemedic/autofix-system:latest .
else
    echo "   Building for linux/amd64..."
    docker build --platform linux/amd64 -t codemedic/autofix-system:latest .
fi
echo "✅ Image built successfully"
echo ""

# Stop and remove existing container
echo "🧹 Cleaning up existing container..."
docker stop autofix-system 2>/dev/null || true
docker rm autofix-system 2>/dev/null || true
echo "✅ Cleanup complete"
echo ""

# Run container
echo "🚀 Starting CodeMedic AutoFix System..."
docker run -d \
  --name autofix-system \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/logs:/app/logs" \
  --restart unless-stopped \
  codemedic/autofix-system:latest

echo "✅ Container started successfully!"
echo ""
echo "📊 Container Status:"
docker ps --filter name=autofix-system --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "🌐 API Endpoints:"
echo "  - Health Check: http://localhost:8000/health"
echo "  - API Docs:     http://localhost:8000/docs"
echo "  - OpenAPI:      http://localhost:8000/openapi.json"
echo ""
echo "📝 Useful Commands:"
echo "  - View logs:    docker logs -f autofix-system"
echo "  - Stop:         docker stop autofix-system"
echo "  - Restart:      docker restart autofix-system"
echo "  - Remove:       docker rm -f autofix-system"
echo ""
echo "🎉 CodeMedic AutoFix System is ready!"

# Made with ❤️ by CodeMedic Team

# Made with Bob

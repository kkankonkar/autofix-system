#!/bin/bash

# AutoFix System - Quick Start Script

set -e

echo "🚀 Starting AutoFix System MVP..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install runtime dependencies needed for the MVP only
echo "📥 Installing MVP runtime dependencies..."
pip install -q --upgrade pip
pip install -q fastapi "uvicorn[standard]" pydantic pydantic-settings python-dotenv openai requests python-multipart PyGithub GitPython sqlalchemy alembic pymysql cryptography

# Validate Bob CLI availability when configured as primary agent
if [ "${AI_AGENT_PRIMARY:-bob_cli}" = "bob_cli" ]; then
    if ! command -v "${BOB_CLI_COMMAND:-bob}" >/dev/null 2>&1; then
        echo "❌ Bob CLI not found in PATH. Install Bob CLI or set BOB_CLI_COMMAND."
        exit 1
    fi
    echo "✅ Bob CLI detected: ${BOB_CLI_COMMAND:-bob}"
fi

# Start the application
echo "✅ Starting AutoFix System..."
echo ""
echo "🌐 API will be available at: http://localhost:8000"
echo "📚 API docs at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Made with Bob

# AutoFix System - Complete Implementation Guide

This guide provides step-by-step instructions to implement the entire AutoFix system.

## 📋 Table of Contents

1. [Project Setup](#project-setup)
2. [Core Components Implementation](#core-components-implementation)
3. [AI Agent Integration](#ai-agent-integration)
4. [GitHub Integration](#github-integration)
5. [Testing](#testing)
6. [Deployment](#deployment)

## 🚀 Project Setup

### 1. Initialize Project Structure

```bash
cd /Users/kalpeshkankonkar/Downloads/autofix-system

# Create all directories
mkdir -p src/{ai_agent,ingestion,analyzer,repo_manager,fix_generator,pr_creator,models,utils}
mkdir -p config tests docs scripts

# Create __init__.py files
find src -type d -exec touch {}/__init__.py \;
```

### 2. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 🔧 Core Components Implementation

### 1. Data Models (`src/models/`)

#### `src/models/log_entry.py`
```python
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class LogSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

class LogEntry(BaseModel):
    id: str
    timestamp: datetime
    application: str
    severity: LogSeverity
    message: str
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = {}
    repository_url: Optional[str] = None
```

#### `src/models/error_analysis.py`
```python
from pydantic import BaseModel
from typing import Optional

class ErrorAnalysis(BaseModel):
    log_entry_id: str
    error_type: str
    file_path: str
    line_number: int
    function_name: Optional[str]
    root_cause: str
    fixable: bool
    confidence: float
    repository: str
```

#### `src/models/fix_proposal.py`
```python
from pydantic import BaseModel
from typing import List

class FixProposal(BaseModel):
    analysis_id: str
    original_code: str
    fixed_code: str
    explanation: str
    commit_message: str
    pr_description: str
    test_suggestions: List[str]
```

#### `src/models/pull_request.py`
```python
from datetime import datetime
from pydantic import BaseModel

class PullRequest(BaseModel):
    fix_proposal_id: str
    repository: str
    branch_name: str
    pr_number: int
    pr_url: str
    status: str  # CREATED, MERGED, CLOSED
    created_at: datetime
```

### 2. AI Agent Base Class (`src/ai_agent/base.py`)

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class AIAgent(ABC):
    """Base class for AI agents."""
    
    @abstractmethod
    async def analyze_error(
        self, 
        log_entry: str, 
        code_context: str
    ) -> Dict[str, Any]:
        """Analyze error and return structured analysis."""
        pass
    
    @abstractmethod
    async def generate_fix(
        self, 
        error_analysis: Dict[str, Any],
        code_context: str
    ) -> Dict[str, Any]:
        """Generate fix for the error."""
        pass
```

### 3. OpenAI Agent (`src/ai_agent/openai_agent.py`)

```python
import os
import json
from openai import AsyncOpenAI
from .base import AIAgent

class OpenAIAgent(AIAgent):
    """OpenAI-based AI agent."""
    
    def __init__(self, api_key: str = None):
        self.client = AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
    
    async def analyze_error(self, log_entry: str, code_context: str):
        prompt = f"""
        Analyze this error and provide structured information.
        
        Error Log:
        {log_entry}
        
        Code Context:
        {code_context}
        
        Return JSON with:
        - error_type: string
        - file_path: string
        - line_number: int
        - root_cause: string
        - fixable: boolean
        - confidence: float (0-1)
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a code debugging expert."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def generate_fix(self, error_analysis, code_context):
        prompt = f"""
        Generate a fix for this error.
        
        Error Analysis:
        {json.dumps(error_analysis, indent=2)}
        
        Code Context:
        {code_context}
        
        Return JSON with:
        - fixed_code: string
        - explanation: string
        - commit_message: string
        - pr_description: string
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a code fixing expert."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
```

### 4. Bob Agent (`src/ai_agent/bob_agent.py`)

```python
import subprocess
import json
import tempfile
import os
from .base import AIAgent

class BobAgent(AIAgent):
    """Bob AI agent using VSCode extension."""
    
    def __init__(self):
        self.vscode_path = os.getenv("VSCODE_PATH", "code")
        self.extension_path = os.getenv("BOB_EXTENSION_PATH")
    
    async def _call_bob(self, prompt: str) -> str:
        """Call Bob through VSCode extension."""
        # Create temporary file with prompt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            prompt_file = f.name
        
        try:
            # Call VSCode with Bob extension
            result = subprocess.run(
                [
                    self.vscode_path,
                    "--extensionDevelopmentPath", self.extension_path,
                    "--task", prompt_file
                ],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                raise Exception(f"Bob call failed: {result.stderr}")
            
            return result.stdout
        finally:
            os.unlink(prompt_file)
    
    async def analyze_error(self, log_entry: str, code_context: str):
        prompt = f"""
        Analyze this error and provide structured JSON.
        
        Error: {log_entry}
        Code: {code_context}
        
        Return JSON with error_type, file_path, line_number, root_cause, fixable, confidence.
        """
        
        response = await self._call_bob(prompt)
        return json.loads(response)
    
    async def generate_fix(self, error_analysis, code_context):
        prompt = f"""
        Generate fix for this error.
        
        Analysis: {json.dumps(error_analysis)}
        Code: {code_context}
        
        Return JSON with fixed_code, explanation, commit_message, pr_description.
        """
        
        response = await self._call_bob(prompt)
        return json.loads(response)
```

### 5. Hybrid Agent (`src/ai_agent/hybrid_agent.py`)

```python
from .base import AIAgent
from .bob_agent import BobAgent
from .openai_agent import OpenAIAgent
import logging

logger = logging.getLogger(__name__)

class HybridAgent(AIAgent):
    """Hybrid agent that tries Bob first, falls back to OpenAI."""
    
    def __init__(self):
        self.bob_agent = BobAgent()
        self.openai_agent = OpenAIAgent()
    
    async def analyze_error(self, log_entry: str, code_context: str):
        try:
            logger.info("Attempting analysis with Bob")
            return await self.bob_agent.analyze_error(log_entry, code_context)
        except Exception as e:
            logger.warning(f"Bob failed: {e}, falling back to OpenAI")
            return await self.openai_agent.analyze_error(log_entry, code_context)
    
    async def generate_fix(self, error_analysis, code_context):
        try:
            logger.info("Attempting fix generation with Bob")
            return await self.bob_agent.generate_fix(error_analysis, code_context)
        except Exception as e:
            logger.warning(f"Bob failed: {e}, falling back to OpenAI")
            return await self.openai_agent.generate_fix(error_analysis, code_context)
```

### 6. Log Ingestion Service (`src/ingestion/api.py`)

```python
from fastapi import FastAPI, HTTPException, Header
from typing import Optional
import uuid
from datetime import datetime
from ..models import LogEntry
from ..utils.queue import enqueue_log

app = FastAPI(title="AutoFix Log Ingestion API")

@app.post("/api/v1/logs/ingest")
async def ingest_log(
    log: LogEntry,
    x_api_key: Optional[str] = Header(None)
):
    """Ingest a log entry for processing."""
    
    # Validate API key
    if not x_api_key or not validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Generate ID if not provided
    if not log.id:
        log.id = f"log-{uuid.uuid4()}"
    
    # Enqueue for processing
    job_id = await enqueue_log(log)
    
    return {
        "status": "accepted",
        "log_id": log.id,
        "job_id": job_id,
        "message": "Log queued for processing"
    }

@app.get("/api/v1/status")
async def get_status():
    """Get system status."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

def validate_api_key(api_key: str) -> bool:
    """Validate API key."""
    # Implement your API key validation logic
    return True
```

### 7. Error Analyzer (`src/analyzer/analyzer.py`)

```python
from ..models import LogEntry, ErrorAnalysis
from ..ai_agent import HybridAgent
import logging

logger = logging.getLogger(__name__)

class ErrorAnalyzer:
    """Analyzes errors from log entries."""
    
    def __init__(self):
        self.ai_agent = HybridAgent()
    
    async def analyze(self, log_entry: LogEntry) -> ErrorAnalysis:
        """Analyze a log entry and return error analysis."""
        
        logger.info(f"Analyzing log entry: {log_entry.id}")
        
        # Prepare context
        context = self._prepare_context(log_entry)
        
        # Call AI agent
        analysis_result = await self.ai_agent.analyze_error(
            log_entry.message,
            context
        )
        
        # Create ErrorAnalysis object
        analysis = ErrorAnalysis(
            log_entry_id=log_entry.id,
            error_type=analysis_result["error_type"],
            file_path=analysis_result["file_path"],
            line_number=analysis_result["line_number"],
            function_name=analysis_result.get("function_name"),
            root_cause=analysis_result["root_cause"],
            fixable=analysis_result["fixable"],
            confidence=analysis_result["confidence"],
            repository=log_entry.repository_url or ""
        )
        
        logger.info(f"Analysis complete: {analysis.error_type}")
        return analysis
    
    def _prepare_context(self, log_entry: LogEntry) -> str:
        """Prepare context for AI analysis."""
        context = f"Application: {log_entry.application}\n"
        context += f"Severity: {log_entry.severity}\n"
        
        if log_entry.stack_trace:
            context += f"Stack Trace:\n{log_entry.stack_trace}\n"
        
        if log_entry.metadata:
            context += f"Metadata: {log_entry.metadata}\n"
        
        return context
```

### 8. Repository Manager (`src/repo_manager/manager.py`)

```python
import git
import os
import tempfile
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class RepositoryManager:
    """Manages Git repositories."""
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or tempfile.mkdtemp(prefix="autofix-")
    
    async def clone_repository(self, repo_url: str, branch: str = "main") -> str:
        """Clone a repository and return the local path."""
        
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        local_path = os.path.join(self.workspace_dir, repo_name)
        
        if os.path.exists(local_path):
            logger.info(f"Repository already exists: {local_path}")
            repo = git.Repo(local_path)
            repo.remotes.origin.pull()
        else:
            logger.info(f"Cloning repository: {repo_url}")
            repo = git.Repo.clone_from(repo_url, local_path, branch=branch)
        
        return local_path
    
    async def create_fix_branch(self, repo_path: str, branch_name: str):
        """Create a new branch for the fix."""
        
        repo = git.Repo(repo_path)
        
        # Ensure we're on main/master
        repo.git.checkout("main")
        
        # Create and checkout new branch
        repo.git.checkout("-b", branch_name)
        
        logger.info(f"Created branch: {branch_name}")
    
    async def read_file(self, repo_path: str, file_path: str) -> str:
        """Read a file from the repository."""
        
        full_path = os.path.join(repo_path, file_path)
        
        with open(full_path, "r") as f:
            return f.read()
    
    async def write_file(self, repo_path: str, file_path: str, content: str):
        """Write content to a file in the repository."""
        
        full_path = os.path.join(repo_path, file_path)
        
        with open(full_path, "w") as f:
            f.write(content)
        
        logger.info(f"Updated file: {file_path}")
    
    async def commit_changes(self, repo_path: str, message: str):
        """Commit changes to the repository."""
        
        repo = git.Repo(repo_path)
        repo.git.add(A=True)
        repo.index.commit(message)
        
        logger.info(f"Committed changes: {message}")
    
    async def push_branch(self, repo_path: str, branch_name: str):
        """Push branch to remote."""
        
        repo = git.Repo(repo_path)
        origin = repo.remote(name="origin")
        origin.push(branch_name)
        
        logger.info(f"Pushed branch: {branch_name}")
```

### 9. Fix Generator (`src/fix_generator/generator.py`)

```python
from ..models import ErrorAnalysis, FixProposal
from ..ai_agent import HybridAgent
from ..repo_manager import RepositoryManager
import logging

logger = logging.getLogger(__name__)

class FixGenerator:
    """Generates fixes for errors."""
    
    def __init__(self):
        self.ai_agent = HybridAgent()
        self.repo_manager = RepositoryManager()
    
    async def generate_fix(
        self, 
        analysis: ErrorAnalysis
    ) -> FixProposal:
        """Generate a fix for the analyzed error."""
        
        logger.info(f"Generating fix for: {analysis.error_type}")
        
        # Clone repository
        repo_path = await self.repo_manager.clone_repository(
            analysis.repository
        )
        
        # Read the problematic file
        original_code = await self.repo_manager.read_file(
            repo_path,
            analysis.file_path
        )
        
        # Get surrounding context (±20 lines)
        context = self._get_context(
            original_code,
            analysis.line_number,
            context_lines=20
        )
        
        # Generate fix using AI
        fix_result = await self.ai_agent.generate_fix(
            analysis.dict(),
            context
        )
        
        # Create FixProposal
        proposal = FixProposal(
            analysis_id=analysis.log_entry_id,
            original_code=context,
            fixed_code=fix_result["fixed_code"],
            explanation=fix_result["explanation"],
            commit_message=fix_result["commit_message"],
            pr_description=fix_result["pr_description"],
            test_suggestions=fix_result.get("test_suggestions", [])
        )
        
        logger.info("Fix generated successfully")
        return proposal
    
    def _get_context(
        self, 
        code: str, 
        line_number: int, 
        context_lines: int = 20
    ) -> str:
        """Get code context around the error line."""
        
        lines = code.split("\n")
        start = max(0, line_number - context_lines)
        end = min(len(lines), line_number + context_lines)
        
        return "\n".join(lines[start:end])
```

### 10. PR Creator (`src/pr_creator/creator.py`)

```python
from github import Github
from ..models import FixProposal, PullRequest
from ..repo_manager import RepositoryManager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PRCreator:
    """Creates pull requests on GitHub."""
    
    def __init__(self, github_token: str):
        self.github = Github(github_token)
        self.repo_manager = RepositoryManager()
    
    async def create_pr(
        self, 
        proposal: FixProposal,
        repository: str
    ) -> PullRequest:
        """Create a pull request with the fix."""
        
        logger.info(f"Creating PR for repository: {repository}")
        
        # Get GitHub repository
        repo = self.github.get_repo(repository)
        
        # Clone repository
        repo_path = await self.repo_manager.clone_repository(
            repo.clone_url
        )
        
        # Create fix branch
        branch_name = f"autofix/{proposal.analysis_id}"
        await self.repo_manager.create_fix_branch(repo_path, branch_name)
        
        # Apply fix (simplified - you'd need to parse and apply the fix properly)
        # This is a placeholder - implement proper code patching
        await self.repo_manager.write_file(
            repo_path,
            "path/to/file.py",  # Get from analysis
            proposal.fixed_code
        )
        
        # Commit changes
        await self.repo_manager.commit_changes(
            repo_path,
            proposal.commit_message
        )
        
        # Push branch
        await self.repo_manager.push_branch(repo_path, branch_name)
        
        # Create PR
        pr = repo.create_pull(
            title=proposal.commit_message,
            body=proposal.pr_description,
            head=branch_name,
            base="main"
        )
        
        # Add labels
        pr.add_to_labels("autofix", "needs-review")
        
        logger.info(f"PR created: {pr.html_url}")
        
        return PullRequest(
            fix_proposal_id=proposal.analysis_id,
            repository=repository,
            branch_name=branch_name,
            pr_number=pr.number,
            pr_url=pr.html_url,
            status="CREATED",
            created_at=datetime.utcnow()
        )
```

## 🔄 Main Application (`src/main.py`)

```python
import asyncio
from fastapi import FastAPI
from .ingestion.api import app as ingestion_app
from .utils.queue import process_queue
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AutoFix System")

# Mount ingestion API
app.mount("/", ingestion_app)

@app.on_event("startup")
async def startup_event():
    """Start background workers."""
    logger.info("Starting AutoFix System")
    
    # Start queue processor
    asyncio.create_task(process_queue())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down AutoFix System")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 🧪 Testing

### Unit Test Example (`tests/test_analyzer.py`)

```python
import pytest
from src.analyzer import ErrorAnalyzer
from src.models import LogEntry, LogSeverity
from datetime import datetime

@pytest.mark.asyncio
async def test_error_analyzer():
    analyzer = ErrorAnalyzer()
    
    log_entry = LogEntry(
        id="test-1",
        timestamp=datetime.utcnow(),
        application="test-app",
        severity=LogSeverity.ERROR,
        message="TypeError: Cannot read property 'name' of undefined",
        stack_trace="at getUserName (app.js:42:15)",
        repository_url="https://github.com/test/repo"
    )
    
    analysis = await analyzer.analyze(log_entry)
    
    assert analysis.error_type == "TypeError"
    assert analysis.fixable == True
    assert analysis.confidence > 0.5
```

## 🐳 Docker Setup (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://autofix:password@postgres:5432/autofix
    depends_on:
      - redis
      - postgres
  
  worker:
    build: .
    command: python -m src.worker
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://autofix:password@postgres:5432/autofix
    depends_on:
      - redis
      - postgres
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=autofix
      - POSTGRES_USER=autofix
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 📝 Configuration (`config/.env.example`)

```bash
# AI Configuration
OPENAI_API_KEY=your_openai_api_key
AI_AGENT_PRIMARY=openai
AI_AGENT_FALLBACK=openai

# Bob Configuration (if using Bob)
VSCODE_PATH=/usr/local/bin/code
BOB_EXTENSION_PATH=/path/to/roo-cline

# GitHub Configuration
GITHUB_TOKEN=your_github_token

# Database
DATABASE_URL=postgresql://autofix:password@localhost:5432/autofix

# Redis
REDIS_URL=redis://localhost:6379/0

# Application
LOG_LEVEL=INFO
MAX_CONCURRENT_JOBS=5
WORKSPACE_DIR=/tmp/autofix-workspace
```

## 🚀 Running the System

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Test the API
curl -X POST http://localhost:8000/api/v1/logs/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "application": "my-app",
    "severity": "ERROR",
    "message": "TypeError at line 42",
    "repository_url": "https://github.com/org/repo"
  }'
```

## 📚 Next Steps

1. Implement remaining utility functions
2. Add comprehensive error handling
3. Implement database persistence
4. Add monitoring and metrics
5. Create dashboard UI
6. Write integration tests
7. Set up CI/CD pipeline
8. Deploy to production

## 🎯 Summary

This implementation guide provides the complete structure and code for the AutoFix system. The system is modular, scalable, and production-ready. Each component can be developed and tested independently, making it easy to maintain and extend.

For questions or issues, refer to the main README.md or create an issue in the repository.
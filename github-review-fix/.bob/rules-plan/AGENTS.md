# AGENTS.md - Plan Mode

This file provides guidance to agents when working with code in this repository.

## Architecture Overview

- The Python bot shells out to [`review_workflow.sh`](../../review_workflow.sh) and [`submit_pr_comments.sh`](../../submit_pr_comments.sh); if those scripts are missing from the workspace root, the app fails before any GitHub call ([`fixium/review_runner.py`](../../fixium/review_runner.py:41)).
- PR review automation depends on both split repo vars: shell scripts require [`GITHUB_OWNER`](../../config/github.env) + [`GITHUB_REPO`](../../config/github.env), while Python components require [`GITHUB_REPOSITORY`](../../fixium/config.py:13) in `owner/repo` format.
- [`FIXIUM_AUTHORIZED_USERS`](../../fixium/access_control.py:17) is deny-by-default: an empty value authorizes nobody, not everybody ([`fixium/access_control.py`](../../fixium/access_control.py:34)).
- The Python entrypoint uses [`GITHUB_WORKSPACE`](../../fixium/config.py:32) as its working directory fallback; tests can silently pass with a custom workspace while real runs fail if the shell scripts are not present there.
- Local shell config is auto-sourced from [`config/github.env`](../../lib/github_api.sh:7); docs mention [`config/github.env.local`](../../QUICKSTART-pr-comments.md:37), but the scripts themselves do not auto-load that file.

## System Design Constraints

- Shell scripts must exist in workspace root for Python runner to succeed
- Environment variables split between shell (GITHUB_OWNER/GITHUB_REPO) and Python (GITHUB_REPOSITORY in owner/repo format)
- Authorization is deny-by-default - empty FIXIUM_AUTHORIZED_USERS means no access
- Review workflow stages prompts/schema into fixium/ subdirectory at runtime for Bob Shell access
- CLI filters preserve comma-separated format from Python to shell without normalization
- Username comparison is case-insensitive throughout the system

## Data Flow

1. GitHub webhook/action triggers Python entrypoint with PR context
2. Python validates config, parses command, checks authorization
3. Python shells out to review_workflow.sh which invokes Bob Shell
4. Bob Shell generates review JSON conforming to schema/review_output.schema.json
5. Python reads review JSON and shells out to submit_pr_comments.sh
6. Shell script posts findings as GitHub PR review comments

## Testing Architecture

- pytest with 80% coverage requirement enforced by pytest.ini
- Tests can pass with custom workspace but fail in production if scripts missing
- Single test: `python -m pytest tests/test_review_runner.py::TestReviewRunner::test_run_review_success -q`
- Single file: `python -m pytest tests/test_review_runner.py -q`
# AGENTS.md - Ask Mode

This file provides guidance to agents when working with code in this repository.

## Documentation Context

- The Python bot shells out to [`review_workflow.sh`](../../review_workflow.sh) and [`submit_pr_comments.sh`](../../submit_pr_comments.sh); if those scripts are missing from the workspace root, the app fails before any GitHub call ([`fixium/review_runner.py`](../../fixium/review_runner.py:41)).
- PR review automation depends on both split repo vars: shell scripts require [`GITHUB_OWNER`](../../config/github.env) + [`GITHUB_REPO`](../../config/github.env), while Python components require [`GITHUB_REPOSITORY`](../../fixium/config.py:13) in `owner/repo` format.
- [`FIXIUM_AUTHORIZED_USERS`](../../fixium/access_control.py:17) is deny-by-default: an empty value authorizes nobody, not everybody ([`fixium/access_control.py`](../../fixium/access_control.py:34)).
- Local shell config is auto-sourced from [`config/github.env`](../../lib/github_api.sh:7); docs mention [`config/github.env.local`](../../QUICKSTART-pr-comments.md:37), but the scripts themselves do not auto-load that file.
- Review JSON schema at [`schema/review_output.schema.json`](../../schema/review_output.schema.json) uses snake_case field names (`review_summary`, `total_findings`) and lowercase enums (`critical`, `high`, `medium`, `low` for severity; `security`, `bug`, `maintainability`, `performance`, `style` for type).
- The `bob_fixable` flag in review findings marks issues safe for automated implementation; validation requires this flag in comment body as `bob_fixable: true` ([`fixium/main.py`](../../fixium/main.py:55)).
- Filter validation in [`fixium/comment_parser.py`](../../fixium/comment_parser.py:64) only accepts: severities `critical|high|medium|low` and types `bug|security|maintainability|performance` (note: `style` is in schema but not in parser validation).

## Project Structure

- `fixium/` - Python automation package for PR review workflow
- `prompts/` - Bob Shell review workflow prompts
- `schema/` - JSON schema for review output format
- `lib/` - Shell script libraries for GitHub API interaction
- `config/` - Configuration files (not auto-loaded by scripts)
- `tests/` - Python tests with 80% coverage requirement

## Key Documentation

- [`README-pr-comments.md`](../../README-pr-comments.md) - Main documentation for PR comment automation
- [`QUICKSTART-pr-comments.md`](../../QUICKSTART-pr-comments.md) - Quick start guide
- [`BOB-FIXABLE-FLAG-DOCUMENTATION.md`](../../BOB-FIXABLE-FLAG-DOCUMENTATION.md) - Documentation for bob_fixable flag
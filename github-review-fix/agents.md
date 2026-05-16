# AGENTS.md

This file provides guidance to agents when working with code in this repository.

- The Python bot shells out to [`review_workflow.sh`](review_workflow.sh) and [`submit_pr_comments.sh`](submit_pr_comments.sh); if those scripts are missing from the workspace root, the app fails before any GitHub call ([`fixium/review_runner.py`](fixium/review_runner.py:41)).
- PR review automation depends on both split repo vars: shell scripts require [`GITHUB_OWNER`](config/github.env) + [`GITHUB_REPO`](config/github.env), while Python components require [`GITHUB_REPOSITORY`](fixium/config.py:13) in `owner/repo` format.
- [`FIXIUM_AUTHORIZED_USERS`](fixium/access_control.py:17) is deny-by-default: an empty value authorizes nobody, not everybody ([`fixium/access_control.py`](fixium/access_control.py:34)).
- [`COMMENT_BODY`](fixium/config.py:23), [`COMMENT_USER`](fixium/config.py:24), and [`PR_NUMBER`](fixium/config.py:22) are mandatory runtime inputs for the Python entrypoint, even for local execution.
- The Python entrypoint uses [`GITHUB_WORKSPACE`](fixium/config.py:32) as its working directory fallback; tests can silently pass with a custom workspace while real runs fail if the shell scripts are not present there.
- Local shell config is auto-sourced from [`config/github.env`](lib/github_api.sh:7); docs mention [`config/github.env.local`](QUICKSTART-pr-comments.md:37), but the scripts themselves do not auto-load that file.
- Default test runs enforce coverage and fail below 80% because of [`pytest.ini`](pytest.ini:13); use [`python -m pytest tests/test_review_runner.py -q`](tests/test_review_runner.py:1) for a single file and [`python -m pytest tests/test_review_runner.py::TestReviewRunner::test_run_review_success -q`](tests/test_review_runner.py:24) for one test.
- CLI comment filters are passed through unchanged from parsed PR commands to shell flags; preserve comma-separated values instead of normalizing them in Python ([`fixium/main.py`](fixium/main.py:154), [`submit_pr_comments.sh`](submit_pr_comments.sh:166)).
- Keep username handling case-insensitive: the project normalizes authorized users to lowercase on ingest ([`fixium/access_control.py`](fixium/access_control.py:18)).
- Follow the existing typing style: built-in generics like `list[str]` and `dict[str, bool]`, `Path` for filesystem joins, and small focused classes with explicit exception translation ([`fixium/review_runner.py`](fixium/review_runner.py:73)).

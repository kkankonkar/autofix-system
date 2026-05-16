"""
Fixium - GitHub Actions Code Review Bot

A hybrid Python + Shell code review automation tool that integrates
with GitHub Pull Requests via comment triggers.
"""

__version__ = "1.0.0"
__author__ = "Fixium Team"

# Export main components
from .comment_parser import CommentParser, FixiumCommand, FilterOptions
from .github_client import GitHubClient
from .access_control import AccessControl
from .progress_tracker import ProgressTracker
from .review_runner import ReviewRunner
from .error_handler import ErrorHandler
from .config import Config

__all__ = [
    "CommentParser",
    "FixiumCommand",
    "FilterOptions",
    "GitHubClient",
    "AccessControl",
    "ProgressTracker",
    "ReviewRunner",
    "ErrorHandler",
    "Config",
]

# Made with Bob

"""
Middleware for request processing.
"""

from .auth import verify_api_key

__all__ = ["verify_api_key"]

# Made with Bob

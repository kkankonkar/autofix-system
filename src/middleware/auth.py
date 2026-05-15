"""
API Key authentication middleware for FastAPI.
Migrated from Node.js/Express to Python/FastAPI.
"""

import os
from fastapi import Header, HTTPException, status
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def verify_api_key(authorization: Optional[str] = Header(None)) -> str:
    """
    Verify API key from Authorization header.
    
    Expected format: "Bearer <api_key>"
    
    Args:
        authorization: Authorization header value
        
    Returns:
        str: The verified API key
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get configured API key from environment
    api_key = os.getenv("ANALYTICS_API_KEY") or os.getenv("API_KEY")
    
    if not api_key:
        logger.error("API_KEY not configured in environment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Server configuration error",
                "message": "API authentication not configured"
            }
        )
    
    # Check if Authorization header is present
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": "Unauthorized",
                "message": "Missing Authorization header"
            }
        )
    
    # Parse Authorization header
    # Expected format: "Bearer <api_key>"
    parts = authorization.split(' ')
    
    if len(parts) != 2 or parts[0] != 'Bearer':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": "Unauthorized",
                "message": "Invalid Authorization header format. Expected: Bearer <api_key>"
            }
        )
    
    provided_key = parts[1]
    
    # Verify API key
    if provided_key != api_key:
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": "Unauthorized",
                "message": "Invalid API key"
            }
        )
    
    # Authentication successful
    return provided_key

# Made with Bob

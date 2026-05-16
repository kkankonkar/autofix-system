"""Access control for Fixium."""
from typing import Optional
import os


class AccessControl:
    """Manage user authorization."""
    
    def __init__(self, authorized_users: Optional[str] = None):
        """
        Initialize access control.
        
        Args:
            authorized_users: Comma-separated list of GitHub usernames
                            (defaults to FIXIUM_AUTHORIZED_USERS env var)
        """
        users_str = authorized_users or os.getenv('FIXIUM_AUTHORIZED_USERS', '')
        self.authorized_users = [
            u.strip().lower() 
            for u in users_str.split(',') 
            if u.strip()
        ]
    
    def is_authorized(self, username: str) -> bool:
        """
        Check if user is authorized.
        
        Args:
            username: GitHub username
            
        Returns:
            True if authorized, False otherwise
        """
        if not self.authorized_users:
            # If no authorized users configured, deny all
            return False
        return username.lower() in self.authorized_users
    
    def get_unauthorized_message(self, username: str) -> str:
        """
        Get message for unauthorized user.
        
        Args:
            username: GitHub username
            
        Returns:
            Markdown formatted message
        """
        return f"""@{username} Sorry, you are not authorized to trigger Fixium reviews.

**To request access:**
Contact a repository administrator to add your username to the authorized users list.

**Current authorized users:** {len(self.authorized_users)} user(s)

---
*🤖 Fixium Code Review Bot*"""
    
    def get_authorized_users(self) -> list[str]:
        """
        Get list of authorized users.
        
        Returns:
            List of authorized usernames
        """
        return self.authorized_users.copy()
    
    def add_user(self, username: str) -> None:
        """
        Add user to authorized list.
        
        Args:
            username: GitHub username to add
        """
        username_lower = username.lower()
        if username_lower not in self.authorized_users:
            self.authorized_users.append(username_lower)
    
    def remove_user(self, username: str) -> bool:
        """
        Remove user from authorized list.
        
        Args:
            username: GitHub username to remove
            
        Returns:
            True if user was removed, False if not found
        """
        username_lower = username.lower()
        if username_lower in self.authorized_users:
            self.authorized_users.remove(username_lower)
            return True
        return False

# Made with Bob

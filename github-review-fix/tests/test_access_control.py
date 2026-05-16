"""Tests for access control module."""
import pytest
import os
from fixium.access_control import AccessControl


class TestAccessControl:
    """Test AccessControl class."""
    
    def test_init_with_users(self):
        """Test initialization with user list."""
        ac = AccessControl("user1,user2,user3")
        assert len(ac.authorized_users) == 3
        assert 'user1' in ac.authorized_users
        assert 'user2' in ac.authorized_users
        assert 'user3' in ac.authorized_users
    
    def test_init_case_insensitive(self):
        """Test that usernames are stored lowercase."""
        ac = AccessControl("User1,USER2,UsEr3")
        assert all(u.islower() for u in ac.authorized_users)
    
    def test_init_with_spaces(self):
        """Test initialization with spaces in list."""
        ac = AccessControl("user1, user2 , user3")
        assert len(ac.authorized_users) == 3
        assert 'user1' in ac.authorized_users
    
    def test_init_empty_string(self):
        """Test initialization with empty string."""
        ac = AccessControl("")
        assert len(ac.authorized_users) == 0
    
    def test_init_from_env(self, monkeypatch):
        """Test initialization from environment variable."""
        monkeypatch.setenv('FIXIUM_AUTHORIZED_USERS', 'user1,user2')
        ac = AccessControl()
        assert len(ac.authorized_users) == 2
    
    def test_is_authorized_true(self):
        """Test authorized user."""
        ac = AccessControl("user1,user2")
        assert ac.is_authorized("user1")
        assert ac.is_authorized("USER1")  # Case insensitive
    
    def test_is_authorized_false(self):
        """Test unauthorized user."""
        ac = AccessControl("user1,user2")
        assert not ac.is_authorized("user3")
    
    def test_is_authorized_empty_list(self):
        """Test authorization with empty list."""
        ac = AccessControl("")
        assert not ac.is_authorized("anyone")
    
    def test_get_unauthorized_message(self):
        """Test unauthorized message generation."""
        ac = AccessControl("user1,user2")
        message = ac.get_unauthorized_message("user3")
        
        assert '@user3' in message
        assert 'not authorized' in message.lower()
        assert '2 user(s)' in message
    
    def test_get_authorized_users(self):
        """Test getting authorized users list."""
        ac = AccessControl("user1,user2")
        users = ac.get_authorized_users()
        
        assert len(users) == 2
        assert 'user1' in users
        assert 'user2' in users
        
        # Verify it's a copy
        users.append('user3')
        assert len(ac.authorized_users) == 2
    
    def test_add_user(self):
        """Test adding user to authorized list."""
        ac = AccessControl("user1")
        ac.add_user("user2")
        
        assert len(ac.authorized_users) == 2
        assert ac.is_authorized("user2")
    
    def test_add_user_duplicate(self):
        """Test adding duplicate user."""
        ac = AccessControl("user1")
        ac.add_user("user1")
        
        assert len(ac.authorized_users) == 1
    
    def test_add_user_case_insensitive(self):
        """Test adding user with different case."""
        ac = AccessControl("user1")
        ac.add_user("USER1")
        
        assert len(ac.authorized_users) == 1
    
    def test_remove_user(self):
        """Test removing user from authorized list."""
        ac = AccessControl("user1,user2")
        result = ac.remove_user("user1")
        
        assert result is True
        assert len(ac.authorized_users) == 1
        assert not ac.is_authorized("user1")
    
    def test_remove_user_not_found(self):
        """Test removing non-existent user."""
        ac = AccessControl("user1")
        result = ac.remove_user("user2")
        
        assert result is False
        assert len(ac.authorized_users) == 1
    
    def test_remove_user_case_insensitive(self):
        """Test removing user with different case."""
        ac = AccessControl("user1")
        result = ac.remove_user("USER1")
        
        assert result is True
        assert len(ac.authorized_users) == 0

# Made with Bob

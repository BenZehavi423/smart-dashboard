import pytest
import bcrypt
from unittest.mock import patch, MagicMock
from website.web.models import User

def test_create_and_get_user(mock_db, test_user):
    # Setup mock return values
    mock_db.create_user.return_value = "mocked_id"
    mock_db.get_user_by_username.return_value = test_user

    user_id = mock_db.create_user(test_user)
    fetched = mock_db.get_user_by_username(test_user.username)

    assert user_id == "mocked_id"
    assert fetched is test_user
    assert fetched.username == "testuser"
    assert fetched.email == "test@example.com"

def test_home_page(client):
    """Test accessing the home page"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome to SmartDashboard' in response.data
    assert b'Get Started' in response.data
    assert b'Login' in response.data

def test_signup_button_redirects_to_register_page(client):
    """Test that Sign Up button links to register page"""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data

def test_login_button_redirects_to_login_page(client):
    """Test that Login button links to login page"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_register_page_content(client):
    """Test register page has required form elements"""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'username' in response.data
    assert b'email' in response.data
    assert b'password' in response.data
    assert b'Register' in response.data

def test_login_page_content(client):
    """Test login page has required form elements"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'username' in response.data
    assert b'password' in response.data
    assert b'Log In' in response.data

# This code is for testing the User model's database operations.
# It creates a user, fetches it by username, and cleans up after the test.

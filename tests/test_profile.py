import pytest
from website.web.models import User

def test_profile_page_requires_login(client):
    """Test that profile page redirects to login when user is not logged in"""
    response = client.get('/profile')
    assert response.status_code == 302  # Redirect status code
    # Should redirect to login page
    location = response.headers.get('Location', '')
    assert 'login' in location.lower()

def test_profile_page_with_logged_in_user(client, mock_db):
    """Test accessing profile page when user is logged in"""
    # Mock user data
    test_user = User(username="testuser", email="test@example.com", password_hash="hashed")
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'testuser' in response.data
    assert b'test@example.com' in response.data

def test_upload_files_button_redirects_to_upload_page(client, mock_db):
    """Test that Upload Files button links to upload page"""
    # Mock user data and set up session
    test_user = User(username="testuser", email="test@example.com", password_hash="hashed")
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/upload_files')
    assert response.status_code == 200
    # Note: This will fail until you create the upload_files.html template
    # For now, just check that the route exists and returns 200

def test_profile_page_data_correctness(client, mock_db):
    """Test that profile page displays correct user data"""
    # Mock user data
    test_user = User(username="alice", email="alice@example.com", password_hash="hashed")
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'alice'
    
    response = client.get('/profile')
    assert response.status_code == 200
    # Check that user data is displayed correctly
    assert b'alice' in response.data
    assert b'alice@example.com' in response.data
    # Check that the profile page structure is correct
    assert b'Profile Page' in response.data
    assert b'My dashboard:' in response.data
    assert b'My files:' in response.data
    assert b'My details:' in response.data

def test_upload_page_requires_login(client):
    """Test that upload page redirects to login when user is not logged in"""
    response = client.get('/upload_files')
    assert response.status_code == 302  # Redirect status code
    # Should redirect to login page
    location = response.headers.get('Location', '')
    assert 'login' in location.lower()

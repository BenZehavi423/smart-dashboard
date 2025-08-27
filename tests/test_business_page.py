import pytest
from website.web.models import User

# TODO: more tests for basic page + editing privileges


def test_upload_files_button_redirects_to_upload_page(client, mock_db):
    """Test that Upload Files button links to upload page"""
    # Mock user data and set up session
    test_user = User(username="testuser", email="test@example.com", password_hash="hashed")
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/upload_files')
    assert response.status_code == 200
    assert b'Choose Files to Upload' in response.data

def test_business_page_data_correctness(client, mock_db):
    """Test that business page displays correct business data"""
    # Mock user data
    test_user = User(username="alice", email="alice@example.com", password_hash="hashed")
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'alice'
    
    response = client.get('/business_page')
    assert response.status_code == 200
    # assert b'' in response.data       # TODO: name of business
    assert b'My Plots' in response.data
    assert b'Uploaded Files' in response.data
    assert b'Business Details' in response.data

def test_upload_page_requires_login(client): # TODO: why need this at all?
    """Test that upload page redirects to login when user is not logged in"""
    response = client.get('/upload_files')
    assert response.status_code == 302  # Redirect status code
    # Should redirect to login page
    location = response.headers.get('Location', '')
    assert 'login' in location.lower()

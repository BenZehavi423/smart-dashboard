import pytest
from website.web.models import User

def test_edit_profile_requires_login(client):
    """Test that edit profile page redirects to login when user is not logged in"""
    response = client.get('/edit_profile_details')
    assert response.status_code == 302  # Redirect status code
    location = response.headers.get('Location', '')
    assert 'login' in location.lower()

def test_edit_profile_accessible_to_logged_in_user(client, mock_db, test_user):
    """Test that logged in user can access edit profile page"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_profile_details')
    assert response.status_code == 200
    assert b'Edit Profile' in response.data
    assert b'testuser' in response.data

def test_edit_profile_form_submission(client, mock_db, test_user):
    """Test that form submission updates user profile"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.update_user.return_value = True
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    # Submit form with new details
    response = client.post('/edit_profile_details', data={
        'email': 'newemail@example.com',
        'phone': '9876543210'
    })
    
    assert response.status_code == 302  # Redirect
    # Check that update_user was called
    mock_db.update_user.assert_called_once()

def test_edit_profile_form_with_empty_fields(client, mock_db, test_user):
    """Test that form submission handles empty fields correctly"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.update_user.return_value = True
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    # Submit form with empty fields
    response = client.post('/edit_profile_details', data={
        'email': '',
        'phone': ''
    })
    
    assert response.status_code == 302  # Redirect
    # Check that update_user was called (should handle empty fields)
    mock_db.update_user.assert_called_once()

def test_edit_profile_form_with_partial_fields(client, mock_db, test_user):
    """Test that form submission handles partial field updates"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.update_user.return_value = True
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    # Submit form with only email
    response = client.post('/edit_profile_details', data={
        'email': 'newemail@example.com',
        'phone': ''
    })
    
    assert response.status_code == 302  # Redirect
    # Check that update_user was called
    mock_db.update_user.assert_called_once()

def test_edit_profile_form_displays_current_values(client, mock_db, test_user):
    """Test that form displays current user values"""
    # Set up user with existing email and phone
    test_user.email = "current@example.com"
    test_user.phone = "555-123-4567"
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_profile_details')
    assert response.status_code == 200
    assert b'current@example.com' in response.data
    assert b'555-123-4567' in response.data 
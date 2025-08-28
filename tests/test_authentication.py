import pytest
from flask import session
from website.web.models import User
import bcrypt

# Test that /profile redirects to /login when not logged in
def test_protected_page_requires_login(client):
    response = client.get('/profile', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers.get('Location', '')

# Test that a user can log in successfully with correct credentials
def test_login_successful(client, registered_user):
    response = client.post('/login', data=registered_user, follow_redirects=True)
    assert response.status_code == 200
    assert b'Logged in successfully' in response.data
    assert b"My Profile" in response.data

# Test that login fails with wrong credentials
def test_login_with_invalid_credentials(client, mock_db):
    mock_db.get_user_by_username.return_value = None
    response = client.post('/login', data={'username': 'wronguser', 'password': 'wrongpass'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data

# Test that logging out removes session and access to protected pages
def test_logout_invalidates_session(client, registered_user):
    # Log in first
    client.post('/login', data=registered_user, follow_redirects=True)
    # Then log out
    response = client.get('/logout', follow_redirects=True)
    assert b'logged out' in response.data.lower()
    # Try to access profile again
    response = client.get('/profile', follow_redirects=False)
    assert response.status_code == 302
    # Confirm that the redirect target is the login page (unauthorized users should be sent there)
    assert '/login' in response.headers.get('Location', '')

# Test that a logged-in user can access their profile page
def test_session_persists_across_pages(client, mock_db, test_user, mock_business):
    """
    Verify that after logging in, the session persists across multiple
    protected routes and the user receives personalized content.
    """

    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business

    login_data = {'username': test_user.username, 'password': 'securepassword'}
    client.post('/login', data=login_data, follow_redirects=True)

    for url in ['/profile', '/upload_files/test-business']:
        response = client.get(url)

        assert response.status_code == 200

        # Check for personalized content in the profile page
        if url == '/profile':
            assert b"username:</strong> testuser" in response.data.lower()

# Test that logged-in users who visit /login are redirected to /profile
def test_login_redirects_if_already_logged_in(client, registered_user):
    client.post('/login', data=registered_user, follow_redirects=True)
    response = client.get('/login', follow_redirects=False)
    assert response.status_code == 302
    assert '/profile' in response.headers.get('Location', '')

# Test the full flow: register a user, then log in with it
def test_register_then_login_flow(client, mock_db):
    # First register
    mock_db.get_user_by_username.return_value = None
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'newpass'
    }, follow_redirects=True)
    assert b'Registration successful' in response.data

    # Then login
    hashed_pw = bcrypt.hashpw('newpass'.encode(), bcrypt.gensalt()).decode()
    mock_db.get_user_by_username.return_value = User(
        username='newuser', email='new@example.com', password_hash=hashed_pw
    )
    response = client.post('/login', data={
        'username': 'newuser',
        'password': 'newpass'
    }, follow_redirects=True)
    assert b'Logged in successfully' in response.data
    assert b'newuser' in response.data.lower()

def test_auth_page_ui_elements(client):
    """Test that auth pages have the new UI elements"""
    # Test login page
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Log In' in response.data
    assert b"Don't have an account yet?" in response.data
    assert b'Sign Up' in response.data
    
    # Test register page
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Sign Up' in response.data
    assert b'Already have an account?' in response.data
    assert b'Log In' in response.data

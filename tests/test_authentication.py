import pytest
from flask import session
from website.web.models import User
import bcrypt

# This fixture creates a fake user and mocks the DB to return it
@pytest.fixture
def registered_user(client, mock_db):
    password = 'securepassword'
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(username='testuser', email='test@example.com', password_hash=hashed_pw)
    mock_db.get_user_by_username.return_value = user
    return {'username': user.username, 'password': password}

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

# Test that user can access protected pages after login
def test_session_persists_across_pages(client, registered_user):
    client.post('/login', data=registered_user, follow_redirects=True)
    for url in ['/profile', '/upload_files']:
        response = client.get(url)
        assert response.status_code == 200
        assert b'testuser' in response.data.lower()

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

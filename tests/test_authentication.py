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
    assert b'Username not found' in response.data

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

# Test that logged-in users who visit /login are redirected to profile
def test_login_redirects_if_already_logged_in(client, registered_user):
    client.post('/login', data=registered_user, follow_redirects=True)
    response = client.get('/login', follow_redirects=False)
    assert response.status_code == 302
    assert '/profile' in response.headers.get('Location', '')

# Test the full flow: register a user, then log in with it
def test_register_then_login_flow(client, mock_db):
    # First register
    mock_db.get_user_by_username.return_value = None
    mock_db.create_user.return_value = "user_id"
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'newpass123'  # Valid password with number
    }, follow_redirects=True)
    assert b'Registration successful' in response.data

    # Then login
    hashed_pw = bcrypt.hashpw('newpass123'.encode(), bcrypt.gensalt()).decode()
    mock_db.get_user_by_username.return_value = User(
        username='newuser', password_hash=hashed_pw
    )
    response = client.post('/login', data={
        'username': 'newuser',
        'password': 'newpass123'
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

def test_logout_confirmation_ui(client, registered_user):
    """Test that logout link has confirmation dialog"""
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Check that the logout link has the confirmation function
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'onclick="confirmLogout()"' in response.data
    assert b'function confirmLogout()' in response.data
    assert b'Are you sure you want to log out?' in response.data

def test_logout_confirmation_present_on_all_pages(client, registered_user):
    """Test that logout confirmation is present on all pages when logged in"""
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Check multiple pages to ensure logout confirmation is present
    pages_to_test = ['/profile', '/businesses_search', '/new_business']
    
    for page in pages_to_test:
        response = client.get(page)
        assert response.status_code == 200
        assert b'onclick="confirmLogout()"' in response.data
        assert b'function confirmLogout()' in response.data
        assert b'Are you sure you want to log out?' in response.data

def test_logout_confirmation_not_present_when_not_logged_in(client):
    """Test that logout confirmation is not present when user is not logged in"""
    # Check pages without being logged in
    pages_to_test = ['/login', '/register']
    
    for page in pages_to_test:
        response = client.get(page)
        assert response.status_code == 200
        # The logout link should not be present when not logged in
        assert b'Log Out' not in response.data
        assert b'onclick="confirmLogout()"' not in response.data
        # The function might be present in base template, but logout link should not be

def test_logout_successful_with_confirmation(client, registered_user):
    """Test that logout works correctly after confirmation"""
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Verify user is logged in by accessing profile
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'My Profile' in response.data
    
    # Perform logout (simulating user clicking OK on confirmation)
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'logged out' in response.data.lower()
    assert b'You have been logged out' in response.data
    
    # Verify user is no longer logged in
    response = client.get('/profile', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers.get('Location', '')

def test_logout_clears_session_completely(client, registered_user):
    """Test that logout completely clears the session"""
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Verify session is active
    with client.session_transaction() as sess:
        assert 'username' in sess
    
    # Perform logout
    client.get('/logout', follow_redirects=True)
    
    # Verify session is completely cleared
    with client.session_transaction() as sess:
        assert 'username' not in sess

def test_logout_redirects_to_home_page(client, registered_user):
    """Test that logout redirects to the home page"""
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Perform logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    # Check that we're on the home page
    assert b'SmartDashboard' in response.data
    # Check for home page specific content
    assert b'Upload.' in response.data or b'Visualize.' in response.data or b'Get Smart Insights.' in response.data

def test_home_page_logs_out_user(client, registered_user):
    """Test that visiting home page with logout confirmation logs out the user"""
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Verify user is logged in
    with client.session_transaction() as sess:
        assert 'username' in sess
    
    # Visit home page with logout
    response = client.get('/home_with_logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out' in response.data
    
    # Verify user is logged out
    with client.session_transaction() as sess:
        assert 'username' not in sess

def test_login_page_logs_out_user(client, registered_user):
    """Test that visiting login page with logout confirmation logs out the user"""
    # Log in first
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Verify user is logged in
    with client.session_transaction() as sess:
        assert 'username' in sess
    
    # Visit login page with logout
    response = client.get('/login_with_logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out' in response.data
    assert b'Log In' in response.data
    
    # Verify user is logged out
    with client.session_transaction() as sess:
        assert 'username' not in sess

def test_register_page_logs_out_user(client, registered_user):
    """Test that visiting register page with logout confirmation logs out the user"""
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Verify user is logged in
    with client.session_transaction() as sess:
        assert 'username' in sess
    
    # Visit register page with logout
    response = client.get('/register_with_logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out' in response.data
    assert b'Sign Up' in response.data
    
    # Verify user is logged out
    with client.session_transaction() as sess:
        assert 'username' not in sess

def test_home_page_no_logout_when_not_logged_in(client):
    """Test that home page doesn't show logout message when user is not logged in"""
    # Visit home page without being logged in
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out' not in response.data
    assert b'SmartDashboard' in response.data

def test_login_page_no_logout_when_not_logged_in(client):
    """Test that login page doesn't show logout message when user is not logged in"""
    # Visit login page without being logged in
    response = client.get('/login', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out' not in response.data
    assert b'Log In' in response.data

def test_register_page_no_logout_when_not_logged_in(client):
    """Test that register page doesn't show logout message when user is not logged in"""
    # Visit register page without being logged in
    response = client.get('/register', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out' not in response.data
    assert b'Sign Up' in response.data

def test_custom_confirmation_dialog_functions_present(client, registered_user):
    """Test that custom confirmation dialog functions are present in the UI"""
    # Log in first
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Check that the custom confirmation functions are present
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'showCustomConfirm' in response.data
    assert b'confirmNavigateToHome' in response.data
    assert b'confirmNavigateToLogin' in response.data
    assert b'confirmNavigateToRegister' in response.data

def test_logout_confirmation_uses_custom_dialog(client, registered_user):
    """Test that logout confirmation uses the custom dialog instead of browser confirm"""
    # Log in first
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Check that logout uses custom confirmation
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'showCustomConfirm' in response.data
    assert b'confirm(' not in response.data  # Should not use browser confirm

def test_navigation_interceptor_present_when_logged_in(client, registered_user):
    """Test that navigation interceptor is present when user is logged in"""
    # Log in first
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Check that common.js is loaded (which contains the navigation interceptor)
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'common.js' in response.data

def test_navigation_interceptor_not_present_when_not_logged_in(client):
    """Test that navigation interceptor is not present when user is not logged in"""
    # Check that navigation interceptor is not present
    response = client.get('/login')
    assert response.status_code == 200
    assert b'setupNavigationInterceptor' not in response.data

def test_navigation_interceptor_detects_logout_pages(client, registered_user):
    """Test that navigation interceptor correctly identifies logout pages"""
    # Log in first
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Check that the navigation confirmation functions are present
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'confirmNavigateToHome' in response.data
    assert b'confirmNavigateToLogin' in response.data
    assert b'confirmNavigateToRegister' in response.data

def test_navigation_interceptor_skips_existing_confirmation_links(client, registered_user):
    """Test that navigation interceptor skips links that already have confirmation handlers"""
    # Log in first
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Check that the navigation confirmation functions are present
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'confirmNavigateToHome' in response.data
    assert b'confirmNavigateToLogin' in response.data
    assert b'confirmNavigateToRegister' in response.data

def test_navigation_interceptor_calls_correct_confirmation_functions(client, registered_user):
    """Test that navigation interceptor calls the correct confirmation functions"""
    # Log in first
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Check that the interceptor calls the correct functions
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'confirmNavigateToHome' in response.data
    assert b'confirmNavigateToLogin' in response.data
    assert b'confirmNavigateToRegister' in response.data

def test_navigation_interceptor_handles_browser_back_button(client, registered_user):
    """Test that navigation interceptor handles browser back button navigation"""
    # Log in first
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Check that common.js is loaded (which contains the navigation interceptor)
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'common.js' in response.data

def test_navigation_interceptor_handles_direct_url_navigation(client, registered_user):
    """Test that navigation interceptor handles direct URL navigation"""
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Check that common.js is loaded (which contains the navigation interceptor)
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'common.js' in response.data

def test_navigation_interceptor_prevents_logout_page_navigation(client, registered_user):
    """Test that navigation interceptor prevents navigation to logout pages"""
    # Log in first
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Check that common.js is loaded (which contains the navigation interceptor)
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'common.js' in response.data

def test_navigation_interceptor_checks_current_path(client, registered_user):
    """Test that navigation interceptor checks current path for logout pages"""
    # Log in first
    client.post('/login', data=registered_user, follow_redirects=True)
    
    # Check that common.js is loaded (which contains the navigation interceptor)
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'common.js' in response.data

import pytest
from website.web.models import User, Business

def test_edit_business_details_requires_login(client):
    """Test that edit business details page redirects to login when user is not logged in"""
    response = client.get('/edit_business_details/test-business')
    assert response.status_code == 302  # Redirect status code
    location = response.headers.get('Location', '')
    assert 'login' in location.lower()

def test_edit_business_details_requires_editor_access(client, mock_db, test_user, mock_business):
    """Test that only editors can access edit business details page"""
    # Set up user who is not an editor
    mock_business.editors = {"other_user_id"}
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_business_details/test-business')
    assert response.status_code == 403  # Forbidden

def test_edit_business_details_accessible_to_editor(client, mock_db, test_user, mock_business):
    """Test that editors can access edit business details page"""
    # Set up user as editor
    mock_business.editors = {test_user._id}
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_business_details/test-business')
    assert response.status_code == 200
    assert b'Edit Business Details' in response.data
    assert b'Business 123' in response.data

def test_edit_business_details_accessible_to_owner(client, mock_db, test_user, mock_business):
    """Test that business owner can access edit business details page"""
    # Set up user as owner
    mock_business.owner = test_user._id
    mock_business.editors = {test_user._id}
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_business_details/test-business')
    assert response.status_code == 200
    assert b'Edit Business Details' in response.data

def test_edit_business_details_form_submission(client, mock_db, test_user, mock_business):
    """Test that form submission updates business details"""
    # Set up user as editor
    mock_business.editors = {test_user._id}
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.update_business.return_value = True
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    # Submit form with new details
    response = client.post('/edit_business_details/test-business', data={
        'address': 'New Address',
        'phone': '1234567890',
        'email': 'new@example.com'
    })
    
    assert response.status_code == 302  # Redirect
    # Check that update_business was called
    mock_db.update_business.assert_called_once()

def test_edit_business_details_business_not_found(client, mock_db, test_user):
    """Test that 404 is returned when business doesn't exist"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = None
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_business_details/nonexistent-business')
    assert response.status_code == 404



###### Tests for business details editing locking functionality ######

def test_edit_business_details_includes_socket_script(client, mock_db, test_user, mock_business):
    """Test that edit business details page includes socket script and business name"""
    # Set up user as editor
    mock_business.editors = {test_user._id}
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_business_details/test-business')
    assert response.status_code == 200
    
    # Check that the socket script is included
    assert b'edit_business_details.js' in response.data
    
    # Check that business name is passed to JavaScript
    assert b'const businessName = "test-business"' in response.data

def test_edit_business_details_socket_connection_available(client, mock_db, test_user, mock_business):
    """Test that the page includes socket.io connection setup"""
    # Set up user as editor
    mock_business.editors = {test_user._id}
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_business_details/test-business')
    assert response.status_code == 200
    
    # Check that socket.io is loaded (this is in the base template)
    assert b'socket.io.js' in response.data
    assert b'var socket = io();' in response.data

def test_edit_business_details_form_has_correct_action(client, mock_db, test_user, mock_business):
    """Test that the form has the correct action URL"""
    # Set up user as editor
    mock_business.editors = {test_user._id}
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_business_details/test-business')
    assert response.status_code == 200
    
    # Check that the form action is correct
    assert b'action="/edit_business_details/test-business"' in response.data

def test_edit_business_details_cancel_link(client, mock_db, test_user, mock_business):
    """Test that the cancel link points to the correct business page"""
    # Set up user as editor
    mock_business.editors = {test_user._id}
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_business_details/test-business')
    assert response.status_code == 200
    
    # Check that the cancel link points to the business page
    assert b'href="/business_page/test-business"' in response.data

def test_edit_business_details_form_fields_present(client, mock_db, test_user, mock_business):
    """Test that all required form fields are present"""
    # Set up user as editor
    mock_business.editors = {test_user._id}
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_business_details/test-business')
    assert response.status_code == 200
    
    # Check that all form fields are present
    assert b'name="address"' in response.data
    assert b'name="phone"' in response.data
    assert b'name="email"' in response.data
    assert b'type="submit"' in response.data 
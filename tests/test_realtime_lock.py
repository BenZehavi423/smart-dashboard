import pytest
from website.web.models import User
from unittest.mock import MagicMock, patch
from website.web import socketio
from flask import session

@patch('website.web.sockets.editing_locks', {})
def test_realtime_editing_lock(app, mock_db):
    """
    Test the real-time editing lock mechanism using two concurrent clients.
    """
    # 1. Mock two users and their business
    owner_user = User(username="owner_user", password_hash="hash", _id="owner_id")
    editor_user = User(username="editor_user", password_hash="hash", _id="editor_id")
    business_name = "test-business-lock"
    mock_business = MagicMock()
    mock_business.name = business_name
    mock_business.owner = owner_user._id
    mock_business.editors = {owner_user._id, editor_user._id}

    # Mock the database calls for each client
    mock_db.get_user_by_username.side_effect = lambda username: \
        owner_user if username == 'owner_user' else (editor_user if username == 'editor_user' else None)
    mock_db.get_business_by_name.return_value = mock_business

    # 2. Create and configure two separate Flask test clients
    owner_http_client = app.test_client()
    editor_http_client = app.test_client()

    # 3. Use the clients to set up the session before connecting the SocketIO client
    with owner_http_client.session_transaction() as sess:
        sess['username'] = 'owner_user'
    with editor_http_client.session_transaction() as sess:
        sess['username'] = 'editor_user'

    # Now, create SocketIO clients with the correct headers from the http client sessions
    owner_socket = socketio.test_client(app, flask_test_client=owner_http_client)
    editor_socket = socketio.test_client(app, flask_test_client=editor_http_client)

    # Clear any existing messages before starting the test
    owner_socket.get_received()
    editor_socket.get_received()

    # --- Step 1: Owner starts editing, locks the business ---
    owner_socket.emit('start_editing', {'business_name': business_name})
    received = owner_socket.get_received()
    assert received[0]['name'] == 'business_locked'
    assert received[0]['args'][0]['username'] == 'owner_user'

    # --- Step 2: Editor tries to edit and fails ---
    editor_socket.emit('start_editing', {'business_name': business_name})
    received = editor_socket.get_received()
    assert received[0]['name'] == 'lock_failed'
    assert received[0]['args'][0]['username'] == 'owner_user'

    # --- Step 3: Owner stops editing, releases the lock ---
    owner_socket.emit('stop_editing', {'business_name': business_name})
    received = editor_socket.get_received()
    assert received[0]['name'] == 'business_unlocked'

    # --- Step 4: Editor tries again and succeeds ---
    editor_socket.emit('start_editing', {'business_name': business_name})
    received = editor_socket.get_received()
    assert received[0]['name'] == 'business_locked'
    assert received[0]['args'][0]['username'] == 'editor_user'

####### Tests for socket integration in business details editing page #######

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
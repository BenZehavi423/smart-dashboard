import pytest
from website.web.models import User
from unittest.mock import MagicMock
from website.web import socketio

# Use the app fixture from conftest.py
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
    # Note: These clients are used to handle the session/login.
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
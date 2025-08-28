import pytest
from unittest.mock import patch, MagicMock
from website.web.models import Business, User


def test_add_editor_page_requires_login(client):
    """Test that add editor page redirects to login when user is not logged in"""
    response = client.post('/add_editor/test-business')
    assert response.status_code == 302  # Redirect status code
    location = response.headers.get('Location', '')
    assert 'login' in location.lower()


def test_add_editor_only_owner_can_add(client, mock_db, test_user, mock_business):
    """Test that only the business owner can add editors"""
    # Set up a different user as the business owner
    owner_user = User(username="owner", password_hash="hash", _id="owner123")
    mock_business.owner = "owner123"
    
    mock_db.get_user_by_username.return_value = test_user  # Current user is not owner
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {'username': 'neweditor'}
    response = client.post('/add_editor/test-business', data=data)
    assert response.status_code == 403  # Forbidden


def test_add_editor_success(client, mock_db, test_user, mock_business):
    """Test successful editor addition"""
    # Set up test user as the business owner
    mock_business.owner = test_user._id
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    # Mock the editor user to be added
    editor_user = User(username="neweditor", password_hash="hash", _id="editor123")
    mock_db.get_user_by_username.side_effect = lambda username: test_user if username == 'testuser' else editor_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {'username': 'neweditor'}
    response = client.post('/add_editor/test-business', data=data)
    assert response.status_code == 302  # Redirect to business page
    location = response.headers.get('Location', '')
    assert 'business_page' in location


def test_add_editor_user_not_found(client, mock_db, test_user, mock_business):
    """Test adding editor when user doesn't exist"""
    mock_business.owner = test_user._id
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {'username': 'nonexistent'}
    response = client.post('/add_editor/test-business', data=data)
    assert response.status_code == 302  # Redirect to business page


def test_add_editor_already_editor(client, mock_db, test_user, mock_business):
    """Test adding editor when user is already an editor"""
    mock_business.owner = test_user._id
    mock_business.editors = {"testuser_id", "editor123"}
    
    editor_user = User(username="neweditor", password_hash="hash", _id="editor123")
    mock_db.get_user_by_username.side_effect = lambda username: test_user if username == 'testuser' else editor_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {'username': 'neweditor'}
    response = client.post('/add_editor/test-business', data=data)
    assert response.status_code == 302  # Redirect to business page


def test_remove_editor_page_requires_login(client):
    """Test that remove editor page redirects to login when user is not logged in"""
    response = client.post('/remove_editor/test-business')
    assert response.status_code == 302  # Redirect status code
    location = response.headers.get('Location', '')
    assert 'login' in location.lower()


def test_remove_editor_only_owner_can_remove(client, mock_db, test_user, mock_business):
    """Test that only the business owner can remove editors"""
    # Set up a different user as the business owner
    owner_user = User(username="owner", password_hash="hash", _id="owner123")
    mock_business.owner = "owner123"
    
    mock_db.get_user_by_username.return_value = test_user  # Current user is not owner
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {'editor_id': 'editor123'}
    response = client.post('/remove_editor/test-business', data=data)
    assert response.status_code == 403  # Forbidden


def test_remove_editor_success(client, mock_db, test_user, mock_business):
    """Test successful editor removal"""
    mock_business.owner = test_user._id
    mock_business.editors = {"testuser_id", "editor123"}
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    # Mock the editor user to be removed
    editor_user = User(username="editor", password_hash="hash", _id="editor123")
    mock_db.get_user_by_id.return_value = editor_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {'editor_id': 'editor123'}
    response = client.post('/remove_editor/test-business', data=data)
    assert response.status_code == 302  # Redirect to business page
    location = response.headers.get('Location', '')
    assert 'business_page' in location


def test_remove_editor_cannot_remove_owner(client, mock_db, test_user, mock_business):
    """Test that owner cannot be removed as editor"""
    mock_business.owner = test_user._id
    mock_business.editors = {"testuser_id"}
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {'editor_id': test_user._id}  # Try to remove owner
    response = client.post('/remove_editor/test-business', data=data)
    assert response.status_code == 302  # Redirect to business page


def test_business_page_shows_editor_management_for_owner(client, mock_db, test_user, mock_business):
    """Test that business page shows editor management section for owner"""
    mock_business.owner = test_user._id
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business')
    assert response.status_code == 200
    assert b'Manage Editors' in response.data
    assert b'Add Editor' in response.data


def test_business_page_hides_editor_management_for_non_owner(client, mock_db, test_user, mock_business):
    """Test that business page hides editor management section for non-owners"""
    mock_business.owner = "owner123"  # Different owner
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business')
    assert response.status_code == 200
    assert b'Manage Editors' not in response.data
    assert b'Add Editor' not in response.data 
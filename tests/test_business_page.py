import pytest
from website.web.models import User, Business, File, Plot
from unittest.mock import MagicMock


def test_upload_files_button_redirects_to_upload_page(client, mock_db, mock_business):
    """Test that Upload Files button links to upload page"""
    # Mock user data and set up session
    test_user = User(username="testuser", email="test@example.com", password_hash="hashed")
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/upload_files/test-business')
    assert response.status_code == 200
    assert b'Choose Files to Upload' in response.data

def test_business_page_data_correctness(client, mock_db, mock_business):
    """Test that business page displays correct business data"""
    # Mock user data and set up session
    test_user = User(username="alice", email="alice@example.com", password_hash="hashed")
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'alice'
    
    response = client.get('/business_page/test-business')
    assert response.status_code == 200
    assert b'Business 123' in response.data
    assert b'Details' in response.data
    assert b'Plots' in response.data

# ----- Missing Business Page Tests -----

def test_business_page_requires_login(client):
    """Test that business page redirects to login when user is not logged in"""
    response = client.get('/business_page/test-business')
    assert response.status_code == 302  # Redirect status code
    location = response.headers.get('Location', '')
    assert 'login' in location.lower()

def test_business_page_business_not_found(client, mock_db, test_user):
    """Test that 404 is returned when business doesn't exist"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = None
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/nonexistent-business')
    assert response.status_code == 404
    assert b'Business not found' in response.data

def test_business_page_displays_files(client, mock_db, test_user, mock_business):
    """Test that business page displays uploaded files"""
    # Mock files for the business
    mock_file1 = File(business_id="business123", filename="sales.csv", _id="file1")
    mock_file2 = File(business_id="business123", filename="inventory.csv", _id="file2")
    mock_files = [mock_file1, mock_file2]
    
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = test_user
    mock_db.get_files_for_business.return_value = mock_files
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business')
    assert response.status_code == 200
    assert b'sales.csv' in response.data
    assert b'inventory.csv' in response.data

def test_business_page_displays_owner_information(client, mock_db, test_user, mock_business):
    """Test that business page displays owner information correctly"""
    # Mock owner user
    owner_user = User(username="owner_user", email="owner@example.com", password_hash="hash", _id="owner_id")
    mock_business.owner = "owner_id"
    
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.side_effect = lambda user_id: owner_user if user_id == "owner_id" else test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business')
    assert response.status_code == 200
    assert b'owner_user' in response.data

def test_business_page_handles_missing_owner(client, mock_db, test_user, mock_business):
    """Test that business page handles missing owner gracefully"""
    mock_business.owner = "nonexistent_owner_id"
    
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = None  # Owner not found
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business')
    assert response.status_code == 200
    assert b'Unknown User' in response.data

def test_business_page_displays_editor_management_for_owner(client, mock_db, test_user, mock_business):
    """Test that business page shows editor management for business owner"""
    # Set up user as owner with another editor
    mock_business.owner = test_user._id
    mock_business.editors = {test_user._id, "other_editor_id"}  # Add another editor so Remove button appears
    
    # Mock the other editor user
    other_editor = User(username="other_editor", email="other@example.com", password_hash="hash", _id="other_editor_id")
    
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.side_effect = lambda user_id: {
        test_user._id: test_user,
        "other_editor_id": other_editor
    }.get(user_id, test_user)
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business')
    assert response.status_code == 200
    # Check for editor management elements using actual template text
    assert b'Add Editor' in response.data
    assert b'Remove' in response.data  # The button says "Remove", not "Remove Editor"

def test_business_page_hides_editor_management_for_non_owner(client, mock_db, test_user, mock_business):
    """Test that business page hides editor management for non-owners"""
    # Set up user as editor (not owner)
    mock_business.owner = "other_owner_id"
    mock_business.editors = {test_user._id, "other_owner_id"}
    
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business')
    assert response.status_code == 200
    # Check that editor management is NOT present
    assert b'Add Editor' not in response.data
    assert b'Remove' not in response.data

def test_business_page_displays_editor_list(client, mock_db, test_user, mock_business):
    """Test that business page displays list of editors"""
    # Mock editor users
    editor1 = User(username="editor1", email="editor1@example.com", password_hash="hash", _id="editor1_id")
    editor2 = User(username="editor2", email="editor2@example.com", password_hash="hash", _id="editor2_id")
    
    mock_business.owner = test_user._id
    mock_business.editors = {test_user._id, "editor1_id", "editor2_id"}
    
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.side_effect = lambda user_id: {
        test_user._id: test_user,
        "editor1_id": editor1,
        "editor2_id": editor2
    }.get(user_id, test_user)
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business')
    assert response.status_code == 200
    assert b'editor1' in response.data
    assert b'editor2' in response.data

def test_business_page_analyze_button_present_when_files_exist(client, mock_db, test_user, mock_business):
    """Test that analyze button is present when files exist"""
    # Mock files for the business
    mock_file = File(business_id="business123", filename="data.csv", _id="file1")
    mock_files = [mock_file]
    
    mock_business.editors = {test_user._id}  # User must be editor to see the button
    
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = test_user
    mock_db.get_files_for_business.return_value = mock_files
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business')
    assert response.status_code == 200
    assert b'Analyze Data' in response.data  # The button says "Analyze Data", not "Analyze My Data"

def test_business_page_edit_plots_button_present_when_plots_exist(client, mock_db, test_user, mock_business):
    """Test that edit plots button is present when plots exist"""
    # Mock plots for the business
    mock_plot = Plot(image_name="Test Plot", image="data", files=[], business_id="business123", _id="plot1", is_presented=True)
    mock_plots = [mock_plot]
    
    mock_business.editors = {test_user._id}  # User must be editor to see the button
    
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = test_user
    mock_db.get_presented_plots_for_business_ordered.return_value = mock_plots
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business')
    assert response.status_code == 200
    assert b'Edit Plots' in response.data

def test_business_page_success_message_display(client, mock_db, test_user, mock_business):
    """Test that success messages are displayed when redirected with success parameter"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business?success=changes_saved')
    assert response.status_code == 200
    assert b'showTemporarySuccessMessage' in response.data
    assert b'changes_saved' in response.data

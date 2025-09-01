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

def test_edit_business_details_post_fails_for_non_editor(client, mock_db, test_user, mock_business):
    """
    Test that a POST request to edit business details fails for a non-editor user
    """
    # Set up user as non-editor by assigning a different owner
    mock_business.owner = "owner_id_different_from_test_user"
    mock_business.editors = {"other_user_id"}  # Make sure our test user isn't in the editor list

    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {
        'address': 'New Address',
        'phone': '123-4567890',
        'email': 'new@example.com'
    }
    
    response = client.post('/edit_business_details/test-business', data=data)
    
    # We expect a 403 Forbidden status code because the user is not authorized
    assert response.status_code == 403
    assert b'You do not have permission to edit this business' in response.data
    
    # Verify that the database was NOT updated
    mock_db.update_business.assert_not_called()


def test_edit_business_details_empty_form_submission(client, mock_db, test_user, mock_business):
    """Test that empty form submission is handled correctly"""
    # Set up user as editor
    mock_business.editors = {test_user._id}
    mock_business.address = "Old Address"
    mock_business.phone = "Old Phone"
    mock_business.email = "old@example.com"
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.update_business.return_value = True
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    # Submit form with empty fields
    response = client.post('/edit_business_details/test-business', data={
        'address': '',
        'phone': '',
        'email': ''
    })
    
    assert response.status_code == 302  # Redirect
    # Should still call update_business to clear the fields
    mock_db.update_business.assert_called_once()

def test_edit_business_details_partial_update(client, mock_db, test_user, mock_business):
    """Test that only changed fields are updated"""
    # Set up user as editor
    mock_business.editors = {test_user._id}
    # Ensure the business has the expected attributes
    mock_business._id = "business123"  # Ensure _id is set
    mock_business.address = "Old Address"
    mock_business.phone = "1234567890"  # Valid phone format
    mock_business.email = "old@example.com"
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.update_business.return_value = True
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    # Submit form with only address changed (using valid data)
    response = client.post('/edit_business_details/test-business', data={
        'address': 'New Address',
        'phone': '1234567890',  # Same as current
        'email': 'old@example.com'  # Same as current
    })
    
    assert response.status_code == 302  # Redirect
    # Check that it redirects to the business page (not back to the form)
    assert '/business_page/test-business' in response.headers.get('Location', '')
    
    # Should call update_business with only the address change
    mock_db.update_business.assert_called_once()
    call_args = mock_db.update_business.call_args[0]
    assert call_args[1] == {'address': 'New Address'}  # Only address should be updated

def test_edit_business_details_no_changes_skips_update(client, mock_db, test_user, mock_business):
    """Test that no database update occurs when no fields are changed"""
    # Set up user as editor
    mock_business.editors = {test_user._id}
    mock_business.address = "Current Address"
    mock_business.phone = "Current Phone"
    mock_business.email = "current@example.com"
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.update_business.return_value = True
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    # Submit form with same values (no changes)
    response = client.post('/edit_business_details/test-business', data={
        'address': 'Current Address',
        'phone': 'Current Phone',
        'email': 'current@example.com'
    })
    
    assert response.status_code == 302  # Redirect
    # Should NOT call update_business since no changes were made
    mock_db.update_business.assert_not_called()

def test_edit_business_details_validation_errors(client, mock_db, test_user, mock_business):
    """Test that validation errors are handled correctly"""
    # Set up user as editor
    mock_business.editors = {test_user._id}
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    # Submit form with invalid email
    response = client.post('/edit_business_details/test-business', data={
        'address': 'Valid Address',
        'phone': '1234567890',
        'email': 'invalid-email'  # Invalid email format
    })
    
    # Should redirect back to the form due to validation error
    assert response.status_code == 302
    # Should not call update_business due to validation error
    mock_db.update_business.assert_not_called()

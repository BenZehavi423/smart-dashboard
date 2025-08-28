import pytest
from unittest.mock import patch, MagicMock
from website.web.models import Business


def test_new_business_page_requires_login(client):
    """Test that new business page redirects to login when user is not logged in"""
    response = client.get('/new_business')
    assert response.status_code == 302  # Redirect status code
    location = response.headers.get('Location', '')
    assert 'login' in location.lower()


def test_new_business_page_accessible_when_logged_in(client, mock_db, test_user):
    """Test that new business page is accessible when user is logged in"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/new_business')
    assert response.status_code == 200
    assert b'Create New Business' in response.data
    assert b'Business Name' in response.data


def test_new_business_creation_success(client, mock_db, test_user):
    """Test successful business creation"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = None  # No existing business with this name
    mock_db.create_business.return_value = "new_business_id"
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {
        'name': 'Test Business',
        'address': '123 Test Street',
        'phone': '555-1234',
        'email': 'test@business.com'
    }
    
    response = client.post('/new_business', data=data)
    assert response.status_code == 302  # Redirect to business page
    location = response.headers.get('Location', '')
    assert 'business_page' in location
    assert 'Test%20Business' in location  # URL encoded business name


def test_new_business_creation_missing_name(client, mock_db, test_user):
    """Test business creation fails when name is missing"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {
        'address': '123 Test Street',
        'phone': '555-1234',
        'email': 'test@business.com'
    }
    
    response = client.post('/new_business', data=data)
    assert response.status_code == 200
    assert b'Business name is required' in response.data


def test_new_business_creation_duplicate_name(client, mock_db, test_user, mock_business):
    """Test business creation fails when name already exists"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business  # Business with this name exists
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {
        'name': 'Test Business',
        'address': '123 Test Street',
        'phone': '555-1234',
        'email': 'test@business.com'
    }
    
    response = client.post('/new_business', data=data)
    assert response.status_code == 200
    assert b'already exists' in response.data


def test_new_business_creation_with_optional_fields_empty(client, mock_db, test_user):
    """Test business creation with empty optional fields"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = None
    mock_db.create_business.return_value = "new_business_id"
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {
        'name': 'Test Business Only'
    }
    
    response = client.post('/new_business', data=data)
    assert response.status_code == 302  # Redirect to business page
    location = response.headers.get('Location', '')
    assert 'business_page' in location


def test_new_business_form_preserves_data_on_error(client, mock_db, test_user):
    """Test that form data is preserved when validation fails"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {
        'name': 'Test Business',
        'address': '123 Test Street',
        'phone': '555-1234',
        'email': 'test@business.com'
    }
    
    # First, make it fail by having a duplicate name
    mock_db.get_business_by_name.return_value = mock_business = Business(owner="owner123", name="Test Business")
    
    response = client.post('/new_business', data=data)
    assert response.status_code == 200
    assert b'already exists' in response.data
    
    # Check that form data is preserved
    assert b'Test Business' in response.data
    assert b'123 Test Street' in response.data
    assert b'555-1234' in response.data
    assert b'test@business.com' in response.data 
import pytest
from flask import session
from website.web.models import User
import bcrypt

def test_navbar_structure_when_logged_in(client, logged_in_user):
    """Test navbar structure when user is logged in"""
    client.post('/login', data=logged_in_user, follow_redirects=True)
    response = client.get('/profile')
    assert response.status_code == 200
    
    assert b'SmartDashboard' in response.data
    assert b'&#9776;' in response.data

def test_dropdown_menu_items_present(client, logged_in_user):
    """Test that all dropdown menu items are present"""
    client.post('/login', data=logged_in_user, follow_redirects=True)
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'My Profile' in response.data
    assert b'Businesses Search' in response.data
    assert b'New Business' in response.data
    assert b'Log Out' in response.data

def test_current_page_label_different_pages(client, logged_in_user):
    """Test that current page label changes on different pages"""
    client.post('/login', data=logged_in_user, follow_redirects=True)

    response = client.get('/profile')
    assert response.status_code == 200
    assert b'My Profile' in response.data
    
    response = client.get('/businesses_search')
    assert response.status_code == 200
    assert b'Businesses' in response.data

    response = client.get('/new_business')
    assert response.status_code == 200
    assert b'New Business' in response.data
    
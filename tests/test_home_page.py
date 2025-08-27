def test_home_page_elements(client):
    """Test home page has action buttons and images"""
    response = client.get('/')
    assert response.status_code == 200
    
    assert b'images/logo.jpg' in response.data

    assert b'Log In' in response.data
    assert b'Sign Up' in response.data
    
    assert b'Upload.' in response.data
    assert b'Visualize.' in response.data
    assert b'Get Smart Insights.' in response.data

def test_home_page_navbar_structure(client):
    """Test home page navbar structure"""
    response = client.get('/')
    assert response.status_code == 200
    
    assert b'SmartDashboard' in response.data
    # Should not have menu when not logged in
    assert b'&#9776;' not in response.data

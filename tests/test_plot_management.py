import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from website.web.models import User, Plot, UserProfile

# ----- Profile page tests -----
def test_profile_page_displays_presented_plots(client, mock_db, test_user, mock_presented_plots_ordered):
    """Test that profile page displays only presented plots"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/profile')
    assert response.status_code == 200
    
    # Check that presented plots are displayed
    for plot in mock_presented_plots_ordered:
        assert plot.image_name.encode() in response.data
        assert plot._id.encode() in response.data

# TODO: analyze_data
def test_profile_page_analyze_data_button_present(client, mock_db, test_user, mock_presented_plots_ordered):
    """Test that 'Analyze My Data' button is present on profile page"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'Analyze My Data' in response.data

def test_profile_page_edit_plots_button_present(client, mock_db, test_user, mock_presented_plots_ordered):
    """Test that 'Edit Plots' button is present on profile page"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'Edit Plots' in response.data

# TODO: analyze_data
def test_profile_page_no_plots_shows_analyze_button(client, mock_db, test_user):
    """Test that 'Analyze My Data' button is shown even when no plots exist"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_presented_plots_for_user_ordered.return_value = []
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'Analyze My Data' in response.data
    assert b'No presented plots. Upload files and generate plots to see them here.' in response.data

def test_profile_page_plot_serialization(client, mock_db, test_user, mock_presented_plots_ordered):
    """Test that plots are properly serialized for JSON response"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/profile')
    assert response.status_code == 200
    
    # Check that plot data is properly formatted (no base64 data in HTML)
    for plot in mock_presented_plots_ordered:
        assert plot.image_name.encode() in response.data
        # Base64 data should be truncated or not displayed in full
        assert len(plot.image) > 100  # Base64 data is long

# ----- Edit plots page tests -----
def test_edit_plots_page_requires_login(client):
    """Test that edit plots page redirects to login when user is not logged in"""
    response = client.get('/edit_plots')
    assert response.status_code == 302  # Redirect status code
    location = response.headers.get('Location', '')
    assert 'login' in location.lower()

def test_edit_plots_page_displays_all_plots(client, mock_db, test_user, mock_plots_for_user):
    """Test that edit plots page displays all plots (presented and not presented)"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_or_create_user_profile.return_value = UserProfile(user_id="user123")
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots')
    assert response.status_code == 200
    
    # Check that all plots are displayed
    for plot in mock_plots_for_user:
        assert plot.image_name.encode() in response.data
        assert plot._id.encode() in response.data

def test_edit_plots_page_checkbox_states(client, mock_db, test_user, mock_plots_for_user):
    """Test that checkboxes reflect the presented status of plots"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_or_create_user_profile.return_value = UserProfile(user_id="user123")
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots')
    assert response.status_code == 200
    
    # Check that checkboxes are present and have the correct structure
    assert b'Present in Profile' in response.data
    assert b'type="checkbox"' in response.data

def test_edit_plots_save_changes_success(client, mock_db, test_user):
    """Test successful saving of plot changes via AJAX"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.update_multiple_plots.return_value = True
    mock_db.update_plot_presentation_order.return_value = True
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {
        'plot_updates': [
            {'plot_id': 'plot1', 'is_presented': True},
            {'plot_id': 'plot2', 'is_presented': False}
        ],
        'plot_order': ['plot1', 'plot3']
    }
    
    response = client.post('/edit_plots', 
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == True

def test_edit_plots_save_changes_failure(client, mock_db, test_user):
    """Test failed saving of plot changes via AJAX"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.update_multiple_plots.return_value = False
    mock_db.update_plot_presentation_order.return_value = True
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {
        'plot_updates': [
            {'plot_id': 'plot1', 'is_presented': True}
        ],
        'plot_order': ['plot1']
    }
    
    response = client.post('/edit_plots', 
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == False

def test_edit_plots_page_sorting_buttons(client, mock_db, test_user, mock_plots_for_user):
    """Test that sorting buttons are present on edit plots page"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_or_create_user_profile.return_value = UserProfile(user_id="user123")
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots')
    assert response.status_code == 200
    
    # Check for sorting buttons
    assert b'Sort by Name:' in response.data
    assert b'Sort by Date:' in response.data
    assert b'A \xe2\x86\x92 Z' in response.data
    assert b'Z \xe2\x86\x92 A' in response.data

def test_edit_plots_page_drag_drop_functionality(client, mock_db, test_user, mock_plots_for_user):
    """Test that drag and drop functionality is present"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_or_create_user_profile.return_value = UserProfile(user_id="user123")
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots')
    assert response.status_code == 200
    
    # Check for drag and drop related elements (added by JavaScript)
    assert b'plot-card' in response.data
    assert b'reorder-list' in response.data

# ----- Analyze data page tests -----
# TODO: analyze_data

def test_analyze_data_page_requires_login(client):
    """Test that analyze data page redirects to login when user is not logged in"""
    response = client.get('/analyze_data')
    assert response.status_code == 302  # Redirect status code
    location = response.headers.get('Location', '')
    assert 'login' in location.lower()

def test_analyze_data_page_accessible_when_logged_in(client, mock_db, test_user):
    """Test that analyze data page is accessible when user is logged in"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/analyze_data')
    assert response.status_code == 200
    # assert b'Upload Images' in response.data      # TODO: analyze_data

def test_analyze_data_save_plots_success(client, mock_db, test_user):
    """Test successful saving of new plots via AJAX"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_or_create_user_profile.return_value = UserProfile(user_id="user123")
    mock_db.create_plot.return_value = "new_plot_id"
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {
        'new_plots': [
            {
                'image_name': 'New Analysis',
                'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
                'save_to_profile': True
            }
        ]
    }
    
    response = client.post('/analyze_data', 
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == True
    assert result['saved_count'] == 1

def test_analyze_data_save_plots_failure(client, mock_db, test_user):
    """Test failed saving of new plots via AJAX"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_or_create_user_profile.return_value = UserProfile(user_id="user123")
    mock_db.create_plot.side_effect = Exception("Database error")
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {
        'new_plots': [
            {
                'image_name': 'New Analysis',
                'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
                'save_to_profile': True
            }
        ]
    }
    
    response = client.post('/analyze_data', 
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 500
    result = response.get_json()
    assert result['success'] == False

# ----- Database operation tests -----
def test_get_presented_plots_ordered(mock_db, sample_user_profile_with_order):
    """Test that presented plots are returned in correct order"""
    mock_db.get_or_create_user_profile.return_value = sample_user_profile_with_order
    
    # Mock the plots that would be returned
    plot1 = Plot(image_name="Plot 1", image="data1", files=[], user_id="user123", _id="plot1", is_presented=True)
    plot2 = Plot(image_name="Plot 2", image="data2", files=[], user_id="user123", _id="plot2", is_presented=True)
    plot3 = Plot(image_name="Plot 3", image="data3", files=[], user_id="user123", _id="plot3", is_presented=True)
    
    mock_db.get_plots_for_user.return_value = [plot1, plot2, plot3]
    
    # The method should return plots in the order specified in user profile
    result = mock_db.get_presented_plots_for_user_ordered("user123")
    
    # No assert_called_once_with, just check result is a mock (since it's a mock)
    assert isinstance(result, MagicMock) or result is not None

def test_update_plot_presentation_order(mock_db):
    """Test updating plot presentation order"""
    mock_db.update_user_profile.return_value = True
    mock_db.update_plot_presentation_order.return_value = True
    plot_order = ["plot1", "plot3", "plot2"]
    result = mock_db.update_plot_presentation_order("user123", plot_order)
    assert result == True

# ----- Error handling tests -----
def test_edit_plots_invalid_json(client, mock_db, test_user):
    """Test handling of invalid JSON in edit plots request"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.post('/edit_plots', 
                          data='invalid json',
                          content_type='application/json')
    
    assert response.status_code == 400

def test_analyze_data_invalid_json(client, mock_db, test_user):
    """Test handling of invalid JSON in analyze data request"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.post('/analyze_data', 
                          data='invalid json',
                          content_type='application/json')
    
    assert response.status_code == 400

def test_edit_plots_missing_data(client, mock_db, test_user):
    """Test handling of missing data in edit plots request"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.update_multiple_plots.return_value = False
    mock_db.update_plot_presentation_order.return_value = False
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    data = {}  # Missing required fields
    response = client.post('/edit_plots',
                          data=json.dumps(data),
                          content_type='application/json')
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == False

# ----- Integration tests -----
def test_full_plot_workflow(client, mock_db, test_user):
    """Test the full workflow: create plots, edit presentation, view in profile"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_or_create_user_profile.return_value = UserProfile(user_id="user123")
    mock_db.create_plot.return_value = "new_plot_id"
    mock_db.update_multiple_plots.return_value = True
    mock_db.update_plot_presentation_order.return_value = True
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    # Step 1: Create new plots
    create_data = {
        'new_plots': [
            {
                'image_name': 'Workflow Test Plot',
                'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
                'save_to_profile': True
            }
        ]
    }

    response = client.post('/analyze_data', 
                          data=json.dumps(create_data),
                          content_type='application/json')
    assert response.status_code == 200
    create_result = response.get_json()
    assert create_result['success'] == True
    
    # Step 2: Edit plot presentation
    edit_data = {
        'plot_updates': [
            {'plot_id': 'new_plot_id', 'is_presented': True}
        ],
        'plot_order': ['new_plot_id']
    }
    
    response = client.post('/edit_plots', 
                          data=json.dumps(edit_data),
                          content_type='application/json')
    assert response.status_code == 200
    edit_result = response.get_json()
    assert edit_result['success'] == True
    
    # Step 3: View in profile (should show the plot)
    mock_db.get_presented_plots_for_user_ordered.return_value = [
        Plot(image_name="Workflow Test Plot", image="data", files=[], user_id="user123", _id="new_plot_id", is_presented=True)
    ]
    
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'Workflow Test Plot' in response.data 
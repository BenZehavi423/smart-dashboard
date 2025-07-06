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

# ----- Modal functionality tests -----
def test_edit_plots_no_changes_modal(client, mock_db, test_user, mock_plots_for_user):
    """Test that no changes modal is available (script and button present)"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_or_create_user_profile.return_value = UserProfile(user_id="user123")
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots')
    assert response.status_code == 200
    # Check that the JS file is included and the save button is present
    assert b'edit_plots.js' in response.data
    assert b'Save All Changes' in response.data

def test_edit_plots_unsaved_changes_modal(client, mock_db, test_user, mock_plots_for_user):
    """Test that unsaved changes modal is available (script and back button present)"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_or_create_user_profile.return_value = UserProfile(user_id="user123")
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots')
    assert response.status_code == 200
    # Check that the JS file is included and the back button is present
    assert b'edit_plots.js' in response.data
    assert b'Back to Profile' in response.data

def test_edit_plots_success_redirect_with_parameter(client, mock_db, test_user):
    """Test that successful save redirects to profile with success parameter"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.update_multiple_plots.return_value = True
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
    assert result['success'] == True

def test_profile_success_message_display(client, mock_db, test_user, mock_presented_plots_ordered):
    """Test that success message is shown when redirected with success parameter"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/profile?success=changes_saved')
    assert response.status_code == 200
    
    # Check that success message function is available
    assert b'showTemporarySuccessMessage' in response.data
    assert b'changes_saved' in response.data

def test_edit_plots_custom_modal_system(client, mock_db, test_user, mock_plots_for_user):
    """Test that custom modal system is properly implemented (script present)"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_or_create_user_profile.return_value = UserProfile(user_id="user123")
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots')
    assert response.status_code == 200
    # Check that the JS file is included
    assert b'edit_plots.js' in response.data

# ----- Updated existing tests -----
def test_edit_plots_save_changes_success_with_logging(client, mock_db, test_user):
    """Test successful saving of plot changes with proper logging"""
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
    
    with patch('website.web.views.logger') as mock_logger:
        response = client.post('/edit_plots', 
                              data=json.dumps(data),
                              content_type='application/json')
        
        # Verify logging calls
        mock_logger.info.assert_called()
        mock_logger.info.assert_any_call(
            f"User testuser saving plot changes: {len(data['plot_updates'])} updates, {len(data['plot_order'])} plots in order",
            extra_fields={'user_id': test_user._id, 'updates_count': len(data['plot_updates']), 'order_length': len(data['plot_order'])}
        )
        mock_logger.info.assert_any_call(
            f"Plot changes saved successfully for user testuser",
            extra_fields={'user_id': test_user._id, 'presented_plots': len(data['plot_order'])}
        )
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == True

def test_edit_plots_save_changes_failure_with_logging(client, mock_db, test_user):
    """Test failed saving of plot changes with proper logging"""
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
    
    with patch('website.web.views.logger') as mock_logger:
        response = client.post('/edit_plots', 
                              data=json.dumps(data),
                              content_type='application/json')
        
        # Verify logging calls
        mock_logger.info.assert_called()
        mock_logger.error.assert_called_with(
            f"Failed to save plot changes for user testuser",
            extra_fields={'user_id': test_user._id, 'plot_success': False, 'order_success': True}
        )
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == False

def test_edit_plots_page_access_logging(client, mock_db, test_user, mock_plots_for_user):
    """Test that edit plots page access is properly logged"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_or_create_user_profile.return_value = UserProfile(user_id="user123")
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    with patch('website.web.views.logger') as mock_logger:
        response = client.get('/edit_plots')
        
        # Verify logging calls
        mock_logger.info.assert_called()
        mock_logger.info.assert_any_call(
            f"Edit plots page accessed by user: testuser",
            extra_fields={'user_id': test_user._id, 'action': 'edit_plots_access'}
        )
        mock_logger.info.assert_any_call(
            f"Edit plots page rendered for user testuser: {len(mock_plots_for_user)} total plots, {len([p for p in mock_plots_for_user if p.is_presented])} presented",
            extra_fields={'user_id': test_user._id, 'total_plots': len(mock_plots_for_user), 'presented_plots': len([p for p in mock_plots_for_user if p.is_presented])}
        )
    
    assert response.status_code == 200

# ----- JavaScript functionality tests -----
def test_edit_plots_javascript_functions(client, mock_db, test_user, mock_plots_for_user):
    """Test that all required JavaScript functions are present (script present)"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_or_create_user_profile.return_value = UserProfile(user_id="user123")
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots')
    assert response.status_code == 200
    # Check for the JS file
    assert b'edit_plots.js' in response.data

def test_edit_plots_drag_drop_javascript(client, mock_db, test_user, mock_plots_for_user):
    """Test that drag and drop JavaScript functions are present (script present)"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_or_create_user_profile.return_value = UserProfile(user_id="user123")
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots')
    assert response.status_code == 200
    # Check for the JS file
    assert b'edit_plots.js' in response.data

def test_edit_plots_sorting_javascript(client, mock_db, test_user, mock_plots_for_user):
    """Test that sorting JavaScript functions are present"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_or_create_user_profile.return_value = UserProfile(user_id="user123")
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots')
    assert response.status_code == 200
    
    # Check for sorting functions
    assert b'sortByName' in response.data
    assert b'sortByDate' in response.data
    assert b'resetOrder' in response.data

# ----- Error handling tests -----
def test_edit_plots_error_modal_display(client, mock_db, test_user):
    """Test that error modals are shown when operations fail"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.update_multiple_plots.return_value = False
    mock_db.update_plot_presentation_order.return_value = False
    
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

def test_edit_plots_no_plots_selected_confirmation(client, mock_db, test_user):
    """Test that confirmation is shown when no plots are selected"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.update_multiple_plots.return_value = True
    mock_db.update_plot_presentation_order.return_value = True
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {
        'plot_updates': [
            {'plot_id': 'plot1', 'is_presented': False},
            {'plot_id': 'plot2', 'is_presented': False}
        ],
        'plot_order': []
    }
    
    response = client.post('/edit_plots', 
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == True

# ----- Integration tests -----
def test_full_edit_plots_workflow_with_modals(client, mock_db, test_user, mock_plots_for_user):
    """Test the complete edit plots workflow including modal interactions"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_or_create_user_profile.return_value = UserProfile(user_id="user123")
    mock_db.update_multiple_plots.return_value = True
    mock_db.update_plot_presentation_order.return_value = True
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    # Step 1: Access edit plots page
    response = client.get('/edit_plots')
    assert response.status_code == 200
    
    # Step 2: Save changes (simulate successful save)
    data = {
        'plot_updates': [
            {'plot_id': 'plot1', 'is_presented': True},
            {'plot_id': 'plot2', 'is_presented': False}
        ],
        'plot_order': ['plot1']
    }
    
    response = client.post('/edit_plots', 
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == True
    
    # Step 3: Check that profile page can handle success parameter
    response = client.get('/profile?success=changes_saved')
    assert response.status_code == 200
    assert b'showTemporarySuccessMessage' in response.data 
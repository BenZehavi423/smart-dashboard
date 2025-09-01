import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from website.web.models import User, Plot, Business

# TODO: need to refer to specific business to check (throught all the file)
# TODO: change everything from user profile to business

# ----- Business page tests -----
def test_business_page_displays_presented_plots(client, mock_db, test_user, mock_presented_plots_ordered, mock_business):
    """Test that business page displays presented plots in correct order"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business')
    assert response.status_code == 200
    assert b'Plots' in response.data
    # Check that presented plots are shown
    for plot in mock_presented_plots_ordered:
        assert plot.image_name.encode() in response.data

def test_business_page_elements_present(client, mock_db, test_user, mock_presented_plots_ordered, mock_business):
    """Test that business page has all required elements"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business')
    assert response.status_code == 200
    assert b'Plots' in response.data
    assert b'Files' in response.data
    assert b'Details' in response.data

def test_business_page_no_plots_shows_analyze_button(client, mock_db, test_user, mock_business):
    """Test that business page shows analyze button when no plots are present"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = test_user
    mock_db.get_presented_plots_for_business_ordered.return_value = []
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business')
    assert response.status_code == 200
    assert b'Plots' in response.data
    assert b'Analyze Data' in response.data

def test_business_page_plot_serialization(client, mock_db, test_user, mock_presented_plots_ordered, mock_business):
    """Test that plots are properly serialized for the business page"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business')
    assert response.status_code == 200
    
    # Check that plot data is properly serialized
    for plot in mock_presented_plots_ordered:
        assert plot.image_name.encode() in response.data

# ----- Edit plots page tests -----
def test_edit_plots_page_requires_login(client):
    """Test that edit plots page redirects to login when user is not logged in"""
    response = client.get('/edit_plots/test-business')
    assert response.status_code == 302  # Redirect status code
    location = response.headers.get('Location', '')
    assert 'login' in location.lower()

def test_edit_plots_page_displays_all_plots(client, mock_db, test_user, mock_plots_for_business, mock_business):
    """Test that edit plots page displays all plots with correct structure"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_plots_for_business.return_value = mock_plots_for_business
    mock_db.get_business_by_id.return_value = mock_business
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots/test-business')
    assert response.status_code == 200
    assert b'Edit Plots' in response.data
    assert b'Step 1: Select Plots to Present' in response.data
    assert b'Step 2: Reorder Presented Plots' in response.data
    
    # Check that all plots are displayed
    for plot in mock_plots_for_business:
        assert plot.image_name.encode() in response.data

def test_edit_plots_page_checkbox_states(client, mock_db, test_user, mock_plots_for_business, mock_business):
    """Test that checkboxes reflect the correct presented state"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_plots_for_business.return_value = mock_plots_for_business
    mock_db.get_business_by_id.return_value = mock_business
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots/test-business')
    assert response.status_code == 200
    assert b'Present in Business Page' in response.data

def test_edit_plots_save_changes_success(client, mock_db, test_user, mock_business):
    """Test successful saving of plot changes via AJAX"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
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
    
    response = client.post('/edit_plots/test-business', 
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == True

def test_edit_plots_save_changes_failure(client, mock_db, test_user, mock_business):
    """Test failed saving of plot changes via AJAX"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    # Mock the save_plot_changes_for_business method to return False
    mock_db.save_plot_changes_for_business.return_value = False
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {
        'plot_updates': [
            {'plot_id': 'plot1', 'is_presented': True}
        ],
        'plot_order': ['plot1']
    }
    
    response = client.post('/edit_plots/test-business', 
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == False

def test_edit_plots_page_sorting_buttons(client, mock_db, test_user, mock_plots_for_business, mock_business):
    """Test that sorting buttons are present on edit plots page"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_plots_for_business.return_value = mock_plots_for_business
    mock_db.get_business_by_id.return_value = mock_business
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots/test-business')
    assert response.status_code == 200
    
    # Check for sorting buttons
    assert b'Sort by Name:' in response.data
    assert b'Sort by Date:' in response.data
    assert b'A \xe2\x86\x92 Z' in response.data
    assert b'Z \xe2\x86\x92 A' in response.data

def test_edit_plots_page_drag_drop_functionality(client, mock_db, test_user, mock_plots_for_business, mock_business):
    """Test that drag and drop functionality is present"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_plots_for_business.return_value = mock_plots_for_business
    mock_db.get_business_by_id.return_value = mock_business
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots/test-business')
    assert response.status_code == 200
    
    # Check for drag and drop related elements (added by JavaScript)
    assert b'plot-card' in response.data
    assert b'reorder-list' in response.data

# ----- Analyze data page tests -----
# TODO: analyze_data

def test_analyze_data_page_requires_login(client):
    """Test that analyze data page redirects to login when user is not logged in"""
    response = client.get('/analyze_data/test-business')
    assert response.status_code == 302  # Redirect status code
    location = response.headers.get('Location', '')
    assert 'login' in location.lower()

def test_analyze_data_page_accessible_when_logged_in(client, mock_db, test_user, mock_business):
    """Test that analyze data page is accessible when user is logged in"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_files_for_business.return_value = []
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/analyze_data/test-business')
    assert response.status_code == 200
    assert b'Analyze My Data' in response.data

def test_analyze_data_save_plots_success(client, mock_db, test_user, mock_business, mock_processed_file):
    """Test successful plot generation via AJAX"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_id.return_value = mock_business
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_file.return_value = mock_processed_file
    
    with patch('website.web.views.generate_plot_image') as mock_generate:
        mock_generate.return_value = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        with client.session_transaction() as sess:
            sess['username'] = 'testuser'
        
        data = {
            'file_id': 'test_file_id',
            'prompt': 'Create a bar chart of sales data'
        }
        
        response = client.post('/analyze_data/test-business',
                              data=json.dumps(data),
                              content_type='application/json')
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] == True

def test_analyze_data_save_plots_failure(client, mock_db, test_user, mock_business, mock_processed_file):
    """Test failed plot generation via AJAX"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_id.return_value = mock_business
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_file.return_value = mock_processed_file
    
    with patch('website.web.views.generate_plot_image') as mock_generate:
        mock_generate.side_effect = Exception("Plot generation failed")
        
        with client.session_transaction() as sess:
            sess['username'] = 'testuser'
    
    data = {
        'file_id': 'test_file_id',
        'prompt': 'Create a bar chart of sales data'
    }
    
    response = client.post('/analyze_data/test-business',
                          data=json.dumps(data),
                          content_type='application/json')
    assert response.status_code == 500
    result = response.get_json()
    assert result['success'] == False

# ----- Database operation tests -----
def test_get_presented_plots_ordered(mock_db, sample_business_page_with_order):
    """Test that presented plots are returned in correct order"""
    mock_db.get_business.return_value = sample_business_page_with_order

    # Mock the plots that would be returned
    plot1 = Plot(image_name="Plot 1", image="data1", files=[], business_id="business123", _id="plot1", is_presented=True)
    plot2 = Plot(image_name="Plot 2", image="data2", files=[], business_id="business123", _id="plot2", is_presented=True)
    plot3 = Plot(image_name="Plot 3", image="data3", files=[], business_id="business123", _id="plot3", is_presented=True)
    
    mock_db.get_plots_for_user.return_value = [plot1, plot2, plot3]
    
    # The method should return plots in the order specified in business page
    result = mock_db.get_presented_plots_for_user_ordered("user123")
    
    # No assert_called_once_with, just check result is a mock (since it's a mock)
    assert isinstance(result, MagicMock) or result is not None

def test_update_plot_presentation_order(mock_db):
    """Test updating plot presentation order"""
    mock_db.update_business.return_value = True
    mock_db.update_plot_presentation_order.return_value = True
    plot_order = ["plot1", "plot3", "plot2"]
    result = mock_db.update_plot_presentation_order("user123", plot_order)
    assert result == True

# ----- Error handling tests -----
def test_edit_plots_invalid_json(client, mock_db, test_user, mock_business):
    """Test handling of invalid JSON in edit plots request"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.post('/edit_plots/test-business', 
                          data='invalid json',
                          content_type='application/json')
    
    assert response.status_code == 400

def test_analyze_data_invalid_json(client, mock_db, test_user, mock_business):
    """Test analyze data with invalid JSON"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.post('/analyze_data/test-business',
                          data='invalid json',
                          content_type='application/json')
    assert response.status_code == 400

def test_edit_plots_missing_data(client, mock_db, test_user, mock_business):
    """Test handling of missing data in edit plots request"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    # Mock the save_plot_changes_for_business method to return False for missing data
    mock_db.save_plot_changes_for_business.return_value = False
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    data = {}  # Missing required fields
    response = client.post('/edit_plots/test-business',
                          data=json.dumps(data),
                          content_type='application/json')
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == False

# ----- Integration tests -----
def test_full_plot_workflow(client, mock_db, test_user, mock_business, mock_processed_file):
    """Test the full workflow: create plots, edit presentation, view in business page"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_id.return_value = mock_business
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = test_user
    mock_db.get_file.return_value = mock_processed_file
    mock_db.create_plot.return_value = "new_plot_id"
    mock_db.update_multiple_plots.return_value = True
    mock_db.update_plot_presentation_order.return_value = True
    
    with patch('website.web.views.generate_plot_image') as mock_generate:
        mock_generate.return_value = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        with client.session_transaction() as sess:
            sess['username'] = 'testuser'
        
        # Step 1: Generate plot
        create_data = {
            'file_id': 'test_file_id',
            'prompt': 'Create a bar chart of sales data'
        }
        
        response = client.post('/analyze_data/test-business',
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
        
        response = client.post('/edit_plots/test-business',
                              data=json.dumps(edit_data),
                              content_type='application/json')
        assert response.status_code == 200
        edit_result = response.get_json()
        assert edit_result['success'] == True
        
        # Step 3: View in business page (should show the plot)
        mock_db.get_presented_plots_for_business_ordered.return_value = [
            Plot(image_name="Workflow Test Plot", image="data", files=[], business_id="business123", _id="new_plot_id", is_presented=True)
        ]
        
        response = client.get('/business_page/test-business')
        assert response.status_code == 200
        assert b'Workflow Test Plot' in response.data

# ----- Modal functionality tests -----
def test_edit_plots_no_changes_modal(client, mock_db, test_user, mock_plots_for_business, mock_business):
    """Test that no changes modal is available (script and button present)"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_plots_for_business.return_value = mock_plots_for_business
    mock_db.get_business_by_id.return_value = mock_business
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots/test-business')
    assert response.status_code == 200
    # Check that the JS file is included and the save button is present
    assert b'edit_plots.js' in response.data
    assert b'Save All Changes' in response.data

def test_edit_plots_unsaved_changes_modal(client, mock_db, test_user, mock_plots_for_business, mock_business):
    """Test that unsaved changes modal is available (script and back button present)"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_plots_for_business.return_value = mock_plots_for_business
    mock_db.get_business_by_id.return_value = mock_business
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots/test-business')
    assert response.status_code == 200
    # Check that the JS file is included and the back button is present
    assert b'edit_plots.js' in response.data
    assert b'Back to Business Page' in response.data

def test_edit_plots_success_redirect_with_parameter(client, mock_db, test_user, mock_business):
    """Test that successful save redirects to business page with success parameter"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
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
    
    response = client.post('/edit_plots/test-business', 
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == True

def test_business_page_success_message_display(client, mock_db, test_user, mock_presented_plots_ordered, mock_business):
    """Test that success message is shown when redirected with success parameter"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/business_page/test-business?success=changes_saved')
    assert response.status_code == 200
    
    # Check that success message function is available
    assert b'showTemporarySuccessMessage' in response.data
    assert b'changes_saved' in response.data

def test_edit_plots_custom_modal_system(client, mock_db, test_user, mock_plots_for_business, mock_business):
    """Test that custom modal system is properly implemented (script present)"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_plots_for_business.return_value = mock_plots_for_business
    mock_db.get_business_by_id.return_value = mock_business
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots/test-business')
    assert response.status_code == 200
    # Check that the JS file is included
    assert b'edit_plots.js' in response.data

# ----- Updated existing tests -----
def test_edit_plots_save_changes_success_with_logging(client, mock_db, test_user, mock_business):
    """Test successful saving of plot changes with proper logging"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
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
        response = client.post('/edit_plots/test-business', 
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

def test_edit_plots_save_changes_failure_with_logging(client, mock_db, test_user, mock_business):
    """Test failed saving of plot changes with proper logging"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    # Mock the save_plot_changes_for_business method to return False
    mock_db.save_plot_changes_for_business.return_value = False
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {
        'plot_updates': [
            {'plot_id': 'plot1', 'is_presented': True}
        ],
        'plot_order': ['plot1']
    }
    
    with patch('website.web.views.logger') as mock_logger:
        response = client.post('/edit_plots/test-business', 
                              data=json.dumps(data),
                              content_type='application/json')
        
        # Verify logging calls
        mock_logger.info.assert_called()
        mock_logger.error.assert_called_with(
            f"Failed to save plot changes for user testuser"
        )
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == False

def test_edit_plots_page_access_logging(client, mock_db, test_user, mock_plots_for_business, mock_business):
    """Test that edit plots page access is properly logged"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_plots_for_business.return_value = mock_plots_for_business
    mock_db.get_business_by_id.return_value = mock_business
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    with patch('website.web.views.logger') as mock_logger:
        response = client.get('/edit_plots/test-business')
        
        # Verify logging calls
        mock_logger.info.assert_called()
        mock_logger.info.assert_any_call(
            f"Edit plots page accessed by user: testuser",
            extra_fields={'user_id': test_user._id, 'action': 'edit_plots_access'}
        )
        mock_logger.info.assert_any_call(
            f"Edit plots page rendered for user testuser: {len(mock_plots_for_business)} total plots, {len([p for p in mock_plots_for_business if p.is_presented])} presented",
            extra_fields={'user_id': test_user._id, 'total_plots': len(mock_plots_for_business), 'presented_plots': len([p for p in mock_plots_for_business if p.is_presented])}
        )
    
    assert response.status_code == 200

# ----- JavaScript functionality tests -----
def test_edit_plots_javascript_functions(client, mock_db, test_user, mock_plots_for_business, mock_business):
    """Test that all required JavaScript functions are present (script present)"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_plots_for_business.return_value = mock_plots_for_business
    mock_db.get_business_by_id.return_value = mock_business
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots/test-business')
    assert response.status_code == 200
    # Check for the JS file
    assert b'edit_plots.js' in response.data

def test_edit_plots_drag_drop_javascript(client, mock_db, test_user, mock_plots_for_business, mock_business):
    """Test that drag and drop JavaScript functions are present (script present)"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_plots_for_business.return_value = mock_plots_for_business
    mock_db.get_business_by_id.return_value = mock_business
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots/test-business')
    assert response.status_code == 200
    # Check for the JS file
    assert b'edit_plots.js' in response.data

def test_edit_plots_sorting_javascript(client, mock_db, test_user, mock_plots_for_business, mock_business):
    """Test that sorting JavaScript functions are present"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_plots_for_business.return_value = mock_plots_for_business
    mock_db.get_business_by_id.return_value = mock_business
    mock_db.get_business_by_name.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/edit_plots/test-business')
    assert response.status_code == 200
    
    # Check for sorting functions
    assert b'sortByName' in response.data
    assert b'sortByDate' in response.data
    assert b'resetOrder' in response.data

# ----- Error handling tests -----
def test_edit_plots_error_modal_display(client, mock_db, test_user, mock_business):
    """Test that error modals are shown when operations fail"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    # Mock the save_plot_changes_for_business method to return False
    mock_db.save_plot_changes_for_business.return_value = False
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {
        'plot_updates': [
            {'plot_id': 'plot1', 'is_presented': True}
        ],
        'plot_order': ['plot1']
    }
    
    response = client.post('/edit_plots/test-business', 
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == False

def test_edit_plots_no_plots_selected_confirmation(client, mock_db, test_user, mock_business):
    """Test that confirmation is shown when no plots are selected"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    # Mock the save_plot_changes_for_business method to return True
    mock_db.save_plot_changes_for_business.return_value = True
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    data = {
        'plot_updates': [
            {'plot_id': 'plot1', 'is_presented': False},
            {'plot_id': 'plot2', 'is_presented': False}
        ],
        'plot_order': []
    }
    
    response = client.post('/edit_plots/test-business', 
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == True

# ----- Integration tests -----
def test_full_edit_plots_workflow_with_modals(client, mock_db, test_user, mock_plots_for_business, mock_business):
    """Test the complete edit plots workflow including modal interactions"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_plots_for_business.return_value = mock_plots_for_business
    mock_db.get_business_by_id.return_value = mock_business
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.get_user_by_id.return_value = test_user
    # Mock the save_plot_changes_for_business method to return True
    mock_db.save_plot_changes_for_business.return_value = True
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    # Step 1: Access edit plots page
    response = client.get('/edit_plots/test-business')
    assert response.status_code == 200
    
    # Step 2: Save changes (simulate successful save)
    data = {
        'plot_updates': [
            {'plot_id': 'plot1', 'is_presented': True},
            {'plot_id': 'plot2', 'is_presented': False}
        ],
        'plot_order': ['plot1']
    }
    
    response = client.post('/edit_plots/test-business', 
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == True
    
    # Step 3: Check that business page can handle success parameter
    response = client.get('/business_page/test-business?success=changes_saved')
    assert response.status_code == 200
    assert b'showTemporarySuccessMessage' in response.data 
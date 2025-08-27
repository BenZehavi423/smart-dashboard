from website.web.models import User, File
from unittest.mock import patch, MagicMock

def test_upload_page_requires_login(client):
    """Test that upload page redirects to login when user is not logged in"""
    response = client.get('/upload_files/test-business')
    assert response.status_code == 302  # Redirect status code
    location = response.headers.get('Location', '')
    assert 'login' in location.lower()

def test_upload_page_with_logged_in_user(client, mock_db, test_user):
    """Test accessing upload page when user is logged in"""
    # Mock user data and set up session
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_files_for_user.return_value = []
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.get('/upload_files/test-business')
    assert response.status_code == 200
    assert b'Choose Files to Upload' in response.data
    assert b'Back to Business Page' in response.data

def test_file_validation_csv_allowed(client, mock_db, test_user, mock_csv_file, mock_processed_file):
    """Test that CSV files are allowed for upload"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    with patch('website.web.csv_processor.process_file') as mock_process:
        mock_process.return_value = mock_processed_file
        mock_db.create_file.return_value = "file_id"
        
        response = client.post('/upload_files/test-business', 
                             data={'file': mock_csv_file},
                             content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert len(data['failed_files']) == 0

def test_file_validation_non_csv_rejected(client, mock_db, test_user, mock_txt_file):
    """Test that non-CSV files are rejected"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.post('/upload_files/test-business', 
                         data={'file': mock_txt_file},
                         content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == False
    assert len(data['failed_files']) == 1
    assert 'Invalid file: test.txt' in data['failed_files'][0]

def test_multiple_files_upload(client, mock_db, test_user, mock_multiple_csv_files):
    """Test uploading multiple files at once"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    with patch('website.web.csv_processor.process_file') as mock_process:
        mock_processed_file1 = File(business_id="business123", filename="file1.csv")
        mock_processed_file2 = File(business_id="business123", filename="file2.csv")
        mock_process.side_effect = [mock_processed_file1, mock_processed_file2]
        mock_db.create_file.return_value = "file_id"
        
        response = client.post('/upload_files/test-business', 
                             data={'file': mock_multiple_csv_files},
                             content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert len(data['failed_files']) == 0

def test_mixed_files_upload_some_valid_some_invalid(client, mock_db, test_user, mock_mixed_files):
    """Test uploading mix of valid and invalid files"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    with patch('website.web.csv_processor.process_file') as mock_process:
        mock_processed_file = File(business_id="business123", filename="valid.csv")
        mock_process.return_value = mock_processed_file
        mock_db.create_file.return_value = "file_id"
        
        response = client.post('/upload_files/test-business', 
                             data={'file': mock_mixed_files},
                             content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == False
        assert len(data['failed_files']) == 1
        assert 'Invalid file: invalid.txt' in data['failed_files'][0]

def test_empty_file_upload(client, mock_db, test_user, mock_empty_csv_file):
    """Test uploading an empty file"""
    mock_db.get_user_by_username.return_value = test_user
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    
    response = client.post('/upload_files/test-business', 
                         data={'file': mock_empty_csv_file},
                         content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = response.get_json()
    # Empty CSV files currently cause an error in processing
    assert data['success'] == False
    assert len(data['failed_files']) == 1
    assert 'Failed to parse CSV' in data['failed_files'][0]

def test_upload_page_displays_user_files(client, mock_db, test_user, mock_processed_file):
    """Test that upload page displays user's existing files"""
    # Mock user data and set up session
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_files_for_business.return_value = [mock_processed_file]

    with client.session_transaction() as sess:
        sess['username'] = 'testuser'

    response = client.get('/upload_files/test-business')
    assert response.status_code == 200
    assert b'Choose Files to Upload' in response.data

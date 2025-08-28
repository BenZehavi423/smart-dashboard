import pytest
from flask import url_for
from website.web.models import File

# Test uploading a valid CSV file
def test_upload_valid_csv(client, mock_db, test_user, mock_csv_file, mock_business):
    """Test uploading a valid CSV file"""
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_business_by_name.return_value = mock_business
    mock_db.create_business.return_value = mock_business
    
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'

    # Use the filename from the tuple (index 1)   
    mock_db.get_files_for_user.return_value = [File(business_id="business123", filename=mock_csv_file[1])]

    data = {'file': [mock_csv_file]}
    response = client.post('/upload_files/test-business', content_type='multipart/form-data', data=data)

    # Ensure success in response
    assert response.status_code == 200
    assert response.json['success'] is True
    assert mock_csv_file[1] in response.json['files']

# Test uploading a non-CSV file
def test_upload_invalid_file_type(client, mock_db, test_user, mock_txt_file):
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_files_for_user.return_value = []

    with client.session_transaction() as sess:
        sess['username'] = test_user.username

    data = {'file': [mock_txt_file]}
    response = client.post('/upload_files/test-business', content_type='multipart/form-data', data=data)

    # Ensure failure in response
    assert response.status_code == 200
    assert response.json['success'] is False
    assert 'Invalid file' in response.json['failed_files'][0]

# Test uploading both valid and invalid files together
def test_upload_mixed_files(client, mock_db, test_user, mock_mixed_files):
    mock_db.get_user_by_username.return_value = test_user
    mock_db.get_files_for_user.return_value = []

    with client.session_transaction() as sess:
        sess['username'] = test_user.username

    data = {'file': mock_mixed_files}
    response = client.post('/upload_files/test-business', content_type='multipart/form-data', data=data)

    # One file should succeed, one should fail
    assert response.status_code == 200
    assert response.json['success'] is False
    assert any('Invalid file' in err for err in response.json['failed_files'])

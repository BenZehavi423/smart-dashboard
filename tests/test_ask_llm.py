from unittest.mock import Mock, patch
from website.web.models import User
import requests


def test_ask_llm_success(client, mocker, mock_db, test_user):
    """
    GIVEN a logged-in user
    WHEN the /ask_llm endpoint is called
    AND the llm_service returns a successful response
    THEN the main web app should return that response correctly
    """
    # Mock the requests.post call
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'response': 'Success from mock LLM'}
    mocker.patch('requests.post', return_value=mock_response)

    mock_db.get_user_by_username.return_value = test_user
    # Simulate logged-in session
    with client.session_transaction() as sess:
        sess['username'] = test_user.username

    # Make the request to your web app's endpoint
    response = client.post('/ask_llm', json={'query': 'Test query'})
    json_data = response.get_json()

    assert response.status_code == 200
    assert json_data['response'] == 'Success from mock LLM'


def test_ask_llm_service_unavailable(client, mocker, mock_db, test_user):
    """
    GIVEN a logged-in user
    WHEN the /ask_llm endpoint is called
    AND the llm_service is unavailable
    THEN the main web app should return a 503 error
    """
    # Mock a failed requests.post call
    mocker.patch('requests.post', side_effect=requests.exceptions.RequestException)

    mock_db.get_user_by_username.return_value = test_user
    # Simulate logged-in session
    with client.session_transaction() as sess:
        sess['username'] = test_user.username

    response = client.post('/ask_llm', json={'query': 'Test query'})
    json_data = response.get_json()

    assert response.status_code == 503
    assert 'error' in json_data
    assert json_data['error'] == 'The LLM service is currently unavailable.'
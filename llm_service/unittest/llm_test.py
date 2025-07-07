from llm_service.app import app
import pytest

# Use pytest's fixture to create a test client
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Test for the successful path
def test_predict_success(client, mocker):
    """
    GIVEN a running llm_service
    WHEN the /predict endpoint is called with a valid query
    THEN it should return a successful response from the mocked Gemini API
    """
    # Mock the Gemini API's generate_content method
    mock_gemini_response = mocker.MagicMock()
    mock_gemini_response.text = "This is a mocked AI response."
    mocker.patch('google.generativeai.GenerativeModel.generate_content', return_value=mock_gemini_response)

    # Make the test request
    response = client.post('/predict', json={'query': 'Hello, world!'})
    json_data = response.get_json()

    # Assertions
    assert response.status_code == 200
    assert json_data['response'] == "This is a mocked AI response."

# Test for the failure path (missing query)
def test_predict_no_query(client):
    """
    GIVEN a running llm_service
    WHEN the /predict endpoint is called without a query
    THEN it should return a 400 Bad Request error
    """
    response = client.post('/predict', json={})
    json_data = response.get_json()

    assert response.status_code == 400
    assert 'error' in json_data
    assert json_data['error'] == 'Query is required'
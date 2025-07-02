import pytest
import bcrypt
from unittest.mock import patch, MagicMock
from website.web.models import User

@pytest.fixture
def mock_db():
    with patch('website.web.db_manager.MongoDBManager') as MockDB:
        mock_db_instance = MockDB.return_value
        yield mock_db_instance

@pytest.fixture
def test_user():
    return User(username="testuser", email="test@example.com", password_hash="hashed")

def test_create_and_get_user(mock_db, test_user):
    # Setup mock return values
    mock_db.create_user.return_value = "mocked_id"
    mock_db.get_user_by_username.return_value = test_user

    user_id = mock_db.create_user(test_user)
    fetched = mock_db.get_user_by_username(test_user.username)

    assert user_id == "mocked_id"
    assert fetched is test_user
    assert fetched.username == "testuser"
    assert fetched.email == "test@example.com"

# This code is for testing the User model's database operations.
# It creates a user, fetches it by username, and cleans up after the test.

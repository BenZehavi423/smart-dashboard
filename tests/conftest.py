import pytest
import bcrypt
from unittest.mock import patch, MagicMock
from website.web.models import User
from website.web import create_app

@pytest.fixture
def mock_db():
    with patch('website.web.db_manager.MongoDBManager') as MockDB:
        mock_db_instance = MockDB.return_value
        yield mock_db_instance

@pytest.fixture
def test_user():
    return User(username="testuser", email="test@example.com", password_hash="hashed")

@pytest.fixture
def app(mock_db):
    app = create_app()
    app.config['TESTING'] = True
    # Set the mocked database on the app
    app.db = mock_db
    return app

@pytest.fixture
def client(app):
    return app.test_client() 
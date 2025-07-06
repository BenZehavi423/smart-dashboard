import pytest
import bcrypt
import io
from unittest.mock import patch, MagicMock
from website.web.models import User, File
from website.web import create_app

@pytest.fixture
def mock_db():
    with patch('website.web.db_manager.MongoDBManager') as MockDB:
        mock_db_instance = MockDB.return_value
        yield mock_db_instance

@pytest.fixture
def test_user():
    hashed = bcrypt.hashpw("securepassword".encode(), bcrypt.gensalt()).decode()
    return User(username="testuser", email="test@example.com", password_hash=hashed)

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

# Mock file fixtures
@pytest.fixture
def mock_csv_file():
    """Create a mock CSV file for testing"""
    csv_content = "name,age\nJohn,25\nJane,30"
    return (io.BytesIO(csv_content.encode()), 'test.csv')

@pytest.fixture
def mock_csv_file_simple():
    """Create a simple mock CSV file for testing"""
    csv_content = "name,age\nJohn,25"
    return (io.BytesIO(csv_content.encode()), 'simple.csv')

@pytest.fixture
def mock_csv_file_population():
    """Create a mock CSV file with population data"""
    csv_content = "city,population\nNYC,8000000\nLA,4000000"
    return (io.BytesIO(csv_content.encode()), 'population.csv')

@pytest.fixture
def mock_txt_file():
    """Create a mock text file (invalid for upload)"""
    txt_content = "This is a text file"
    return (io.BytesIO(txt_content.encode()), 'test.txt')

@pytest.fixture
def mock_empty_csv_file():
    """Create an empty CSV file"""
    return (io.BytesIO(b''), 'empty.csv')

@pytest.fixture
def mock_processed_file():
    """Create a mock processed File object"""
    return File(filename="test.csv", user_id="user123")

@pytest.fixture
def mock_multiple_csv_files():
    """Create multiple mock CSV files"""
    csv1_content = "name,age\nJohn,25"
    csv1_file = (io.BytesIO(csv1_content.encode()), 'file1.csv')
    csv2_content = "city,population\nNYC,8000000"
    csv2_file = (io.BytesIO(csv2_content.encode()), 'file2.csv')
    return [csv1_file, csv2_file]

@pytest.fixture
def mock_mixed_files():
    """Create a mix of valid and invalid files"""
    csv_content = "name,age\nJohn,25"
    csv_file = (io.BytesIO(csv_content.encode()), 'valid.csv')
    txt_content = "This is invalid"
    txt_file = (io.BytesIO(txt_content.encode()), 'invalid.txt')
    return [csv_file, txt_file] 
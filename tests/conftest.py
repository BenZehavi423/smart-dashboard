import pytest
import bcrypt
import io
from unittest.mock import patch, MagicMock
from website.web.models import User, File, Business
from website.web import create_app

# ----- General Mocks -----
@pytest.fixture
def mock_db():
    """Mock database manager"""
    mock = MagicMock()
    
    # Mock user methods
    mock.get_user_by_username.return_value = None
    mock.get_user_by_id.return_value = None
    mock.create_user.return_value = "user_id"
    
    # Mock file methods
    mock.create_file.return_value = "file_id"
    mock.get_files_for_user.return_value = []
    mock.get_files_for_business.return_value = []
    
    # Mock plot methods
    mock.create_plot.return_value = "plot_id"
    mock.get_plots_for_user.return_value = []
    mock.get_plots_for_business.return_value = []
    mock.get_presented_plots_for_business_ordered.return_value = []
    mock.get_presented_plots_for_user_ordered.return_value = []
    mock.update_multiple_plots.return_value = True
    mock.update_plot_presentation_order.return_value = True
    
    # Mock business methods
    mock.get_business_by_id.return_value = None
    mock.get_business_by_name.return_value = None
    mock.update_business.return_value = True
    
    # Mock user profile methods (for backward compatibility)
    mock.get_or_create_user_profile.return_value = None
    
    return mock

@pytest.fixture
def test_user():
    hashed = bcrypt.hashpw("securepassword".encode(), bcrypt.gensalt()).decode()
    user = User(username="testuser", email="test@example.com", password_hash=hashed, phone="12345")
    user._id = "testuser_id"  # Set specific ID to match mock_business editors
    return user

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

@pytest.fixture
def mock_business():
    """Mock business object with all required attributes"""
    business = Business(owner="owner123", name="Business 123")
    business._id = "business123"
    business.presented_plot_order = []
    business.editors = ["testuser_id"]  # Add test user ID to editors
    return business

@pytest.fixture
def registered_user(mock_db):
    """Mock registered user data for login tests"""
    password = 'securepassword'
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(username='testuser', email='test@example.com', password_hash=hashed_pw)
    mock_db.get_user_by_username.return_value = user
    return {'username': user.username, 'password': password}

@pytest.fixture
def logged_in_user(client, mock_db):
    """Helper fixture to create a logged-in user session"""
    password = 'securepassword'
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(username='testuser', email='test@example.com', password_hash=hashed_pw)
    mock_db.get_user_by_username.return_value = user

    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
        
    return {'username': user.username, 'password': password}

# ----- File Mocks -----
@pytest.fixture
def mock_csv_file():
    csv_content = "name,age\nJohn,25\nJane,30"
    return (io.BytesIO(csv_content.encode()), 'test.csv')

@pytest.fixture
def mock_csv_file_simple():
    csv_content = "name,age\nJohn,25"
    return (io.BytesIO(csv_content.encode()), 'simple.csv')

@pytest.fixture
def mock_csv_file_population():
    csv_content = "city,population\nNYC,8000000\nLA,4000000"
    return (io.BytesIO(csv_content.encode()), 'population.csv')

@pytest.fixture
def mock_txt_file():
    """invalid file for upload"""
    txt_content = "This is a text file"
    return (io.BytesIO(txt_content.encode()), 'test.txt')

@pytest.fixture
def mock_empty_csv_file():
    return (io.BytesIO(b''), 'empty.csv')

@pytest.fixture
def mock_processed_file():
    return File(business_id="business123", filename="test.csv")

@pytest.fixture
def mock_multiple_csv_files():
    csv1_content = "name,age\nJohn,25"
    csv1_file = (io.BytesIO(csv1_content.encode()), 'file1.csv')
    csv2_content = "city,population\nNYC,8000000"
    csv2_file = (io.BytesIO(csv2_content.encode()), 'file2.csv')
    return [csv1_file, csv2_file]

@pytest.fixture
def mock_mixed_files():
    """mix of valid and invalid files"""
    csv_content = "name,age\nJohn,25"
    csv_file = (io.BytesIO(csv_content.encode()), 'valid.csv')
    txt_content = "This is invalid"
    txt_file = (io.BytesIO(txt_content.encode()), 'invalid.txt')
    return [csv_file, txt_file]


# ----- Plot Mocks -----
@pytest.fixture
def sample_plots():
    return [
        {
            '_id': 'plot1',
            'image_name': 'Sales Analysis',
            'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
            'created_time': '2025-07-05T10:00:00',
            'is_presented': True
        },
        {
            '_id': 'plot2',
            'image_name': 'Revenue Chart',
            'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
            'created_time': '2025-07-05T11:00:00',
            'is_presented': False
        },
        {
            '_id': 'plot3',
            'image_name': 'Customer Trends',
            'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
            'created_time': '2025-07-05T12:00:00',
            'is_presented': True
        }
    ]

@pytest.fixture
def sample_business_page_with_order():
    from website.web.models import Business
    business = Business(
        owner="owner123",
        name="Business 123"
    )
    business.presented_plot_order = ["plot1", "plot3", "plot2"]
    return business

@pytest.fixture
def mock_plots_for_business(mock_db, sample_plots):
    from website.web.models import Plot
    from datetime import datetime
    
    plots = []
    for plot_data in sample_plots:
        plot = Plot(
            image_name=plot_data['image_name'],
            image=plot_data['image'],
            files=[],
            created_time=datetime.fromisoformat(plot_data['created_time']),
            is_presented=plot_data['is_presented'],
            business_id="business123",
            _id=plot_data['_id']
        )
        plots.append(plot)
    
    mock_db.get_plots_for_business.return_value = plots
    return plots

@pytest.fixture
def mock_presented_plots_ordered(mock_db, sample_plots):
    from website.web.models import Plot
    from datetime import datetime
    
    presented_plots = []
    for plot_data in sample_plots:
        if plot_data['is_presented']:
            plot = Plot(
                image_name=plot_data['image_name'],
                image=plot_data['image'],
                files=[],
                created_time=datetime.fromisoformat(plot_data['created_time']),
                is_presented=plot_data['is_presented'],
                business_id="business123",
                _id=plot_data['_id']
            )
            presented_plots.append(plot)
    
    mock_db.get_presented_plots_for_business_ordered.return_value = presented_plots
    return presented_plots 
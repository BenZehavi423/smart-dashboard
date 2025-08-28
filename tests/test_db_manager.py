import pytest
from website.web.models import User, Business, File, Plot
from website.web.db_manager import MongoDBManager
from unittest.mock import Mock, MagicMock, patch

@pytest.fixture
def mock_mongo_collections():
    """Mock MongoDB collections for testing"""
    with patch('website.web.db_manager.MongoClient') as mock_client:
        # Create mock collections
        mock_businesses = MagicMock()
        mock_users = MagicMock()
        mock_files = MagicMock()
        mock_datasets = MagicMock()
        mock_analysis = MagicMock()
        mock_plots = MagicMock()
        mock_dashboards = MagicMock()
        
        # Set up the mock client to return our mock database
        mock_db = MagicMock()
        mock_db.__getitem__.side_effect = lambda name: {
            'businesses': mock_businesses,
            'users': mock_users,
            'files': mock_files,
            'datasets': mock_datasets,
            'analysis_results': mock_analysis,
            'plots': mock_plots,
            'dashboards': mock_dashboards
        }[name]
        
        mock_client.return_value.__getitem__.return_value = mock_db
        
        # Create a real MongoDBManager instance
        db_manager = MongoDBManager()
        
        # Replace the collections with our mocks
        db_manager.businesses = mock_businesses
        db_manager.users = mock_users
        db_manager.files = mock_files
        db_manager.datasets = mock_datasets
        db_manager.analysis = mock_analysis
        db_manager.plots = mock_plots
        db_manager.dashboards = mock_dashboards
        
        yield db_manager


def test_get_businesses_for_owner(mock_mongo_collections):
    """Test that get_businesses_for_owner returns businesses owned by user"""
    # Create test businesses
    business1 = Business(owner="owner1", name="Business 1")
    business2 = Business(owner="owner1", name="Business 2")
    business3 = Business(owner="owner2", name="Business 3")
    
    # Mock the database find method to return only businesses owned by owner1
    mock_mongo_collections.businesses.find.return_value = [
        business1.to_dict(),
        business2.to_dict()
    ]
    
    # Test getting businesses for owner1
    result = mock_mongo_collections.get_businesses_for_owner("owner1")
    
    # Should return businesses 1 and 2
    assert len(result) == 2
    business_names = [b.name for b in result]
    assert "Business 1" in business_names
    assert "Business 2" in business_names
    
    # Verify the correct query was made
    mock_mongo_collections.businesses.find.assert_called_with({"owner": "owner1"})

def test_get_files_for_business(mock_mongo_collections):
    """Test that get_files_for_business returns files for the given business"""
    # Create test business and files
    business = Business(owner="owner1", name="Test Business")
    business._id = "business123"
    
    file1 = File(business_id="business123", filename="file1.csv")
    file2 = File(business_id="business123", filename="file2.csv")
    file3 = File(business_id="other_business", filename="file3.csv")
    
    # Mock the database find method to return only files for business123
    mock_mongo_collections.files.find.return_value = [
        file1.to_dict(),
        file2.to_dict()
    ]
    
    # Test getting files for the business
    result = mock_mongo_collections.get_files_for_business(business)
    
    # Should return files 1 and 2 (not file3 which belongs to other business)
    assert len(result) == 2
    filenames = [f.filename for f in result]
    assert "file1.csv" in filenames
    assert "file2.csv" in filenames
    
    # Verify the correct query was made
    mock_mongo_collections.files.find.assert_called_with({"business_id": "business123"})

def test_update_business(mock_mongo_collections):
    """Test that update_business updates business fields correctly"""
    # Mock successful update
    mock_mongo_collections.businesses.update_one.return_value = Mock(modified_count=1)
    
    updates = {"address": "New Address", "phone": "123-456-7890"}
    result = mock_mongo_collections.update_business("business123", updates)
    
    assert result == True
    mock_mongo_collections.businesses.update_one.assert_called_with(
        {"_id": "business123"}, 
        {"$set": updates}
    )

def test_update_user(mock_mongo_collections):
    """Test that update_user updates user fields correctly"""
    # Mock successful update
    mock_mongo_collections.users.update_one.return_value = Mock(modified_count=1)
    
    updates = {"email": "new@example.com", "phone": "987-654-3210"}
    result = mock_mongo_collections.update_user("user123", updates)
    
    assert result == True
    mock_mongo_collections.users.update_one.assert_called_with(
        {"_id": "user123"}, 
        {"$set": updates}
    ) 
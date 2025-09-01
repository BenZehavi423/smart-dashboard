import pytest
import pandas as pd
import io
from unittest.mock import patch, MagicMock
from website.web.csv_processor import process_file
from website.web.models import File
from werkzeug.utils import secure_filename

# Mock the secure_filename function to simplify testing
@patch('website.web.csv_processor.secure_filename', new=lambda filename: filename)
def test_process_file_valid_csv():
    """Test processing a valid CSV file."""
    # Create a mock file object with valid CSV content
    csv_content = "column1,column2\nvalue1,value2"
    mock_file = MagicMock()
    mock_file.filename = "test.csv"
    mock_file.read.return_value = csv_content.encode('utf-8')
    mock_file.seek.return_value = 0
    
    business_id = "test_business_id"
    
    # We need to mock pandas.read_csv because the real one is called inside
    with patch('pandas.read_csv') as mock_read_csv:
        # Mock read_csv to return a DataFrame
        mock_df = pd.DataFrame([{"column1": "value1", "column2": "value2"}])
        mock_read_csv.return_value = mock_df

        # Call the function
        result_file = process_file(mock_file, business_id)

    # Assertions
    assert isinstance(result_file, File)
    assert result_file.filename == "test.csv"
    assert result_file.business_id == business_id
    assert result_file.preview == [{"column1": "value1", "column2": "value2"}]
    assert len(result_file.preview) == 1

@patch('website.web.csv_processor.secure_filename', new=lambda filename: filename)
def test_process_file_with_only_header():
    """Test processing a CSV file with only a header row."""
    csv_content = "column1,column2"
    mock_file = MagicMock()
    mock_file.filename = "header_only.csv"
    mock_file.read.return_value = csv_content.encode('utf-8')
    mock_file.seek.return_value = 0

    business_id = "test_business_id"

    with patch('pandas.read_csv') as mock_read_csv:
        mock_df = pd.DataFrame(columns=["column1", "column2"])
        mock_read_csv.return_value = mock_df

        result_file = process_file(mock_file, business_id)

    assert isinstance(result_file, File)
    assert result_file.filename == "header_only.csv"
    assert result_file.preview == []
    
@patch('website.web.csv_processor.secure_filename', new=lambda filename: filename)
def test_process_file_with_invalid_format():
    """Test that a non-CSV file raises a ValueError."""
    # Create a mock file object for a text file
    txt_content = "This is not a CSV file."
    mock_file = MagicMock()
    mock_file.filename = "test.txt"
    mock_file.read.return_value = txt_content.encode('utf-8')
    mock_file.seek.return_value = 0

    business_id = "test_business_id"

    # We mock pandas.read_csv to raise an error
    with patch('pandas.read_csv', side_effect=pd.errors.ParserError("Invalid format")):
        with pytest.raises(ValueError, match="Failed to parse CSV"):
            process_file(mock_file, business_id)

@patch('website.web.csv_processor.secure_filename', new=lambda filename: filename)
def test_process_file_with_large_data_preview_limit():
    """Test that only the first 100 rows are used for the preview."""
    # Create a mock DataFrame with more than 100 rows
    mock_df = pd.DataFrame([{'col': i} for i in range(150)])
    mock_file = MagicMock()
    mock_file.filename = "large.csv"
    
    with patch('pandas.read_csv', return_value=mock_df):
        result_file = process_file(mock_file, "test_business_id")
        
    assert isinstance(result_file, File)
    # The preview should only contain the first 100 rows
    assert len(result_file.preview) == 100
    assert result_file.preview[0]['col'] == 0
    assert result_file.preview[99]['col'] == 99
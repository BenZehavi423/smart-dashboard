import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from website.web.plot_generator import build_plot_generation_prompt, generate_plot_image
from website.web.models import File
from io import BytesIO
from flask import Flask

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.db = MagicMock()
    return app

@pytest.fixture
def mock_df_preview():
    """Returns a sample pandas DataFrame for mocking."""
    data = {'city': ['Tel Aviv', 'Haifa', 'Jerusalem'], 'sales': [100, 150, 200]}
    return pd.DataFrame(data)

@pytest.fixture
def mock_file_obj_with_preview(mock_df_preview):
    """Returns a mock File object with a data preview."""
    file = File(business_id="test_business_id", filename="sales.csv")
    file._id = "test_file_id"
    file.preview = mock_df_preview.to_dict(orient="records")
    return file


# Use the 'app' fixture and context to run the tests
# Patching is applied directly to the module where the function is used
@patch('website.web.plot_generator.request_llm')
def test_generate_plot_image_success(mock_request_llm, mock_file_obj_with_preview, app):
    """Test successful plot generation from LLM code."""
    mock_request_llm.return_value = [
        "plt.figure(figsize=(8, 6))",
        "plt.bar(df['city'], df['sales'])",
        "plt.title('Sales by City')",
        "plt.xlabel('City')",
        "plt.ylabel('Sales')",
        "buffer = io.BytesIO()",
        "plt.savefig(buffer, format='png')",
        "buffer.seek(0)"
    ]
    
    with app.app_context():
        # Correctly mock the database call within the application context
        app.db.get_file.return_value = mock_file_obj_with_preview
        
        user_prompt = "Create a bar chart of sales by city."
        image_b64 = generate_plot_image(mock_file_obj_with_preview._id, user_prompt)
    
    assert image_b64.startswith("data:image/png;base64,")
    mock_request_llm.assert_called_once()
    
@patch('website.web.plot_generator.request_llm')
def test_generate_plot_image_llm_returns_bad_code(mock_request_llm, mock_file_obj_with_preview, app):
    """Test that bad LLM code raises a RuntimeError."""
    mock_request_llm.return_value = ["plt.invalid_command(df)"]
    
    with app.app_context():
        app.db.get_file.return_value = mock_file_obj_with_preview
        
        with pytest.raises(RuntimeError, match="An error occurred while executing the generated plot code"):
            generate_plot_image(mock_file_obj_with_preview._id, "Generate an invalid plot.")
        
@patch('website.web.plot_generator.request_llm')
def test_generate_plot_image_llm_returns_no_code(mock_request_llm, mock_file_obj_with_preview, app):
    """Test that an empty LLM response raises a RuntimeError."""
    mock_request_llm.return_value = []
    
    with app.app_context():
        app.db.get_file.return_value = mock_file_obj_with_preview
        
        with pytest.raises(RuntimeError, match="LLM did not return any code"):
            generate_plot_image(mock_file_obj_with_preview._id, "This should fail.")
        
def test_generate_plot_image_file_not_found(app):
    """Test that a non-existent file_id raises a ValueError."""
    
    with app.app_context():
        app.db.get_file.return_value = None
        
        with pytest.raises(ValueError, match="File not found or has no data preview."):
            generate_plot_image("non_existent_file_id", "Prompt.")
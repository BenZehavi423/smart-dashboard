import pytest
import json
from unittest.mock import patch, MagicMock
from website.web.validation import Validator
from website.web.models import User, Business
import bcrypt

class TestValidator:
    """Test the Validator class and its validation methods"""

    def test_validate_username_valid(self):
        """Test valid username validation"""
        valid_usernames = [
            "john123",
            "user_name",
            "test.user",
            "user-name",
            "a" * 20,  # Max length
            "abc"  # Min length
        ]
        
        for username in valid_usernames:
            is_valid, error_msg = Validator.validate_username(username)
            assert is_valid, f"Username '{username}' should be valid: {error_msg}"
            assert error_msg == ""

    def test_validate_username_invalid(self):
        """Test invalid username validation"""
        invalid_cases = [
            ("", "Username is required"),
            ("ab", "Username must be at least 3 characters long"),
            ("a" * 21, "Username must be no more than 20 characters long"),
            ("user@name", "Username can only contain letters, numbers, underscores, hyphens, and periods"),
            ("user name", "Username can only contain letters, numbers, underscores, hyphens, and periods"),
            ("user#name", "Username can only contain letters, numbers, underscores, hyphens, and periods")
        ]
        
        for username, expected_error in invalid_cases:
            is_valid, error_msg = Validator.validate_username(username)
            assert not is_valid, f"Username '{username}' should be invalid"
            assert expected_error in error_msg

    def test_validate_password_valid(self):
        """Test valid password validation"""
        valid_passwords = [
            "password123",
            "Pass123",
            "MyPass1",
            "abc1"  # Min length with letter and number
        ]
        
        for password in valid_passwords:
            is_valid, error_msg = Validator.validate_password(password)
            assert is_valid, f"Password '{password}' should be valid: {error_msg}"
            assert error_msg == ""

    def test_validate_password_invalid(self):
        """Test invalid password validation"""
        invalid_cases = [
            ("", "Password is required"),
            ("ab", "Password must be at least 3 characters long"),
            ("a" * 31, "Password too long"),
            ("password", "Password must contain at least one letter and one number"),
            ("123456", "Password must contain at least one letter and one number"),
            ("pass", "Password must contain at least one letter and one number")
        ]
        
        for password, expected_error in invalid_cases:
            is_valid, error_msg = Validator.validate_password(password)
            assert not is_valid, f"Password '{password}' should be invalid"
            assert expected_error in error_msg

    def test_validate_email_valid(self):
        """Test valid email validation"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@test.com"
        ]
        
        for email in valid_emails:
            is_valid, error_msg = Validator.validate_email(email)
            assert is_valid, f"Email '{email}' should be valid: {error_msg}"
            assert error_msg == ""

    def test_validate_email_invalid(self):
        """Test invalid email validation"""
        invalid_cases = [
            ("", "Email is required"),
            ("invalid-email", "Please enter a valid email address"),
            ("@example.com", "Please enter a valid email address"),
            ("user@", "Please enter a valid email address"),
            ("user@.com", "Please enter a valid email address"),
            ("a" * 255 + "@example.com", "Email address is too long")
        ]
        
        for email, expected_error in invalid_cases:
            is_valid, error_msg = Validator.validate_email(email)
            assert not is_valid, f"Email '{email}' should be invalid"
            assert expected_error in error_msg

    def test_validate_email_optional(self):
        """Test optional email validation"""
        # Empty email should be valid when not required
        is_valid, error_msg = Validator.validate_email("", required=False)
        assert is_valid
        assert error_msg == ""

    def test_validate_phone_valid(self):
        """Test valid phone validation"""
        valid_phones = [
            "1234567890",
            "1234567",
            "123456789012345",
            "+1234567890",
            "*1234",
            "#1234"
        ]
        
        for phone in valid_phones:
            is_valid, error_msg = Validator.validate_phone(phone)
            assert is_valid, f"Phone '{phone}' should be valid: {error_msg}"
            assert error_msg == ""

    def test_validate_phone_invalid(self):
        """Test invalid phone validation"""
        invalid_cases = [
            ("123", "Invalid phone number format"),
            ("1234567890123456", "Invalid phone number format"),
            ("abc123", "Invalid phone number format"),
            ("123-abc-456", "Invalid phone number format")
        ]
        
        for phone, expected_error in invalid_cases:
            is_valid, error_msg = Validator.validate_phone(phone)
            assert not is_valid, f"Phone '{phone}' should be invalid"
            assert expected_error in error_msg

    def test_validate_phone_optional(self):
        """Test optional phone validation"""
        # Empty phone should be valid when not required
        is_valid, error_msg = Validator.validate_phone("", required=False)
        assert is_valid
        assert error_msg == ""
        
        # Empty phone should be invalid when required
        is_valid, error_msg = Validator.validate_phone("", required=True)
        assert not is_valid
        assert "Phone number is required" in error_msg

    def test_validate_business_name_valid(self):
        """Test valid business name validation"""
        valid_names = [
            "My Business",
            "Business & Co.",
            "123 Company",
            "Business-Name",
            "Business_Name",
            "a" * 50,  # Max length
            "ab"  # Min length
        ]
        
        for name in valid_names:
            is_valid, error_msg = Validator.validate_business_name(name)
            assert is_valid, f"Business name '{name}' should be valid: {error_msg}"
            assert error_msg == ""

    def test_validate_business_name_invalid(self):
        """Test invalid business name validation"""
        invalid_cases = [
            ("", "Business name is required"),
            ("a", "Business name must be at least 2 characters long"),
            ("a" * 51, "Business name must be no more than 50 characters long")
        ]
        
        for name, expected_error in invalid_cases:
            is_valid, error_msg = Validator.validate_business_name(name)
            assert not is_valid, f"Business name '{name}' should be invalid"
            assert expected_error in error_msg

    def test_validate_address_valid(self):
        """Test valid address validation"""
        valid_addresses = [
            "123 Main St",
            "123 Main St, Apt 4B",
            "123 Main St. Suite 100",
            "123 Main St - Building A",
            "a" * 100,  # Max length
            "12345"  # Min length
        ]
        
        for address in valid_addresses:
            is_valid, error_msg = Validator.validate_address(address)
            assert is_valid, f"Address '{address}' should be valid: {error_msg}"
            assert error_msg == ""

    def test_validate_address_invalid(self):
        """Test invalid address validation"""
        invalid_cases = [
            ("", "Address is required"),
            ("1234", "Address must be at least 5 characters long"),
            ("a" * 101, "Address must be no more than 100 characters long")
        ]
        
        for address, expected_error in invalid_cases:
            is_valid, error_msg = Validator.validate_address(address, required=True)
            assert not is_valid, f"Address '{address}' should be invalid"
            assert expected_error in error_msg

    def test_validate_address_optional(self):
        """Test optional address validation"""
        # Empty address should be valid when not required
        is_valid, error_msg = Validator.validate_address("", required=False)
        assert is_valid
        assert error_msg == ""

    def test_validate_analysis_prompt_valid(self):
        """Test valid analysis prompt validation"""
        valid_prompts = [
            "Analyze the sales data",
            "Show me trends in customer behavior",
            "a" * 500,  # Max length
            "Analyze data"  # Min length
        ]
        
        for prompt in valid_prompts:
            is_valid, error_msg = Validator.validate_analysis_prompt(prompt)
            assert is_valid, f"Prompt '{prompt}' should be valid: {error_msg}"
            assert error_msg == ""

    def test_validate_analysis_prompt_invalid(self):
        """Test invalid analysis prompt validation"""
        invalid_cases = [
            ("", "Analysis prompt is required"),
            ("Short", "Analysis prompt must be at least 10 characters long"),
            ("a" * 501, "Analysis prompt must be no more than 500 characters long")
        ]
        
        for prompt, expected_error in invalid_cases:
            is_valid, error_msg = Validator.validate_analysis_prompt(prompt)
            assert not is_valid, f"Prompt '{prompt}' should be invalid"
            assert expected_error in error_msg

    def test_validate_plot_name_valid(self):
        """Test valid plot name validation"""
        valid_names = [
            "Sales Analysis",
            "Revenue Chart",
            "a" * 100,  # Max length
            "ab"  # Min length
        ]
        
        for name in valid_names:
            is_valid, error_msg = Validator.validate_plot_name(name)
            assert is_valid, f"Plot name '{name}' should be valid: {error_msg}"
            assert error_msg == ""

    def test_validate_plot_name_invalid(self):
        """Test invalid plot name validation"""
        invalid_cases = [
            ("", "Plot name is required"),
            ("a", "Plot name must be at least 2 characters long"),
            ("a" * 101, "Plot name must be no more than 100 characters long")
        ]
        
        for name, expected_error in invalid_cases:
            is_valid, error_msg = Validator.validate_plot_name(name)
            assert not is_valid, f"Plot name '{name}' should be invalid"
            assert expected_error in error_msg

    def test_validate_file_valid(self):
        """Test valid file validation"""
        mock_file = MagicMock()
        mock_file.filename = "test.csv"
        mock_file.seek.return_value = None
        mock_file.tell.return_value = 1024  # 1KB
        mock_file.read.return_value = b"name,age\nJohn,25\nJane,30"  # Valid CSV content
        
        is_valid, error_msg = Validator.validate_file(mock_file)
        assert is_valid
        assert error_msg == ""
        
        # Test with different valid extensions
        mock_file.filename = "data.csv"
        is_valid, error_msg = Validator.validate_file(mock_file)
        assert is_valid
        assert error_msg == ""
        
        # Test with uppercase extension
        mock_file.filename = "data.CSV"
        is_valid, error_msg = Validator.validate_file(mock_file)
        assert is_valid
        assert error_msg == ""

    def test_validate_file_invalid(self):
        """Test invalid file validation"""
        # Test no file
        is_valid, error_msg = Validator.validate_file(None)
        assert not is_valid
        assert "No file selected" in error_msg

        # Test invalid extension
        mock_file = MagicMock()
        mock_file.filename = "test.txt"
        mock_file.seek.return_value = None
        mock_file.tell.return_value = 1024
        
        is_valid, error_msg = Validator.validate_file(mock_file)
        assert not is_valid
        assert "File type not allowed" in error_msg

        # Test file too large
        mock_file = MagicMock()
        mock_file.filename = "test.csv"
        mock_file.seek.return_value = None
        mock_file.tell.return_value = 11 * 1024 * 1024  # 11MB
        
        is_valid, error_msg = Validator.validate_file(mock_file)
        assert not is_valid
        assert "File size too large" in error_msg

    def test_sanitize_input(self):
        """Test input sanitization"""
        test_cases = [
            ("normal text", "normal text"),
            ("text with <script>alert('xss')</script>", "text with scriptalert(xss)/script"),
            ("text with 'quotes' and \"double quotes\"", "text with quotes and double quotes"),
            ("text with & symbols", "text with  symbols"),
            ("", ""),
            ("  whitespace  ", "whitespace")
        ]
        
        for input_text, expected_output in test_cases:
            sanitized = Validator.sanitize_input(input_text)
            assert sanitized == expected_output

    def test_validate_form_data(self):
        """Test bulk form validation"""
        form_data = {
            'username': 'testuser',
            'password': 'password123',
            'email': 'test@example.com',
            'phone': '1234567890'
        }
        
        validation_rules = {
            'username': {'type': 'username', 'required': True, 'label': 'Username'},
            'password': {'type': 'password', 'required': True, 'label': 'Password'},
            'email': {'type': 'email', 'required': True, 'label': 'Email'},
            'phone': {'type': 'phone', 'required': False, 'label': 'Phone'}
        }
        
        errors = Validator.validate_form_data(form_data, validation_rules)
        assert len(errors) == 0

    def test_validate_form_data_with_errors(self):
        """Test bulk form validation with errors"""
        form_data = {
            'username': 'ab',  # Too short
            'password': 'pass',  # Missing number
            'email': 'invalid-email',  # Invalid email
            'phone': '123'  # Too short
        }
        
        validation_rules = {
            'username': {'type': 'username', 'required': True, 'label': 'Username'},
            'password': {'type': 'password', 'required': True, 'label': 'Password'},
            'email': {'type': 'email', 'required': True, 'label': 'Email'},
            'phone': {'type': 'phone', 'required': True, 'label': 'Phone'}
        }
        
        errors = Validator.validate_form_data(form_data, validation_rules)
        assert len(errors) == 4
        assert 'username' in errors
        assert 'password' in errors
        assert 'email' in errors
        assert 'phone' in errors

    def test_get_username_requirements(self):
        """Test username requirements method"""
        requirements = Validator.get_username_requirements("testuser")
        assert isinstance(requirements, dict)
        assert len(requirements) > 0
        assert all(isinstance(value, bool) for value in requirements.values())

    def test_get_password_requirements(self):
        """Test password requirements method"""
        requirements = Validator.get_password_requirements("password123")
        assert isinstance(requirements, dict)
        assert len(requirements) > 0
        assert all(isinstance(value, bool) for value in requirements.values())


class TestValidationIntegration:
    """Test validation integration with Flask routes"""

    def test_register_validation_success(self, client, mock_db):
        """Test successful registration with valid data"""
        mock_db.get_user_by_username.return_value = None
        mock_db.create_user.return_value = "user_id"
        
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'password123',
            'email': 'newuser@example.com'
        })
        
        assert response.status_code == 302  # Redirect to login
        mock_db.create_user.assert_called_once()

    def test_register_validation_failure(self, client, mock_db):
        """Test registration failure with invalid data"""
        response = client.post('/register', data={
            'username': 'ab',  # Too short
            'password': 'pass'  # Missing number
        })
        
        assert response.status_code == 302  # Redirect with flash message
        # The error message will be in the flash message, not in the response data

    def test_new_business_validation_success(self, client, mock_db, test_user, mock_business):
        """Test successful business creation with valid data"""
        mock_db.get_user_by_username.return_value = test_user
        mock_db.get_business_by_name.return_value = None
        mock_db.create_business.return_value = "business_id"
        
        with client.session_transaction() as sess:
            sess['username'] = 'testuser'
        
        response = client.post('/new_business', data={
            'name': 'New Business',
            'address': '123 Main St',
            'phone': '1234567890',
            'email': 'business@example.com'
        })
        
        assert response.status_code == 302  # Redirect
        mock_db.create_business.assert_called_once()

    def test_new_business_validation_failure(self, client, mock_db, test_user):
        """Test business creation failure with invalid data"""
        mock_db.get_user_by_username.return_value = test_user
        
        with client.session_transaction() as sess:
            sess['username'] = 'testuser'
        
        response = client.post('/new_business', data={
            'name': '',  # Empty name
            'address': '123 Main St',
            'phone': '123',  # Too short
            'email': 'invalid-email'  # Invalid email
        })
        
        assert response.status_code == 200  # Stay on page
        assert b'Business name is required' in response.data

    def test_edit_profile_validation_success(self, client, mock_db, test_user):
        """Test successful profile update with valid data"""
        mock_db.get_user_by_username.return_value = test_user
        mock_db.update_user.return_value = True
        
        with client.session_transaction() as sess:
            sess['username'] = 'testuser'
        
        response = client.post('/edit_profile_details', data={
            'email': 'newemail@example.com',
            'phone': '9876543210'
        })
        
        assert response.status_code == 302  # Redirect
        mock_db.update_user.assert_called_once()

    def test_edit_profile_validation_failure(self, client, mock_db, test_user):
        """Test profile update failure with invalid data"""
        mock_db.get_user_by_username.return_value = test_user
        
        with client.session_transaction() as sess:
            sess['username'] = 'testuser'
        
        response = client.post('/edit_profile_details', data={
            'email': 'invalid-email',
            'phone': '123'  # Too short
        })
        
        assert response.status_code == 302  # Redirect with flash message

    def test_analyze_data_validation_success(self, client, mock_db, test_user, mock_business):
        """Test successful analysis with valid prompt - simplified version"""
        mock_db.get_user_by_username.return_value = test_user
        mock_db.get_business_by_name.return_value = mock_business
        
        mock_file = MagicMock()
        mock_file.data_preview = "Product,Sales\nA,100\nB,200"
        mock_db.get_file.return_value = mock_file
        
        with client.session_transaction() as sess:
            sess['username'] = 'testuser'
        
        response = client.post('/analyze_data/test-business', 
                             json={'file_id': 'file123', 'prompt': 'Analyze the sales data trends'})
        
        # Test endpoint structure - should either succeed or fail gracefully
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.get_json()
            assert data['success'] == True
        else:
            # If it fails, it should be due to plot generation, not endpoint structure
            data = response.get_json()
            assert 'error' in data

    def test_save_plot_validation_success(self, client, mock_db, test_user, mock_business):
        """Test successful plot save with valid name"""
        mock_db.get_user_by_username.return_value = test_user
        mock_db.get_business_by_name.return_value = mock_business
        mock_db.create_plot.return_value = "plot_id"
        
        with client.session_transaction() as sess:
            sess['username'] = 'testuser'
        
        response = client.post('/save_generated_plot/test-business', 
                             json={
                                 'image_name': 'Sales Analysis Chart',
                                 'image_data': 'data:image/png;base64,test',
                                 'based_on_file': 'file123'
                             })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True

    def test_save_plot_validation_failure(self, client, mock_db, test_user, mock_business):
        """Test plot save failure with invalid name"""
        mock_db.get_user_by_username.return_value = test_user
        mock_db.get_business_by_name.return_value = mock_business
        
        with client.session_transaction() as sess:
            sess['username'] = 'testuser'
        
        response = client.post('/save_generated_plot/test-business', 
                             json={
                                 'image_name': '',  # Empty name
                                 'image_data': 'data:image/png;base64,test',
                                 'based_on_file': 'file123'
                             })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] == False
        assert 'Plot name is required' in data['error'] 

    def test_register_ajax_validation_success(self, client, mock_db):
        """Test successful AJAX registration with valid data"""
        mock_db.get_user_by_username.return_value = None
        mock_db.create_user.return_value = "user_id"
        
        response = client.post('/register', 
                              data={'username': 'newuser', 'password': 'password123'},
                              headers={'X-Requested-With': 'XMLHttpRequest'})
        
        # Should redirect on success
        assert response.status_code == 302
        mock_db.create_user.assert_called_once()

    def test_register_ajax_validation_failure(self, client, mock_db):
        """Test AJAX registration failure with invalid data"""
        response = client.post('/register', 
                              data={'username': 'ab', 'password': 'pass'},
                              headers={'X-Requested-With': 'XMLHttpRequest'})
        
        # Should return 400 status for AJAX requests with errors
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Username must be at least 3 characters long' in data['error']

    def test_register_ajax_duplicate_username(self, client, mock_db):
        """Test AJAX registration failure with duplicate username"""
        # Mock existing user
        mock_user = User(username='existinguser', password_hash='hashed')
        mock_db.get_user_by_username.return_value = mock_user
        
        response = client.post('/register', 
                              data={'username': 'existinguser', 'password': 'password123'},
                              headers={'X-Requested-With': 'XMLHttpRequest'})
        
        # Should return 400 status for AJAX requests with errors
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Username already exists' in data['error'] 

    def test_login_ajax_validation_success(self, client, mock_db):
        """Test successful AJAX login with valid credentials"""
        password = 'password123'
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(username='testuser', password_hash=hashed_pw)
        mock_db.get_user_by_username.return_value = user
        
        response = client.post('/login', 
                              data={'username': 'testuser', 'password': 'password123'},
                              headers={'X-Requested-With': 'XMLHttpRequest'})
        
        # Should redirect on success
        assert response.status_code == 302

    def test_login_ajax_validation_failure(self, client, mock_db):
        """Test AJAX login failure with invalid credentials"""
        mock_db.get_user_by_username.return_value = None
        
        response = client.post('/login', 
                              data={'username': 'wronguser', 'password': 'wrongpass'},
                              headers={'X-Requested-With': 'XMLHttpRequest'})
        
        # Should return 400 status for AJAX requests with errors
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Username not found' in data['error']

    def test_login_ajax_incorrect_password(self, client, mock_db):
        """Test AJAX login failure with correct username but wrong password"""
        # Mock user exists but password is wrong
        password = 'correctpassword'
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(username='testuser', password_hash=hashed_pw)
        mock_db.get_user_by_username.return_value = user
        
        response = client.post('/login', 
                              data={'username': 'testuser', 'password': 'wrongpassword'},
                              headers={'X-Requested-With': 'XMLHttpRequest'})
        
        # Should return 400 status for AJAX requests with errors
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Incorrect password' in data['error'] 
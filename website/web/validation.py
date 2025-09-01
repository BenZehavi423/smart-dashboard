import re
import os
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Set up logger
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(message)

class Validator:
    """Comprehensive input validation class for the SmartDashboard application"""
    
    # Regex patterns for validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^(\+?\d{4,15}|(\*|#)\d{4}|\d+-\d+)$')  # Various phone formats
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]{3,20}$')  # 3-20 chars, alphanumeric + underscore, hyphen, period
    PASSWORD_PATTERN = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*?&]{3,30}$')  # 3-30 chars, 1 letter, 1 digit
    BUSINESS_NAME_PATTERN = re.compile(r'^.{2,50}$')  # 2-50 chars, any character
    ADDRESS_PATTERN = re.compile(r'^.{5,100}$')  # 5-100 chars, any character
    
    # File validation
    ALLOWED_EXTENSIONS = {'.csv'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def validate_username(cls, username: str) -> Tuple[bool, str]:
        """Validate username format and length"""
        if not username:
            return False, "Username is required"
        
        username = username.strip()
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 20:
            return False, "Username must be no more than 20 characters long"
        
        if not cls.USERNAME_PATTERN.match(username):
            return False, "Username can only contain letters, numbers, underscores, hyphens, and periods"
        
        return True, ""
    
    @classmethod
    def validate_password(cls, password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if not password:
            return False, "Password is required"
        
        if len(password) < 3:
            return False, "Password must be at least 3 characters long"
        
        if len(password) > 30:
            return False, "Password too long"
        
        if not cls.PASSWORD_PATTERN.match(password):
            return False, "Password must contain at least one letter and one number"
        
        return True, ""
    
    @classmethod
    def validate_email(cls, email: str, required: bool = True) -> Tuple[bool, str]:
        """Validate email format"""
        if not email and not required:
            return True, ""
        
        if not email:
            return False, "Email is required"
        
        email = email.strip()
        
        if not cls.EMAIL_PATTERN.match(email):
            return False, "Please enter a valid email address"
        
        if len(email) > 254:
            return False, "Email address is too long"
        
        return True, ""
    
    @classmethod
    def validate_phone(cls, phone: str, required: bool = False) -> Tuple[bool, str]:
        """Validate phone number format"""
        if not phone and not required:
            return True, ""
        
        if not phone:
            return False, "Phone number is required"
        
        phone = phone.strip()
        
        if not cls.PHONE_PATTERN.match(phone):
            return False, "Invalid phone number format"
        
        if '-' in phone:
            if phone.startswith('-') or phone.endswith('-'):
                return False, "Phone Number cannot start or end with a hyphen"
            # Check that there's only one hyphen
            if phone.count('-') > 1:
                return False, "Only one hyphen allowed"
        
        if phone.startswith('*') or phone.startswith('#'):
            # Must be exactly 5 characters (symbol + 4 digits)
            if len(phone) != 5:
                return False, "Invalid format for * or # numbers"
        
        # Count digits only for length validation
        digits_only = re.sub(r'[^\d]', '', phone)
        if len(digits_only) < 4 or len(digits_only) > 15:
            return False, "Phone number must be 4-15 digits"
        
        return True, ""
    
    @classmethod
    def validate_business_name(cls, name: str) -> Tuple[bool, str]:
        """Validate business name format and length"""
        if not name:
            return False, "Business name is required"
        
        name = name.strip()
        
        if len(name) < 2:
            return False, "Business name must be at least 2 characters long"
        
        if len(name) > 50:
            return False, "Business name must be no more than 50 characters long"
        
        if not cls.BUSINESS_NAME_PATTERN.match(name):
            return False, "Business name must be 2-50 characters long"
        
        return True, ""
    
    @classmethod
    def validate_address(cls, address: str, required: bool = False) -> Tuple[bool, str]:
        """Validate address format"""
        if not address and not required:
            return True, ""
        
        if not address:
            return False, "Address is required"
        
        address = address.strip()
        
        if len(address) < 5:
            return False, "Address must be at least 5 characters long"
        
        if len(address) > 100:
            return False, "Address must be no more than 100 characters long"
        
        if not cls.ADDRESS_PATTERN.match(address):
            return False, "Invalid address format"
        
        return True, ""
    
    @classmethod
    def validate_file(cls, file, allowed_extensions: Optional[set] = None, max_size: Optional[int] = None) -> Tuple[bool, str]:
        """Validate uploaded file"""
        if not file:
            return False, "No file selected"
        
        if not file.filename:
            return False, "Invalid file"
        
        # Check file extension
        allowed_exts = allowed_extensions or cls.ALLOWED_EXTENSIONS
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_exts:
            return False, f"File type not allowed. Allowed types: {', '.join(allowed_exts)}"
        
        # Check file size
        max_file_size = max_size or cls.MAX_FILE_SIZE
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size == 0:
            return False, "File is empty"
        
        if file_size > max_file_size:
            return False, f"File size too large. Maximum size: {max_file_size // (1024*1024)}MB"
        
        # For CSV files, check if they have content beyond headers
        if file_ext == '.csv':
            try:
                # Read first few lines to check for content
                file.seek(0)
                content = file.read(1024).decode('utf-8', errors='ignore')
                file.seek(0)  # Reset position
                
                lines = content.split('\n')
                if len(lines) <= 1:
                    return False, "CSV file appears to be empty or contains only headers"
                
                # Check if there's actual data (not just empty lines)
                has_data = False
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        has_data = True
                        break
                
                if not has_data:
                    return False, "CSV file contains no data rows"
                    
            except Exception as e:
                # If we can't read the file, still allow it but log the issue
                logger.warning(f"Could not validate CSV content for {file.filename}: {e}")
        
        return True, ""
    
    @classmethod
    def validate_analysis_prompt(cls, prompt: str) -> Tuple[bool, str]:
        """Validate analysis prompt"""
        if not prompt:
            return False, "Analysis prompt is required"
        
        prompt = prompt.strip()
        
        if len(prompt) < 10:
            return False, "Analysis prompt must be at least 10 characters long"
        
        if len(prompt) > 500:
            return False, "Analysis prompt must be no more than 500 characters long"
        
        return True, ""
    
    @classmethod
    def validate_plot_name(cls, name: str) -> Tuple[bool, str]:
        """Validate plot name"""
        if not name:
            return False, "Plot name is required"
        
        name = name.strip()
        
        if len(name) < 2:
            return False, "Plot name must be at least 2 characters long"
        
        if len(name) > 100:
            return False, "Plot name must be no more than 100 characters long"
        
        return True, ""
    
    @classmethod
    def validate_form_data(cls, form_data: Dict, validation_rules: Dict) -> Dict[str, str]:
        """Validate multiple form fields at once"""
        errors = {}
        
        for field, rules in validation_rules.items():
            value = form_data.get(field, '').strip() if form_data.get(field) else ''
            
            # Check required
            if rules.get('required', False) and not value:
                errors[field] = f"{rules.get('label', field.title())} is required"
                continue
            
            # Skip validation if field is empty and not required
            if not value and not rules.get('required', False):
                continue
            
            # Apply specific validation
            validation_type = rules.get('type')
            if validation_type == 'username':
                is_valid, error_msg = cls.validate_username(value)
            elif validation_type == 'password':
                is_valid, error_msg = cls.validate_password(value)
            elif validation_type == 'email':
                is_valid, error_msg = cls.validate_email(value, rules.get('required', False))
            elif validation_type == 'phone':
                is_valid, error_msg = cls.validate_phone(value, rules.get('required', False))
            elif validation_type == 'business_name':
                is_valid, error_msg = cls.validate_business_name(value)
            elif validation_type == 'address':
                is_valid, error_msg = cls.validate_address(value, rules.get('required', False))
            elif validation_type == 'analysis_prompt':
                is_valid, error_msg = cls.validate_analysis_prompt(value)
            elif validation_type == 'plot_name':
                is_valid, error_msg = cls.validate_plot_name(value)
            else:
                # Default validation - check length if specified
                min_length = rules.get('min_length')
                max_length = rules.get('max_length')
                
                if min_length and len(value) < min_length:
                    errors[field] = f"{rules.get('label', field.title())} must be at least {min_length} characters long"
                    continue
                
                if max_length and len(value) > max_length:
                    errors[field] = f"{rules.get('label', field.title())} must be no more than {max_length} characters long"
                    continue
                
                is_valid, error_msg = True, ""
            
            if not is_valid:
                errors[field] = error_msg
        
        return errors
    
    @classmethod
    def get_username_requirements(cls, username: str) -> Dict[str, bool]:
        """Get detailed username requirements for UI feedback"""
        username = username.strip() if username else ""
        return {
            "Length (3-20 characters)": 3 <= len(username) <= 20,
            "Contains only letters, numbers, underscores, hyphens, and periods": cls.USERNAME_PATTERN.match(username) is not None
        }
    
    @classmethod
    def get_password_requirements(cls, password: str) -> Dict[str, bool]:
        """Get detailed password requirements for UI feedback"""
        password = password.strip() if password else ""
        return {
            "Length (at least 3 characters)": len(password) >= 3,
            "Contains at least one letter": any(c.isalpha() for c in password),
            "Contains at least one number": any(c.isdigit() for c in password)
        }
    
    @classmethod
    def sanitize_input(cls, value: str) -> str:
        """Sanitize user input to prevent XSS"""
        if not value:
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&']
        for char in dangerous_chars:
            value = value.replace(char, '')
        
        return value.strip() 
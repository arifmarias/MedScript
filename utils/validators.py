"""
MedScript Pro - Form Validation Functions
This file contains comprehensive validation functions for all forms in the application.
"""

import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from config.settings import (
    VALIDATION_RULES, ERROR_MESSAGES, USER_TYPES, GENDER_OPTIONS,
    VISIT_TYPES, DRUG_CLASSES, STATUS_OPTIONS
)

class ValidationResult:
    """Class to hold validation results"""
    
    def __init__(self, is_valid: bool = True, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning message"""
        self.warnings.append(warning)
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0
    
    def get_all_messages(self) -> List[str]:
        """Get all error and warning messages"""
        return self.errors + self.warnings

def validate_required_field(value: Any, field_name: str) -> ValidationResult:
    """
    Validate that a required field has a value
    
    Args:
        value: The value to validate
        field_name (str): Name of the field for error messages
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    if value is None or (isinstance(value, str) and not value.strip()):
        result.add_error(f"{field_name} is required")
    
    return result

def validate_string_length(value: str, field_name: str, min_length: int = 0, 
                         max_length: int = None) -> ValidationResult:
    """
    Validate string length
    
    Args:
        value (str): String to validate
        field_name (str): Name of the field
        min_length (int): Minimum length
        max_length (int): Maximum length
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    if value is None:
        value = ""
    
    length = len(str(value).strip())
    
    if length < min_length:
        result.add_error(f"{field_name} must be at least {min_length} characters long")
    
    if max_length and length > max_length:
        result.add_error(f"{field_name} must not exceed {max_length} characters")
    
    return result

def validate_email(email: str) -> ValidationResult:
    """
    Validate email address format
    
    Args:
        email (str): Email address to validate
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    if not email or not email.strip():
        result.add_error("Email address is required")
        return result
    
    email = email.strip()
    pattern = VALIDATION_RULES['EMAIL']['PATTERN']
    
    if not re.match(pattern, email):
        result.add_error("Please enter a valid email address")
    
    return result

def validate_phone(phone: str) -> ValidationResult:
    """
    Validate phone number format
    
    Args:
        phone (str): Phone number to validate
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    if not phone or not phone.strip():
        result.add_error("Phone number is required")
        return result
    
    phone = phone.strip()
    pattern = VALIDATION_RULES['PHONE']['PATTERN']
    
    if not re.match(pattern, phone):
        result.add_error("Please enter a valid phone number (e.g., +1234567890)")
    
    return result

def validate_username(username: str) -> ValidationResult:
    """
    Validate username format and length
    
    Args:
        username (str): Username to validate
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    if not username or not username.strip():
        result.add_error("Username is required")
        return result
    
    username = username.strip()
    rules = VALIDATION_RULES['USERNAME']
    
    # Check length
    if len(username) < rules['MIN_LENGTH']:
        result.add_error(f"Username must be at least {rules['MIN_LENGTH']} characters long")
    
    if len(username) > rules['MAX_LENGTH']:
        result.add_error(f"Username must not exceed {rules['MAX_LENGTH']} characters")
    
    # Check pattern
    if not re.match(rules['PATTERN'], username):
        result.add_error("Username can only contain letters, numbers, and underscores")
    
    return result

def validate_password(password: str) -> ValidationResult:
    """
    Validate password strength
    
    Args:
        password (str): Password to validate
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    if not password:
        result.add_error("Password is required")
        return result
    
    rules = VALIDATION_RULES['PASSWORD']
    
    # Check length
    if len(password) < rules['MIN_LENGTH']:
        result.add_error(f"Password must be at least {rules['MIN_LENGTH']} characters long")
    
    if len(password) > rules['MAX_LENGTH']:
        result.add_error(f"Password must not exceed {rules['MAX_LENGTH']} characters")
    
    # Check for at least one letter and one number (recommended)
    if not re.search(r'[A-Za-z]', password):
        result.add_warning("Password should contain at least one letter")
    
    if not re.search(r'\d', password):
        result.add_warning("Password should contain at least one number")
    
    return result

def validate_medical_license(license_num: str) -> ValidationResult:
    """
    Validate medical license number format
    
    Args:
        license_num (str): Medical license number
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    if not license_num or not license_num.strip():
        # Medical license is optional for some roles
        return result
    
    license_num = license_num.strip()
    pattern = VALIDATION_RULES['MEDICAL_LICENSE']['PATTERN']
    
    if not re.match(pattern, license_num):
        result.add_error("Medical license should be in format: XX-YYYY-XXX (e.g., MD-2023-001)")
    
    return result

def validate_date(date_value: Union[str, date], field_name: str, 
                 allow_future: bool = True, allow_past: bool = True,
                 min_date: date = None, max_date: date = None) -> ValidationResult:
    """
    Validate date value and constraints
    
    Args:
        date_value: Date to validate
        field_name (str): Name of the field
        allow_future (bool): Whether future dates are allowed
        allow_past (bool): Whether past dates are allowed
        min_date (date): Minimum allowed date
        max_date (date): Maximum allowed date
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    if not date_value:
        result.add_error(f"{field_name} is required")
        return result
    
    # Convert string to date if needed
    if isinstance(date_value, str):
        try:
            date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
        except ValueError:
            result.add_error(f"{field_name} must be a valid date")
            return result
    
    today = date.today()
    
    # Check future/past constraints
    if not allow_future and date_value > today:
        result.add_error(f"{field_name} cannot be in the future")
    
    if not allow_past and date_value < today:
        result.add_error(f"{field_name} cannot be in the past")
    
    # Check min/max constraints
    if min_date and date_value < min_date:
        result.add_error(f"{field_name} cannot be earlier than {min_date}")
    
    if max_date and date_value > max_date:
        result.add_error(f"{field_name} cannot be later than {max_date}")
    
    return result

def validate_birth_date(birth_date: Union[str, date]) -> ValidationResult:
    """
    Validate birth date with age constraints
    
    Args:
        birth_date: Birth date to validate
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    # First validate basic date requirements
    date_result = validate_date(birth_date, "Date of birth", allow_future=False)
    if date_result.has_errors():
        result.errors.extend(date_result.errors)
        return result
    
    # Convert to date if string
    if isinstance(birth_date, str):
        birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
    
    # Check reasonable age limits
    today = date.today()
    age = today.year - birth_date.year
    
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    if age < 0:
        result.add_error("Birth date cannot be in the future")
    elif age > 150:
        result.add_error("Birth date seems unrealistic (age > 150 years)")
    
    return result

def validate_user_data(user_data: Dict[str, Any]) -> ValidationResult:
    """
    Validate complete user registration/update data
    
    Args:
        user_data (Dict[str, Any]): User data to validate
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    # Required fields
    required_fields = ['username', 'password', 'full_name', 'user_type']
    for field in required_fields:
        field_result = validate_required_field(user_data.get(field), field.replace('_', ' ').title())
        if field_result.has_errors():
            result.errors.extend(field_result.errors)
    
    # Username validation
    if user_data.get('username'):
        username_result = validate_username(user_data['username'])
        if username_result.has_errors():
            result.errors.extend(username_result.errors)
        if username_result.has_warnings():
            result.warnings.extend(username_result.warnings)
    
    # Password validation
    if user_data.get('password'):
        password_result = validate_password(user_data['password'])
        if password_result.has_errors():
            result.errors.extend(password_result.errors)
        if password_result.has_warnings():
            result.warnings.extend(password_result.warnings)
    
    # User type validation
    if user_data.get('user_type') and user_data['user_type'] not in USER_TYPES:
        result.add_error(f"User type must be one of: {', '.join(USER_TYPES)}")
    
    # Email validation (if provided)
    if user_data.get('email'):
        email_result = validate_email(user_data['email'])
        if email_result.has_errors():
            result.errors.extend(email_result.errors)
    
    # Phone validation (if provided)
    if user_data.get('phone'):
        phone_result = validate_phone(user_data['phone'])
        if phone_result.has_errors():
            result.errors.extend(phone_result.errors)
    
    # Medical license validation (for doctors)
    if user_data.get('user_type') == 'doctor' and user_data.get('medical_license'):
        license_result = validate_medical_license(user_data['medical_license'])
        if license_result.has_errors():
            result.errors.extend(license_result.errors)
    
    return result

def validate_patient_data(patient_data: Dict[str, Any]) -> ValidationResult:
    """
    Validate complete patient registration/update data
    
    Args:
        patient_data (Dict[str, Any]): Patient data to validate
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    # Required fields
    required_fields = ['first_name', 'last_name', 'date_of_birth', 'gender']
    for field in required_fields:
        field_result = validate_required_field(patient_data.get(field), field.replace('_', ' ').title())
        if field_result.has_errors():
            result.errors.extend(field_result.errors)
    
    # Name length validation
    if patient_data.get('first_name'):
        name_result = validate_string_length(patient_data['first_name'], "First name", 1, 100)
        if name_result.has_errors():
            result.errors.extend(name_result.errors)
    
    if patient_data.get('last_name'):
        name_result = validate_string_length(patient_data['last_name'], "Last name", 1, 100)
        if name_result.has_errors():
            result.errors.extend(name_result.errors)
    
    # Birth date validation
    if patient_data.get('date_of_birth'):
        birth_date_result = validate_birth_date(patient_data['date_of_birth'])
        if birth_date_result.has_errors():
            result.errors.extend(birth_date_result.errors)
    
    # Gender validation
    if patient_data.get('gender') and patient_data['gender'] not in GENDER_OPTIONS:
        result.add_error(f"Gender must be one of: {', '.join(GENDER_OPTIONS)}")
    
    # Email validation (if provided)
    if patient_data.get('email'):
        email_result = validate_email(patient_data['email'])
        if email_result.has_errors():
            result.errors.extend(email_result.errors)
    
    # Phone validation (if provided)
    if patient_data.get('phone'):
        phone_result = validate_phone(patient_data['phone'])
        if phone_result.has_errors():
            result.errors.extend(phone_result.errors)
    
    # Weight validation (if provided)
    if patient_data.get('weight'):
        try:
            weight = float(patient_data['weight'])
            if weight <= 0 or weight > 1000:  # kg
                result.add_error("Weight must be between 1 and 1000 kg")
        except (ValueError, TypeError):
            result.add_error("Weight must be a valid number")
    
    # Height validation (if provided)
    if patient_data.get('height'):
        try:
            height = float(patient_data['height'])
            if height <= 0 or height > 300:  # cm
                result.add_error("Height must be between 1 and 300 cm")
        except (ValueError, TypeError):
            result.add_error("Height must be a valid number")
    
    return result

def validate_visit_data(visit_data: Dict[str, Any]) -> ValidationResult:
    """
    Validate patient visit data
    
    Args:
        visit_data (Dict[str, Any]): Visit data to validate
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    # Required fields
    required_fields = ['patient_id', 'visit_date', 'visit_type', 'current_problems']
    for field in required_fields:
        field_result = validate_required_field(visit_data.get(field), field.replace('_', ' ').title())
        if field_result.has_errors():
            result.errors.extend(field_result.errors)
    
    # Visit date validation
    if visit_data.get('visit_date'):
        date_result = validate_date(visit_data['visit_date'], "Visit date")
        if date_result.has_errors():
            result.errors.extend(date_result.errors)
    
    # Visit type validation
    if visit_data.get('visit_type') and visit_data['visit_type'] not in VISIT_TYPES:
        result.add_error(f"Visit type must be one of: {', '.join(VISIT_TYPES)}")
    
    # Vital signs validation (if provided)
    if visit_data.get('temperature'):
        try:
            temp = float(visit_data['temperature'])
            if temp < 90 or temp > 110:  # Fahrenheit
                result.add_error("Temperature must be between 90 and 110°F")
        except (ValueError, TypeError):
            result.add_error("Temperature must be a valid number")
    
    if visit_data.get('pulse_rate'):
        try:
            pulse = int(visit_data['pulse_rate'])
            if pulse < 30 or pulse > 200:
                result.add_error("Pulse rate must be between 30 and 200 bpm")
        except (ValueError, TypeError):
            result.add_error("Pulse rate must be a valid number")
    
    if visit_data.get('respiratory_rate'):
        try:
            rr = int(visit_data['respiratory_rate'])
            if rr < 8 or rr > 40:
                result.add_error("Respiratory rate must be between 8 and 40 breaths/min")
        except (ValueError, TypeError):
            result.add_error("Respiratory rate must be a valid number")
    
    if visit_data.get('oxygen_saturation'):
        try:
            o2 = float(visit_data['oxygen_saturation'])
            if o2 < 70 or o2 > 100:
                result.add_error("Oxygen saturation must be between 70 and 100%")
        except (ValueError, TypeError):
            result.add_error("Oxygen saturation must be a valid number")
    
    # Blood pressure validation (if provided)
    if visit_data.get('blood_pressure'):
        bp = visit_data['blood_pressure'].strip()
        bp_pattern = r'^\d{2,3}/\d{2,3}$'
        if not re.match(bp_pattern, bp):
            result.add_error("Blood pressure must be in format: XXX/XX (e.g., 120/80)")
        else:
            try:
                systolic, diastolic = map(int, bp.split('/'))
                if systolic < 70 or systolic > 250:
                    result.add_error("Systolic blood pressure must be between 70 and 250 mmHg")
                if diastolic < 40 or diastolic > 150:
                    result.add_error("Diastolic blood pressure must be between 40 and 150 mmHg")
                if systolic <= diastolic:
                    result.add_error("Systolic pressure must be higher than diastolic pressure")
            except ValueError:
                result.add_error("Invalid blood pressure format")
    
    return result

def validate_medication_data(medication_data: Dict[str, Any]) -> ValidationResult:
    """
    Validate medication data
    
    Args:
        medication_data (Dict[str, Any]): Medication data to validate
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    # Required fields
    required_fields = ['name', 'generic_name', 'drug_class']
    for field in required_fields:
        field_result = validate_required_field(medication_data.get(field), field.replace('_', ' ').title())
        if field_result.has_errors():
            result.errors.extend(field_result.errors)
    
    # Name length validation
    if medication_data.get('name'):
        name_result = validate_string_length(medication_data['name'], "Medication name", 1, 200)
        if name_result.has_errors():
            result.errors.extend(name_result.errors)
    
    # Drug class validation
    if medication_data.get('drug_class') and medication_data['drug_class'] not in DRUG_CLASSES:
        result.add_warning(f"Drug class '{medication_data['drug_class']}' is not in the standard list")
    
    return result

def validate_prescription_data(prescription_data: Dict[str, Any]) -> ValidationResult:
    """
    Validate prescription data
    
    Args:
        prescription_data (Dict[str, Any]): Prescription data to validate
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    # Required fields
    required_fields = ['doctor_id', 'patient_id', 'diagnosis']
    for field in required_fields:
        field_result = validate_required_field(prescription_data.get(field), field.replace('_', ' ').title())
        if field_result.has_errors():
            result.errors.extend(field_result.errors)
    
    # Status validation
    if prescription_data.get('status'):
        valid_statuses = STATUS_OPTIONS.get('PRESCRIPTION', [])
        if prescription_data['status'] not in valid_statuses:
            result.add_error(f"Status must be one of: {', '.join(valid_statuses)}")
    
    # Follow-up date validation (if provided)
    if prescription_data.get('follow_up_date'):
        date_result = validate_date(prescription_data['follow_up_date'], "Follow-up date", allow_past=False)
        if date_result.has_errors():
            result.errors.extend(date_result.errors)
    
    return result

def validate_prescription_item_data(item_data: Dict[str, Any]) -> ValidationResult:
    """
    Validate prescription item (medication) data
    
    Args:
        item_data (Dict[str, Any]): Prescription item data to validate
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    # Required fields
    required_fields = ['medication_id', 'dosage', 'frequency', 'duration']
    for field in required_fields:
        field_result = validate_required_field(item_data.get(field), field.replace('_', ' ').title())
        if field_result.has_errors():
            result.errors.extend(field_result.errors)
    
    # Quantity validation (if provided)
    if item_data.get('quantity'):
        quantity_str = str(item_data['quantity']).strip()
        if not re.match(r'^\d+\s*(tablet|capsule|ml|mg|g|unit)s?$', quantity_str, re.IGNORECASE):
            result.add_warning("Quantity format should include units (e.g., '30 tablets', '100ml')")
    
    # Refills validation (if provided)
    if item_data.get('refills'):
        try:
            refills = int(item_data['refills'])
            if refills < 0 or refills > 12:
                result.add_error("Number of refills must be between 0 and 12")
        except (ValueError, TypeError):
            result.add_error("Number of refills must be a valid number")
    
    return result

def validate_lab_test_data(test_data: Dict[str, Any]) -> ValidationResult:
    """
    Validate lab test data
    
    Args:
        test_data (Dict[str, Any]): Lab test data to validate
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    # Required fields
    required_fields = ['test_name', 'test_category']
    for field in required_fields:
        field_result = validate_required_field(test_data.get(field), field.replace('_', ' ').title())
        if field_result.has_errors():
            result.errors.extend(field_result.errors)
    
    # Test name length validation
    if test_data.get('test_name'):
        name_result = validate_string_length(test_data['test_name'], "Test name", 1, 200)
        if name_result.has_errors():
            result.errors.extend(name_result.errors)
    
    # Cost validation (if provided)
    if test_data.get('cost'):
        try:
            cost = float(test_data['cost'])
            if cost < 0:
                result.add_error("Test cost cannot be negative")
            elif cost > 10000:
                result.add_warning("Test cost seems unusually high")
        except (ValueError, TypeError):
            result.add_error("Test cost must be a valid number")
    
    return result

def validate_search_query(query: str, min_length: int = 2) -> ValidationResult:
    """
    Validate search query
    
    Args:
        query (str): Search query to validate
        min_length (int): Minimum query length
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    if not query or not query.strip():
        result.add_error("Search query is required")
        return result
    
    query = query.strip()
    
    if len(query) < min_length:
        result.add_error(f"Search query must be at least {min_length} characters long")
    
    # Check for potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", ';', '(', ')', '&', '+']
    if any(char in query for char in dangerous_chars):
        result.add_error("Search query contains invalid characters")
    
    return result

def validate_file_upload(file_data: Any, allowed_types: List[str] = None, 
                        max_size_mb: int = 10) -> ValidationResult:
    """
    Validate file upload
    
    Args:
        file_data: Uploaded file data
        allowed_types (List[str]): Allowed file extensions
        max_size_mb (int): Maximum file size in MB
    
    Returns:
        ValidationResult: Validation result
    """
    result = ValidationResult()
    
    if not file_data:
        result.add_error("No file uploaded")
        return result
    
    # Check file size
    if hasattr(file_data, 'size'):
        file_size_mb = file_data.size / (1024 * 1024)
        if file_size_mb > max_size_mb:
            result.add_error(f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)")
    
    # Check file type
    if allowed_types and hasattr(file_data, 'name'):
        file_extension = '.' + file_data.name.split('.')[-1].lower()
        if file_extension not in [ext.lower() for ext in allowed_types]:
            result.add_error(f"File type not allowed. Allowed types: {', '.join(allowed_types)}")
    
    return result

def validate_bulk_data(data_list: List[Dict[str, Any]], 
                      validation_func: callable) -> Tuple[List[ValidationResult], int]:
    """
    Validate bulk data using specified validation function
    
    Args:
        data_list (List[Dict[str, Any]]): List of data to validate
        validation_func (callable): Validation function to use
    
    Returns:
        Tuple[List[ValidationResult], int]: Validation results and error count
    """
    results = []
    error_count = 0
    
    for i, data in enumerate(data_list):
        result = validation_func(data)
        results.append(result)
        
        if result.has_errors():
            error_count += 1
    
    return results, error_count

def get_validation_summary(validation_result: ValidationResult) -> Dict[str, Any]:
    """
    Get validation summary for display
    
    Args:
        validation_result (ValidationResult): Validation result to summarize
    
    Returns:
        Dict[str, Any]: Validation summary
    """
    return {
        'is_valid': validation_result.is_valid,
        'error_count': len(validation_result.errors),
        'warning_count': len(validation_result.warnings),
        'errors': validation_result.errors,
        'warnings': validation_result.warnings,
        'total_issues': len(validation_result.errors) + len(validation_result.warnings)
    }
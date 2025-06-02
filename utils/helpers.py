"""
MedScript Pro - Utility Helper Functions
This file contains common utility functions used throughout the application.
"""

import hashlib
import uuid
import re
import json
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Any, Union
import streamlit as st
from config.settings import (
    PRESCRIPTION_CONFIG, PATIENT_CONFIG, DATE_FORMATS,
    VALIDATION_RULES, ERROR_MESSAGES, SUCCESS_MESSAGES
)

def hash_password(password: str) -> str:
    """
    Hash password using SHA-256
    
    Args:
        password (str): Plain text password
    
    Returns:
        str: Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    
    Args:
        password (str): Plain text password
        hashed_password (str): Stored hash
    
    Returns:
        bool: True if password matches
    """
    return hash_password(password) == hashed_password

def generate_unique_id(prefix: str, date_obj: Optional[date] = None) -> str:
    """
    Generate unique ID with prefix and date
    
    Args:
        prefix (str): ID prefix (e.g., 'RX', 'PT')
        date_obj (Optional[date]): Date for ID generation
    
    Returns:
        str: Generated unique ID
    """
    if not date_obj:
        date_obj = date.today()
    
    date_str = date_obj.strftime(DATE_FORMATS['FILENAME'])
    sequence = generate_sequence_number()
    
    return f"{prefix}-{date_str}-{sequence:06d}"

def generate_sequence_number() -> int:
    """
    Generate sequence number for IDs
    
    Returns:
        int: Sequence number
    """
    # Generate a random sequence number for demonstration
    # In production, this would be based on database sequence
    import random
    return random.randint(1, 999999)

def format_date(date_obj: Union[date, datetime, str], format_type: str = 'DISPLAY') -> str:
    """
    Format date according to specified format
    
    Args:
        date_obj: Date object or string
        format_type (str): Format type from DATE_FORMATS
    
    Returns:
        str: Formatted date string
    """
    try:
        if isinstance(date_obj, str):
            # Try to parse string date
            if 'T' in date_obj:
                date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
            else:
                date_obj = datetime.strptime(date_obj, DATE_FORMATS['INPUT']).date()
        
        if isinstance(date_obj, datetime):
            date_obj = date_obj.date()
        
        return date_obj.strftime(DATE_FORMATS.get(format_type, DATE_FORMATS['DISPLAY']))
    
    except (ValueError, AttributeError):
        return str(date_obj)

def format_datetime(datetime_obj: Union[datetime, str], format_type: str = 'TIMESTAMP') -> str:
    """
    Format datetime according to specified format
    
    Args:
        datetime_obj: Datetime object or string
        format_type (str): Format type from DATE_FORMATS
    
    Returns:
        str: Formatted datetime string
    """
    try:
        if isinstance(datetime_obj, str):
            datetime_obj = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))
        
        return datetime_obj.strftime(DATE_FORMATS.get(format_type, DATE_FORMATS['TIMESTAMP']))
    
    except (ValueError, AttributeError):
        return str(datetime_obj)

def calculate_age(birth_date: Union[date, str]) -> int:
    """
    Calculate age from birth date
    
    Args:
        birth_date: Birth date object or string
    
    Returns:
        int: Age in years
    """
    try:
        if isinstance(birth_date, str):
            birth_date = datetime.strptime(birth_date, DATE_FORMATS['INPUT']).date()
        
        today = date.today()
        age = today.year - birth_date.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        
        return max(0, age)
    
    except (ValueError, AttributeError):
        return 0

def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email (str): Email address
    
    Returns:
        bool: True if valid email format
    """
    if not email:
        return False
    
    pattern = VALIDATION_RULES['EMAIL']['PATTERN']
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone (str): Phone number
    
    Returns:
        bool: True if valid phone format
    """
    if not phone:
        return False
    
    pattern = VALIDATION_RULES['PHONE']['PATTERN']
    return bool(re.match(pattern, phone))

def validate_medical_license(license_num: str) -> bool:
    """
    Validate medical license format
    
    Args:
        license_num (str): Medical license number
    
    Returns:
        bool: True if valid license format
    """
    if not license_num:
        return False
    
    pattern = VALIDATION_RULES['MEDICAL_LICENSE']['PATTERN']
    return bool(re.match(pattern, license_num))

def sanitize_input(input_str: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input by removing dangerous characters
    
    Args:
        input_str (str): Input string to sanitize
        max_length (Optional[int]): Maximum allowed length
    
    Returns:
        str: Sanitized string
    """
    if not input_str:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\';()&+]', '', str(input_str))
    
    # Limit length if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()

def format_currency(amount: Union[float, int, str]) -> str:
    """
    Format currency amount
    
    Args:
        amount: Amount to format
    
    Returns:
        str: Formatted currency string
    """
    try:
        amount_float = float(amount)
        return f"${amount_float:,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
        suffix (str): Suffix to append if truncated
    
    Returns:
        str: Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely load JSON string with fallback
    
    Args:
        json_str (str): JSON string to parse
        default (Any): Default value if parsing fails
    
    Returns:
        Any: Parsed JSON or default value
    """
    try:
        return json.loads(json_str) if json_str else default
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    Safely dump object to JSON string
    
    Args:
        obj (Any): Object to serialize
        default (str): Default JSON string if serialization fails
    
    Returns:
        str: JSON string
    """
    try:
        return json.dumps(obj, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return default

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get current user from session state
    
    Returns:
        Optional[Dict[str, Any]]: Current user data or None
    """
    return st.session_state.get('user')

def get_current_user_id() -> Optional[int]:
    """
    Get current user ID from session state
    
    Returns:
        Optional[int]: Current user ID or None
    """
    user = get_current_user()
    return user.get('id') if user else None

def get_current_user_role() -> Optional[str]:
    """
    Get current user role from session state
    
    Returns:
        Optional[str]: Current user role or None
    """
    user = get_current_user()
    return user.get('user_type') if user else None

def is_user_authenticated() -> bool:
    """
    Check if user is authenticated
    
    Returns:
        bool: True if user is authenticated
    """
    return 'user' in st.session_state and st.session_state.user is not None

def check_user_permission(required_roles: List[str]) -> bool:
    """
    Check if current user has required permissions
    
    Args:
        required_roles (List[str]): List of allowed roles
    
    Returns:
        bool: True if user has permission
    """
    user_role = get_current_user_role()
    return user_role in required_roles if user_role else False

def show_success_message(message: str, key: Optional[str] = None) -> None:
    """
    Show success message with consistent styling
    
    Args:
        message (str): Success message
        key (Optional[str]): Unique key for the message
    """
    if key:
        st.success(message, icon="✅")
    else:
        st.success(message, icon="✅")

def show_error_message(message: str, key: Optional[str] = None) -> None:
    """
    Show error message with consistent styling
    
    Args:
        message (str): Error message
        key (Optional[str]): Unique key for the message
    """
    if key:
        st.error(message, icon="❌")
    else:
        st.error(message, icon="❌")

def show_warning_message(message: str, key: Optional[str] = None) -> None:
    """
    Show warning message with consistent styling
    
    Args:
        message (str): Warning message
        key (Optional[str]): Unique key for the message
    """
    if key:
        st.warning(message, icon="⚠️")
    else:
        st.warning(message, icon="⚠️")

def show_info_message(message: str, key: Optional[str] = None) -> None:
    """
    Show info message with consistent styling
    
    Args:
        message (str): Info message
        key (Optional[str]): Unique key for the message
    """
    if key:
        st.info(message, icon="ℹ️")
    else:
        st.info(message, icon="ℹ️")

def format_list_for_display(items: List[str], separator: str = ", ", max_items: int = 3) -> str:
    """
    Format list of items for display with truncation
    
    Args:
        items (List[str]): List of items
        separator (str): Separator between items
        max_items (int): Maximum items to show before truncation
    
    Returns:
        str: Formatted string
    """
    if not items:
        return "None"
    
    if len(items) <= max_items:
        return separator.join(items)
    else:
        visible_items = items[:max_items]
        remaining = len(items) - max_items
        return f"{separator.join(visible_items)}, +{remaining} more"

def extract_keywords_from_text(text: str, min_length: int = 3) -> List[str]:
    """
    Extract keywords from text for search functionality
    
    Args:
        text (str): Text to extract keywords from
        min_length (int): Minimum keyword length
    
    Returns:
        List[str]: List of keywords
    """
    if not text:
        return []
    
    # Split text and filter
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [word for word in words if len(word) >= min_length]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return unique_keywords

def generate_session_id() -> str:
    """
    Generate unique session ID
    
    Returns:
        str: Session ID
    """
    return str(uuid.uuid4())

def get_time_ago(datetime_obj: Union[datetime, str]) -> str:
    """
    Get human-readable time ago string
    
    Args:
        datetime_obj: Datetime object or string
    
    Returns:
        str: Time ago string (e.g., "2 hours ago")
    """
    try:
        if isinstance(datetime_obj, str):
            datetime_obj = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))
        
        now = datetime.now()
        if datetime_obj.tzinfo is not None:
            now = now.replace(tzinfo=datetime_obj.tzinfo)
        
        diff = now - datetime_obj
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 2592000:
            days = int(seconds // 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif seconds < 31536000:
            months = int(seconds // 2592000)
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = int(seconds // 31536000)
            return f"{years} year{'s' if years != 1 else ''} ago"
    
    except (ValueError, AttributeError, TypeError):
        return "Unknown"

def convert_to_title_case(text: str) -> str:
    """
    Convert text to title case with proper handling of medical terms
    
    Args:
        text (str): Text to convert
    
    Returns:
        str: Title case text
    """
    if not text:
        return ""
    
    # Common medical abbreviations to keep uppercase
    medical_abbreviations = {
        'bp', 'hr', 'rr', 'temp', 'o2', 'ecg', 'ekg', 'ct', 'mri', 'xray',
        'hiv', 'aids', 'copd', 'gerd', 'ptsd', 'adhd', 'uti', 'mi', 'pe',
        'dvt', 'ibs', 'crp', 'esr', 'cbc', 'bmp', 'cmp', 'tsh', 'psa'
    }
    
    words = text.lower().split()
    title_words = []
    
    for word in words:
        clean_word = re.sub(r'[^\w]', '', word)
        if clean_word in medical_abbreviations:
            title_words.append(word.upper())
        else:
            title_words.append(word.capitalize())
    
    return ' '.join(title_words)

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Validate required fields in data dictionary
    
    Args:
        data (Dict[str, Any]): Data to validate
        required_fields (List[str]): List of required field names
    
    Returns:
        List[str]: List of missing fields
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or not data[field] or (isinstance(data[field], str) and not data[field].strip()):
            missing_fields.append(field)
    
    return missing_fields

def create_download_link(data: bytes, filename: str, mime_type: str = "application/octet-stream") -> str:
    """
    Create download link for binary data
    
    Args:
        data (bytes): Binary data
        filename (str): Download filename
        mime_type (str): MIME type
    
    Returns:
        str: Download link HTML
    """
    import base64
    
    b64_data = base64.b64encode(data).decode()
    return f'<a href="data:{mime_type};base64,{b64_data}" download="{filename}">Download {filename}</a>'

def log_user_activity(action_type: str, entity_type: str = None, entity_id: int = None, 
                     metadata: Dict[str, Any] = None) -> None:
    """
    Log user activity for analytics
    
    Args:
        action_type (str): Type of action performed
        entity_type (str): Type of entity affected
        entity_id (int): ID of entity affected
        metadata (Dict[str, Any]): Additional metadata
    """
    try:
        from config.database import execute_query
        
        user_id = get_current_user_id()
        if not user_id:
            return
        
        query = """
        INSERT INTO analytics (
            user_id, action_type, entity_type, entity_id, metadata
        ) VALUES (?, ?, ?, ?, ?)
        """
        
        params = (
            user_id, action_type, entity_type, entity_id,
            safe_json_dumps(metadata) if metadata else None
        )
        
        execute_query(query, params)
    
    except Exception:
        # Silently fail for logging - don't break main functionality
        pass

def get_file_size_string(size_bytes: int) -> str:
    """
    Convert file size in bytes to human readable string
    
    Args:
        size_bytes (int): Size in bytes
    
    Returns:
        str: Human readable size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

def clean_filename(filename: str) -> str:
    """
    Clean filename by removing invalid characters
    
    Args:
        filename (str): Original filename
    
    Returns:
        str: Cleaned filename
    """
    # Remove invalid characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    cleaned = cleaned.strip(' .')
    
    # Ensure filename is not empty
    if not cleaned:
        cleaned = "unnamed_file"
    
    return cleaned

def is_today(date_obj: Union[date, datetime, str]) -> bool:
    """
    Check if date is today
    
    Args:
        date_obj: Date to check
    
    Returns:
        bool: True if date is today
    """
    try:
        if isinstance(date_obj, str):
            date_obj = datetime.strptime(date_obj, DATE_FORMATS['INPUT']).date()
        elif isinstance(date_obj, datetime):
            date_obj = date_obj.date()
        
        return date_obj == date.today()
    
    except (ValueError, AttributeError):
        return False

def get_days_between(start_date: Union[date, str], end_date: Union[date, str]) -> int:
    """
    Get number of days between two dates
    
    Args:
        start_date: Start date
        end_date: End date
    
    Returns:
        int: Number of days between dates
    """
    try:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, DATE_FORMATS['INPUT']).date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, DATE_FORMATS['INPUT']).date()
        
        return (end_date - start_date).days
    
    except (ValueError, AttributeError):
        return 0

def format_medical_condition(condition: str) -> str:
    """
    Format medical condition name properly
    
    Args:
        condition (str): Medical condition name
    
    Returns:
        str: Properly formatted condition name
    """
    if not condition:
        return ""
    
    # Common medical terms that should remain capitalized
    caps_terms = ['HIV', 'AIDS', 'COPD', 'GERD', 'PTSD', 'ADHD', 'UTI', 'MI', 'CHF', 'DVT', 'PE']
    
    words = condition.split()
    formatted_words = []
    
    for word in words:
        if word.upper() in caps_terms:
            formatted_words.append(word.upper())
        else:
            formatted_words.append(word.capitalize())
    
    return ' '.join(formatted_words)

def generate_patient_summary(patient_data: Dict[str, Any]) -> str:
    """
    Generate patient summary for display
    
    Args:
        patient_data (Dict[str, Any]): Patient data
    
    Returns:
        str: Patient summary
    """
    try:
        age = calculate_age(patient_data.get('date_of_birth', ''))
        gender = patient_data.get('gender', 'Unknown')
        
        summary_parts = [f"{age}-year-old {gender.lower()}"]
        
        if patient_data.get('medical_conditions'):
            conditions = patient_data['medical_conditions'].split(',')[:2]  # First 2 conditions
            conditions_str = ', '.join([condition.strip() for condition in conditions])
            summary_parts.append(f"with {conditions_str}")
        
        if patient_data.get('allergies') and patient_data['allergies'].lower() != 'none':
            allergies = patient_data['allergies'].split(',')[:2]  # First 2 allergies
            allergies_str = ', '.join([allergy.strip() for allergy in allergies])
            summary_parts.append(f"allergic to {allergies_str}")
        
        return '; '.join(summary_parts)
    
    except Exception:
        return "Patient information available"
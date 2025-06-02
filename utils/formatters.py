"""
MedScript Pro - Data Formatting Utilities
This file contains functions to format data for display in the user interface.
"""

import re
import json
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Union
from config.settings import DATE_FORMATS, CHART_CONFIG

def format_patient_name(first_name: str, last_name: str, format_type: str = 'full') -> str:
    """
    Format patient name for display
    
    Args:
        first_name (str): Patient's first name
        last_name (str): Patient's last name
        format_type (str): 'full', 'last_first', 'initials', 'formal'
    
    Returns:
        str: Formatted name
    """
    if not first_name and not last_name:
        return "Unknown Patient"
    
    first_name = str(first_name).strip() if first_name else ""
    last_name = str(last_name).strip() if last_name else ""
    
    if format_type == 'full':
        return f"{first_name} {last_name}".strip()
    elif format_type == 'last_first':
        return f"{last_name}, {first_name}".strip(', ')
    elif format_type == 'initials':
        first_initial = first_name[0].upper() if first_name else ""
        last_initial = last_name[0].upper() if last_name else ""
        return f"{first_initial}{last_initial}"
    elif format_type == 'formal':
        return f"{last_name.upper()}, {first_name}".strip(', ')
    else:
        return f"{first_name} {last_name}".strip()

def format_user_name(full_name: str, user_type: str = None) -> str:
    """
    Format user name with appropriate title
    
    Args:
        full_name (str): User's full name
        user_type (str): User type for title formatting
    
    Returns:
        str: Formatted name with title
    """
    if not full_name:
        return "Unknown User"
    
    full_name = str(full_name).strip()
    
    if user_type == 'doctor':
        if not full_name.startswith('Dr.'):
            return f"Dr. {full_name}"
    elif user_type == 'super_admin':
        return f"{full_name} (Admin)"
    
    return full_name

def format_age_from_birth_date(birth_date: Union[str, date], include_unit: bool = True) -> str:
    """
    Format age from birth date
    
    Args:
        birth_date: Birth date
        include_unit (bool): Whether to include 'years old'
    
    Returns:
        str: Formatted age string
    """
    try:
        if isinstance(birth_date, str):
            birth_date = datetime.strptime(birth_date, DATE_FORMATS['INPUT']).date()
        
        today = date.today()
        age = today.year - birth_date.year
        
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        
        if include_unit:
            return f"{age} years old"
        else:
            return str(age)
    
    except (ValueError, AttributeError, TypeError):
        return "Unknown age"

def format_date_display(date_obj: Union[str, date, datetime], format_type: str = 'display') -> str:
    """
    Format date for display with various formats
    
    Args:
        date_obj: Date to format
        format_type (str): Format type ('display', 'short', 'long', 'relative')
    
    Returns:
        str: Formatted date string
    """
    try:
        if isinstance(date_obj, str):
            if 'T' in date_obj:
                date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
            else:
                date_obj = datetime.strptime(date_obj, DATE_FORMATS['INPUT']).date()
        
        if isinstance(date_obj, datetime):
            date_obj = date_obj.date()
        
        if format_type == 'display':
            return date_obj.strftime(DATE_FORMATS['DISPLAY'])
        elif format_type == 'short':
            return date_obj.strftime('%m/%d/%Y')
        elif format_type == 'long':
            return date_obj.strftime('%A, %B %d, %Y')
        elif format_type == 'relative':
            return format_relative_date(date_obj)
        else:
            return date_obj.strftime(DATE_FORMATS['DISPLAY'])
    
    except (ValueError, AttributeError, TypeError):
        return str(date_obj) if date_obj else "N/A"

def format_relative_date(date_obj: Union[str, date]) -> str:
    """
    Format date relative to today (e.g., 'Today', 'Yesterday', '3 days ago')
    
    Args:
        date_obj: Date to format
    
    Returns:
        str: Relative date string
    """
    try:
        if isinstance(date_obj, str):
            date_obj = datetime.strptime(date_obj, DATE_FORMATS['INPUT']).date()
        
        today = date.today()
        diff = (today - date_obj).days
        
        if diff == 0:
            return "Today"
        elif diff == 1:
            return "Yesterday"
        elif diff == -1:
            return "Tomorrow"
        elif diff > 1:
            if diff < 7:
                return f"{diff} days ago"
            elif diff < 30:
                weeks = diff // 7
                return f"{weeks} week{'s' if weeks != 1 else ''} ago"
            elif diff < 365:
                months = diff // 30
                return f"{months} month{'s' if months != 1 else ''} ago"
            else:
                years = diff // 365
                return f"{years} year{'s' if years != 1 else ''} ago"
        else:  # Future dates
            diff = abs(diff)
            if diff < 7:
                return f"In {diff} days"
            elif diff < 30:
                weeks = diff // 7
                return f"In {weeks} week{'s' if weeks != 1 else ''}"
            elif diff < 365:
                months = diff // 30
                return f"In {months} month{'s' if months != 1 else ''}"
            else:
                years = diff // 365
                return f"In {years} year{'s' if years != 1 else ''}"
    
    except (ValueError, AttributeError, TypeError):
        return str(date_obj) if date_obj else "N/A"

def format_datetime_display(datetime_obj: Union[str, datetime], include_seconds: bool = False) -> str:
    """
    Format datetime for display
    
    Args:
        datetime_obj: Datetime to format
        include_seconds (bool): Whether to include seconds
    
    Returns:
        str: Formatted datetime string
    """
    try:
        if isinstance(datetime_obj, str):
            datetime_obj = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))
        
        if include_seconds:
            return datetime_obj.strftime('%B %d, %Y at %I:%M:%S %p')
        else:
            return datetime_obj.strftime('%B %d, %Y at %I:%M %p')
    
    except (ValueError, AttributeError, TypeError):
        return str(datetime_obj) if datetime_obj else "N/A"

def format_time_display(time_obj: Union[str, datetime], format_12hour: bool = True) -> str:
    """
    Format time for display
    
    Args:
        time_obj: Time to format
        format_12hour (bool): Whether to use 12-hour format
    
    Returns:
        str: Formatted time string
    """
    try:
        if isinstance(time_obj, str):
            if ':' in time_obj:
                time_obj = datetime.strptime(time_obj, '%H:%M:%S').time()
            else:
                time_obj = datetime.fromisoformat(time_obj)
        
        if isinstance(time_obj, datetime):
            time_obj = time_obj.time()
        
        if format_12hour:
            return datetime.combine(date.today(), time_obj).strftime('%I:%M %p')
        else:
            return time_obj.strftime('%H:%M')
    
    except (ValueError, AttributeError, TypeError):
        return str(time_obj) if time_obj else "N/A"

def format_phone_number(phone: str) -> str:
    """
    Format phone number for display
    
    Args:
        phone (str): Phone number to format
    
    Returns:
        str: Formatted phone number
    """
    if not phone:
        return "N/A"
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', str(phone))
    
    # Format based on length
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    elif len(digits) > 10:
        return f"+{digits[:-10]} ({digits[-10:-7]}) {digits[-7:-4]}-{digits[-4:]}"
    else:
        return phone

def format_email_display(email: str, max_length: int = 30) -> str:
    """
    Format email for display with truncation
    
    Args:
        email (str): Email address
        max_length (int): Maximum display length
    
    Returns:
        str: Formatted email
    """
    if not email:
        return "N/A"
    
    email = str(email).strip()
    
    if len(email) <= max_length:
        return email
    else:
        # Truncate while preserving domain
        local, domain = email.split('@', 1) if '@' in email else (email, '')
        if domain:
            available_length = max_length - len(domain) - 4  # 4 for '@...'
            if available_length > 3:
                return f"{local[:available_length]}...@{domain}"
        
        return f"{email[:max_length-3]}..."

def format_address_display(address: str, max_lines: int = 2) -> str:
    """
    Format address for display
    
    Args:
        address (str): Address to format
        max_lines (int): Maximum number of lines
    
    Returns:
        str: Formatted address
    """
    if not address:
        return "N/A"
    
    address = str(address).strip()
    
    # Split by common delimiters
    parts = re.split(r'[,\n\r]+', address)
    parts = [part.strip() for part in parts if part.strip()]
    
    if len(parts) <= max_lines:
        return '\n'.join(parts)
    else:
        return '\n'.join(parts[:max_lines-1] + [f"... (+{len(parts)-max_lines+1} more)"])

def format_medical_conditions(conditions: str, max_display: int = 3) -> str:
    """
    Format medical conditions for display
    
    Args:
        conditions (str): Medical conditions string
        max_display (int): Maximum conditions to display
    
    Returns:
        str: Formatted conditions string
    """
    if not conditions:
        return "None reported"
    
    conditions = str(conditions).strip()
    
    # Split by common delimiters
    condition_list = re.split(r'[,;]+', conditions)
    condition_list = [condition.strip().title() for condition in condition_list if condition.strip()]
    
    if not condition_list:
        return "None reported"
    
    if len(condition_list) <= max_display:
        return ', '.join(condition_list)
    else:
        displayed = condition_list[:max_display]
        remaining = len(condition_list) - max_display
        return f"{', '.join(displayed)}, +{remaining} more"

def format_allergies(allergies: str, max_display: int = 3) -> str:
    """
    Format allergies for display with warning styling
    
    Args:
        allergies (str): Allergies string
        max_display (int): Maximum allergies to display
    
    Returns:
        str: Formatted allergies string
    """
    if not allergies or allergies.lower().strip() in ['none', 'none known', 'nka', 'nkda']:
        return "None known"
    
    allergies = str(allergies).strip()
    
    # Split by common delimiters
    allergy_list = re.split(r'[,;]+', allergies)
    allergy_list = [allergy.strip().title() for allergy in allergy_list if allergy.strip()]
    
    if not allergy_list:
        return "None known"
    
    if len(allergy_list) <= max_display:
        return ', '.join(allergy_list)
    else:
        displayed = allergy_list[:max_display]
        remaining = len(allergy_list) - max_display
        return f"{', '.join(displayed)}, +{remaining} more"

def format_vital_signs(visit_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Format vital signs for display
    
    Args:
        visit_data (Dict[str, Any]): Visit data containing vital signs
    
    Returns:
        Dict[str, str]: Formatted vital signs
    """
    vital_signs = {}
    
    # Blood pressure
    if visit_data.get('blood_pressure'):
        vital_signs['Blood Pressure'] = f"{visit_data['blood_pressure']} mmHg"
    
    # Temperature
    if visit_data.get('temperature'):
        temp = float(visit_data['temperature'])
        vital_signs['Temperature'] = f"{temp:.1f}°F"
    
    # Pulse rate
    if visit_data.get('pulse_rate'):
        vital_signs['Pulse'] = f"{visit_data['pulse_rate']} bpm"
    
    # Respiratory rate
    if visit_data.get('respiratory_rate'):
        vital_signs['Respiratory Rate'] = f"{visit_data['respiratory_rate']} breaths/min"
    
    # Oxygen saturation
    if visit_data.get('oxygen_saturation'):
        o2_sat = float(visit_data['oxygen_saturation'])
        vital_signs['Oxygen Saturation'] = f"{o2_sat:.1f}%"
    
    return vital_signs

def format_medication_dosage(dosage: str, frequency: str, duration: str) -> str:
    """
    Format medication dosage for display
    
    Args:
        dosage (str): Medication dosage
        frequency (str): Dosage frequency
        duration (str): Treatment duration
    
    Returns:
        str: Formatted dosage string
    """
    parts = []
    
    if dosage:
        parts.append(str(dosage).strip())
    
    if frequency:
        parts.append(str(frequency).strip().lower())
    
    if duration:
        parts.append(f"for {str(duration).strip()}")
    
    return ' '.join(parts) if parts else "As directed"

def format_prescription_status(status: str) -> str:
    """
    Format prescription status with appropriate styling
    
    Args:
        status (str): Prescription status
    
    Returns:
        str: Formatted status string
    """
    status_map = {
        'active': '🟢 Active',
        'completed': '✅ Completed',
        'cancelled': '❌ Cancelled',
        'pending': '🟡 Pending'
    }
    
    status_lower = str(status).lower().strip() if status else 'unknown'
    return status_map.get(status_lower, f"❓ {status.title()}")

def format_visit_type(visit_type: str) -> str:
    """
    Format visit type with appropriate icon
    
    Args:
        visit_type (str): Visit type
    
    Returns:
        str: Formatted visit type with icon
    """
    if not visit_type:
        return "📅 General Visit"
    
    visit_type = str(visit_type).strip()
    
    icon_map = {
        'initial consultation': '🆕',
        'follow-up': '🔄',
        'emergency': '🚨',
        'routine check-up': '📋',
        'vaccination': '💉',
        'report consultation': '📄',
        'teleconsultation': '💻'
    }
    
    icon = icon_map.get(visit_type.lower(), '📅')
    return f"{icon} {visit_type}"

def format_urgency_level(urgency: str) -> str:
    """
    Format lab test urgency level
    
    Args:
        urgency (str): Urgency level
    
    Returns:
        str: Formatted urgency with styling
    """
    if not urgency:
        return "📅 Routine"
    
    urgency_lower = str(urgency).lower().strip()
    
    urgency_map = {
        'routine': '📅 Routine',
        'urgent': '⚡ Urgent',
        'stat': '🚨 STAT'
    }
    
    return urgency_map.get(urgency_lower, f"📅 {urgency.title()}")

def format_currency(amount: Union[str, int, float], currency_symbol: str = '$') -> str:
    """
    Format currency amount
    
    Args:
        amount: Amount to format
        currency_symbol (str): Currency symbol
    
    Returns:
        str: Formatted currency string
    """
    try:
        amount_float = float(amount) if amount else 0.0
        return f"{currency_symbol}{amount_float:,.2f}"
    except (ValueError, TypeError):
        return f"{currency_symbol}0.00"

def format_percentage(value: Union[str, int, float], decimal_places: int = 1) -> str:
    """
    Format percentage value
    
    Args:
        value: Value to format as percentage
        decimal_places (int): Number of decimal places
    
    Returns:
        str: Formatted percentage string
    """
    try:
        value_float = float(value) if value else 0.0
        return f"{value_float:.{decimal_places}f}%"
    except (ValueError, TypeError):
        return "0.0%"

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
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

def format_json_for_display(json_str: str, max_length: int = 100) -> str:
    """
    Format JSON string for display
    
    Args:
        json_str (str): JSON string
        max_length (int): Maximum display length
    
    Returns:
        str: Formatted JSON for display
    """
    if not json_str:
        return "No data"
    
    try:
        # Try to parse and pretty print
        data = json.loads(json_str)
        pretty_json = json.dumps(data, indent=2)
        
        if len(pretty_json) <= max_length:
            return pretty_json
        else:
            return f"{pretty_json[:max_length-3]}..."
    
    except json.JSONDecodeError:
        # If not valid JSON, return as string
        if len(json_str) <= max_length:
            return json_str
        else:
            return f"{json_str[:max_length-3]}..."

def format_search_results_summary(total_results: int, page: int = 1, 
                                page_size: int = 25) -> str:
    """
    Format search results summary
    
    Args:
        total_results (int): Total number of results
        page (int): Current page number
        page_size (int): Results per page
    
    Returns:
        str: Formatted results summary
    """
    if total_results == 0:
        return "No results found"
    
    start_result = (page - 1) * page_size + 1
    end_result = min(page * page_size, total_results)
    
    if total_results == 1:
        return "1 result found"
    elif total_results <= page_size:
        return f"{total_results} results found"
    else:
        return f"Showing {start_result}-{end_result} of {total_results} results"

def format_list_display(items: List[str], max_items: int = 5, 
                       separator: str = ", ") -> str:
    """
    Format list for display with truncation
    
    Args:
        items (List[str]): List of items
        max_items (int): Maximum items to display
        separator (str): Separator between items
    
    Returns:
        str: Formatted list string
    """
    if not items:
        return "None"
    
    items = [str(item).strip() for item in items if item]
    
    if not items:
        return "None"
    
    if len(items) <= max_items:
        return separator.join(items)
    else:
        displayed = items[:max_items]
        remaining = len(items) - max_items
        return f"{separator.join(displayed)}{separator}+{remaining} more"

def format_medication_summary(medication_data: Dict[str, Any]) -> str:
    """
    Format medication summary for display
    
    Args:
        medication_data (Dict[str, Any]): Medication data
    
    Returns:
        str: Formatted medication summary
    """
    name = medication_data.get('name', 'Unknown Medication')
    generic_name = medication_data.get('generic_name', '')
    dosage_forms = medication_data.get('dosage_forms', '')
    
    summary_parts = [name]
    
    if generic_name and generic_name.lower() != name.lower():
        summary_parts.append(f"({generic_name})")
    
    if dosage_forms:
        forms = dosage_forms.split(',')[:2]  # First 2 forms
        forms_str = ', '.join([form.strip() for form in forms])
        summary_parts.append(f"- {forms_str}")
    
    return ' '.join(summary_parts)

def format_patient_summary_card(patient_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Format patient data for summary card display
    
    Args:
        patient_data (Dict[str, Any]): Patient data
    
    Returns:
        Dict[str, str]: Formatted patient summary
    """
    summary = {}
    
    # Name and basic info
    name = format_patient_name(
        patient_data.get('first_name', ''),
        patient_data.get('last_name', '')
    )
    summary['name'] = name
    
    # Age and gender
    age = format_age_from_birth_date(patient_data.get('date_of_birth', ''))
    gender = patient_data.get('gender', 'Unknown')
    summary['demographics'] = f"{age}, {gender}"
    
    # Patient ID
    summary['patient_id'] = patient_data.get('patient_id', 'Unknown')
    
    # Contact
    phone = format_phone_number(patient_data.get('phone', ''))
    summary['phone'] = phone
    
    # Medical conditions
    conditions = format_medical_conditions(patient_data.get('medical_conditions', ''))
    summary['conditions'] = conditions
    
    # Allergies
    allergies = format_allergies(patient_data.get('allergies', ''))
    summary['allergies'] = allergies
    
    return summary

def truncate_text_smart(text: str, max_length: int = 100, 
                       preserve_words: bool = True) -> str:
    """
    Smart text truncation that preserves word boundaries
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
        preserve_words (bool): Whether to preserve word boundaries
    
    Returns:
        str: Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    if not preserve_words:
        return f"{text[:max_length-3]}..."
    
    # Find the last space before max_length
    truncated = text[:max_length-3]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If space is reasonably close to end
        return f"{text[:last_space]}..."
    else:
        return f"{text[:max_length-3]}..."
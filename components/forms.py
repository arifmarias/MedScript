"""
MedScript Pro - Reusable Form Components
This file contains reusable form components used throughout the application.
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
import streamlit as st
from config.settings import (
    USER_TYPES, GENDER_OPTIONS, VISIT_TYPES, DRUG_CLASSES,
    VALIDATION_RULES, TEMPLATE_CONFIG
)
from utils.validators import (
    validate_email, validate_phone, validate_username, validate_password,
    validate_medical_license, validate_birth_date, ValidationResult
)
from utils.formatters import format_date_display, format_phone_number
from utils.helpers import calculate_age

class FormComponent:
    """Base class for form components"""
    
    def __init__(self, label: str, key: str, required: bool = False, 
                 help_text: str = None, disabled: bool = False):
        self.label = label
        self.key = key
        self.required = required
        self.help_text = help_text
        self.disabled = disabled
        self.validation_errors = []
    
    def validate(self, value: Any) -> ValidationResult:
        """Validate form component value"""
        result = ValidationResult()
        
        if self.required and (value is None or value == "" or value == []):
            result.add_error(f"{self.label} is required")
        
        return result
    
    def render(self) -> Any:
        """Render the form component"""
        raise NotImplementedError("Subclasses must implement render method")

class TextInputComponent(FormComponent):
    """Text input component with validation"""
    
    def __init__(self, label: str, key: str, value: str = "", 
                 placeholder: str = "", max_chars: int = None, **kwargs):
        super().__init__(label, key, **kwargs)
        self.value = value
        self.placeholder = placeholder
        self.max_chars = max_chars
    
    def render(self) -> str:
        """Render text input"""
        return st.text_input(
            self.label,
            value=self.value,
            placeholder=self.placeholder,
            max_chars=self.max_chars,
            help=self.help_text,
            disabled=self.disabled,
            key=self.key
        )

class TextAreaComponent(FormComponent):
    """Text area component for longer text"""
    
    def __init__(self, label: str, key: str, value: str = "", 
                 height: int = 100, max_chars: int = None, **kwargs):
        super().__init__(label, key, **kwargs)
        self.value = value
        self.height = height
        self.max_chars = max_chars
    
    def render(self) -> str:
        """Render text area"""
        return st.text_area(
            self.label,
            value=self.value,
            height=self.height,
            max_chars=self.max_chars,
            help=self.help_text,
            disabled=self.disabled,
            key=self.key
        )

class EmailInputComponent(FormComponent):
    """Email input with validation"""
    
    def __init__(self, label: str = "Email", key: str = "email", 
                 value: str = "", **kwargs):
        super().__init__(label, key, **kwargs)
        self.value = value
    
    def validate(self, value: str) -> ValidationResult:
        """Validate email address"""
        result = super().validate(value)
        
        if value and not validate_email(value).is_valid:
            result.add_error("Please enter a valid email address")
        
        return result
    
    def render(self) -> str:
        """Render email input"""
        return st.text_input(
            self.label,
            value=self.value,
            placeholder="user@example.com",
            help=self.help_text,
            disabled=self.disabled,
            key=self.key
        )

class PhoneInputComponent(FormComponent):
    """Phone input with validation"""
    
    def __init__(self, label: str = "Phone", key: str = "phone", 
                 value: str = "", **kwargs):
        super().__init__(label, key, **kwargs)
        self.value = value
    
    def validate(self, value: str) -> ValidationResult:
        """Validate phone number"""
        result = super().validate(value)
        
        if value and not validate_phone(value).is_valid:
            result.add_error("Please enter a valid phone number")
        
        return result
    
    def render(self) -> str:
        """Render phone input"""
        return st.text_input(
            self.label,
            value=self.value,
            placeholder="+1234567890",
            help=self.help_text or "Include country code (e.g., +1234567890)",
            disabled=self.disabled,
            key=self.key
        )

class DateInputComponent(FormComponent):
    """Date input component"""
    
    def __init__(self, label: str, key: str, value: date = None,
                 min_value: date = None, max_value: date = None, **kwargs):
        super().__init__(label, key, **kwargs)
        self.value = value or date.today()
        self.min_value = min_value
        self.max_value = max_value
    
    def render(self) -> date:
        """Render date input"""
        return st.date_input(
            self.label,
            value=self.value,
            min_value=self.min_value,
            max_value=self.max_value,
            help=self.help_text,
            disabled=self.disabled,
            key=self.key
        )

class BirthDateComponent(DateInputComponent):
    """Birth date input with age calculation"""
    
    def __init__(self, label: str = "Date of Birth", key: str = "date_of_birth",
                 value: date = None, **kwargs):
        # Set reasonable limits for birth date
        max_date = date.today()
        min_date = date(1900, 1, 1)
        
        super().__init__(label, key, value, min_date, max_date, **kwargs)
    
    def validate(self, value: date) -> ValidationResult:
        """Validate birth date"""
        result = super().validate(value)
        
        if value:
            birth_validation = validate_birth_date(value)
            if birth_validation.has_errors():
                for error in birth_validation.errors:
                    result.add_error(error)
        
        return result
    
    def render(self) -> Tuple[date, int]:
        """Render birth date input and show calculated age"""
        birth_date = super().render()
        
        if birth_date:
            age = calculate_age(birth_date)
            st.caption(f"Age: {age} years old")
            return birth_date, age
        
        return birth_date, 0

class SelectBoxComponent(FormComponent):
    """Select box component"""
    
    def __init__(self, label: str, key: str, options: List[str], 
                 index: int = 0, **kwargs):
        super().__init__(label, key, **kwargs)
        self.options = options
        self.index = index
    
    def render(self) -> str:
        """Render select box"""
        return st.selectbox(
            self.label,
            options=self.options,
            index=self.index,
            help=self.help_text,
            disabled=self.disabled,
            key=self.key
        )

class MultiSelectComponent(FormComponent):
    """Multi-select component"""
    
    def __init__(self, label: str, key: str, options: List[str], 
                 default: List[str] = None, **kwargs):
        super().__init__(label, key, **kwargs)
        self.options = options
        self.default = default or []
    
    def render(self) -> List[str]:
        """Render multi-select"""
        return st.multiselect(
            self.label,
            options=self.options,
            default=self.default,
            help=self.help_text,
            disabled=self.disabled,
            key=self.key
        )

class NumberInputComponent(FormComponent):
    """Number input component"""
    
    def __init__(self, label: str, key: str, value: float = 0.0,
                 min_value: float = None, max_value: float = None,
                 step: float = 1.0, format: str = None, **kwargs):
        super().__init__(label, key, **kwargs)
        self.value = value
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.format = format
    
    def render(self) -> float:
        """Render number input"""
        return st.number_input(
            self.label,
            value=self.value,
            min_value=self.min_value,
            max_value=self.max_value,
            step=self.step,
            format=self.format,
            help=self.help_text,
            disabled=self.disabled,
            key=self.key
        )

class UserFormComponent:
    """Complete user form component"""
    
    def __init__(self, edit_mode: bool = False, user_data: Dict[str, Any] = None):
        self.edit_mode = edit_mode
        self.user_data = user_data or {}
    
    def render(self) -> Dict[str, Any]:
        """Render complete user form"""
        with st.form("user_form"):
            st.subheader("👤 User Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Username
                username = st.text_input(
                    "Username*",
                    value=self.user_data.get('username', ''),
                    disabled=self.edit_mode,  # Can't change username in edit mode
                    help="3-50 characters, letters, numbers, and underscores only"
                )
                
                # Full name
                full_name = st.text_input(
                    "Full Name*",
                    value=self.user_data.get('full_name', ''),
                    placeholder="Dr. John Smith"
                )
                
                # User type
                user_type_index = 0
                if self.user_data.get('user_type'):
                    try:
                        user_type_index = USER_TYPES.index(self.user_data['user_type'])
                    except ValueError:
                        user_type_index = 0
                
                user_type = st.selectbox(
                    "User Type*",
                    options=USER_TYPES,
                    index=user_type_index
                )
            
            with col2:
                # Email
                email = st.text_input(
                    "Email",
                    value=self.user_data.get('email', ''),
                    placeholder="user@example.com"
                )
                
                # Phone
                phone = st.text_input(
                    "Phone",
                    value=self.user_data.get('phone', ''),
                    placeholder="+1234567890"
                )
                
                # Password (only in create mode)
                password = ""
                if not self.edit_mode:
                    password = st.text_input(
                        "Password*",
                        type="password",
                        help="Minimum 6 characters"
                    )
            
            # Doctor-specific fields
            medical_license = ""
            specialization = ""
            
            if user_type == 'doctor':
                st.subheader("🩺 Medical Information")
                
                col3, col4 = st.columns(2)
                
                with col3:
                    medical_license = st.text_input(
                        "Medical License",
                        value=self.user_data.get('medical_license', ''),
                        placeholder="MD-2023-001",
                        help="Format: XX-YYYY-XXX"
                    )
                
                with col4:
                    specialization = st.text_input(
                        "Specialization",
                        value=self.user_data.get('specialization', ''),
                        placeholder="Internal Medicine"
                    )
            
            # Form submission
            col_submit, col_cancel = st.columns([1, 1])
            
            with col_submit:
                submitted = st.form_submit_button(
                    "Update User" if self.edit_mode else "Create User",
                    type="primary",
                    use_container_width=True
                )
            
            with col_cancel:
                cancelled = st.form_submit_button(
                    "Cancel",
                    use_container_width=True
                )
            
            if submitted:
                # Validate and return form data
                form_data = {
                    'username': username,
                    'full_name': full_name,
                    'user_type': user_type,
                    'email': email,
                    'phone': phone,
                    'medical_license': medical_license,
                    'specialization': specialization
                }
                
                if not self.edit_mode:
                    form_data['password'] = password
                
                # Validate form
                validation_errors = self._validate_user_form(form_data)
                
                if validation_errors:
                    for error in validation_errors:
                        st.error(error)
                    return None
                
                return form_data
            
            if cancelled:
                return {"cancelled": True}
        
        return None
    
    def _validate_user_form(self, form_data: Dict[str, Any]) -> List[str]:
        """Validate user form data"""
        errors = []
        
        # Required fields
        if not form_data.get('username'):
            errors.append("Username is required")
        elif not validate_username(form_data['username']).is_valid:
            errors.append("Invalid username format")
        
        if not form_data.get('full_name'):
            errors.append("Full name is required")
        
        if not self.edit_mode and not form_data.get('password'):
            errors.append("Password is required")
        elif not self.edit_mode and not validate_password(form_data['password']).is_valid:
            errors.append("Password must be at least 6 characters")
        
        # Optional field validation
        if form_data.get('email') and not validate_email(form_data['email']).is_valid:
            errors.append("Invalid email format")
        
        if form_data.get('phone') and not validate_phone(form_data['phone']).is_valid:
            errors.append("Invalid phone format")
        
        if (form_data.get('user_type') == 'doctor' and 
            form_data.get('medical_license') and 
            not validate_medical_license(form_data['medical_license']).is_valid):
            errors.append("Invalid medical license format")
        
        return errors

class PatientFormComponent:
    """Complete patient form component"""
    
    def __init__(self, edit_mode: bool = False, patient_data: Dict[str, Any] = None):
        self.edit_mode = edit_mode
        self.patient_data = patient_data or {}
    
    def render(self) -> Dict[str, Any]:
        """Render complete patient form"""
        with st.form("patient_form"):
            st.subheader("🏥 Patient Information")
            
            # Basic Information
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input(
                    "First Name*",
                    value=self.patient_data.get('first_name', ''),
                    placeholder="John"
                )
                
                # Birth date with age calculation
                birth_date = None
                if self.patient_data.get('date_of_birth'):
                    try:
                        if isinstance(self.patient_data['date_of_birth'], str):
                            birth_date = datetime.strptime(
                                self.patient_data['date_of_birth'], '%Y-%m-%d'
                            ).date()
                        else:
                            birth_date = self.patient_data['date_of_birth']
                    except ValueError:
                        birth_date = None
                
                date_of_birth = st.date_input(
                    "Date of Birth*",
                    value=birth_date,
                    min_value=date(1900, 1, 1),
                    max_value=date.today()
                )
                
                if date_of_birth:
                    age = calculate_age(date_of_birth)
                    st.caption(f"Age: {age} years old")
                
                phone = st.text_input(
                    "Phone",
                    value=self.patient_data.get('phone', ''),
                    placeholder="+1234567890"
                )
            
            with col2:
                last_name = st.text_input(
                    "Last Name*",
                    value=self.patient_data.get('last_name', ''),
                    placeholder="Smith"
                )
                
                gender_index = 0
                if self.patient_data.get('gender'):
                    try:
                        gender_index = GENDER_OPTIONS.index(self.patient_data['gender'])
                    except ValueError:
                        gender_index = 0
                
                gender = st.selectbox(
                    "Gender*",
                    options=GENDER_OPTIONS,
                    index=gender_index
                )
                
                email = st.text_input(
                    "Email",
                    value=self.patient_data.get('email', ''),
                    placeholder="patient@example.com"
                )
            
            # Address
            address = st.text_area(
                "Address",
                value=self.patient_data.get('address', ''),
                height=80,
                placeholder="123 Main Street, City, State, ZIP"
            )
            
            # Medical Information
            st.subheader("🩺 Medical Information")
            
            col3, col4 = st.columns(2)
            
            with col3:
                allergies = st.text_area(
                    "Allergies",
                    value=self.patient_data.get('allergies', ''),
                    height=80,
                    placeholder="Penicillin, Shellfish, etc. (or 'None known')",
                    help="List known allergies separated by commas"
                )
                
                blood_group = st.text_input(
                    "Blood Group",
                    value=self.patient_data.get('blood_group', ''),
                    placeholder="O+, A-, etc."
                )
            
            with col4:
                medical_conditions = st.text_area(
                    "Medical Conditions",
                    value=self.patient_data.get('medical_conditions', ''),
                    height=80,
                    placeholder="Hypertension, Diabetes, etc. (or 'None')",
                    help="List chronic conditions separated by commas"
                )
                
                weight = st.number_input(
                    "Weight (kg)",
                    value=float(self.patient_data.get('weight', 0)) if self.patient_data.get('weight') else 0.0,
                    min_value=0.0,
                    max_value=500.0,
                    step=0.1,
                    format="%.1f"
                )
                
                height = st.number_input(
                    "Height (cm)",
                    value=float(self.patient_data.get('height', 0)) if self.patient_data.get('height') else 0.0,
                    min_value=0.0,
                    max_value=300.0,
                    step=0.1,
                    format="%.1f"
                )
            
            # Emergency Contact
            st.subheader("🚨 Emergency Contact")
            
            col5, col6 = st.columns(2)
            
            with col5:
                emergency_contact = st.text_input(
                    "Emergency Contact Name",
                    value=self.patient_data.get('emergency_contact', ''),
                    placeholder="Jane Smith (Spouse)"
                )
            
            with col6:
                emergency_phone = st.text_input(
                    "Emergency Contact Phone",
                    value=self.patient_data.get('emergency_phone', ''),
                    placeholder="+1234567890"
                )
            
            # Insurance
            insurance_info = st.text_area(
                "Insurance Information",
                value=self.patient_data.get('insurance_info', ''),
                height=60,
                placeholder="Insurance Company - Policy Number"
            )
            
            # Notes
            notes = st.text_area(
                "Additional Notes",
                value=self.patient_data.get('notes', ''),
                height=80,
                placeholder="Any additional information about the patient"
            )
            
            # Form submission
            col_submit, col_cancel = st.columns([1, 1])
            
            with col_submit:
                submitted = st.form_submit_button(
                    "Update Patient" if self.edit_mode else "Register Patient",
                    type="primary",
                    use_container_width=True
                )
            
            with col_cancel:
                cancelled = st.form_submit_button(
                    "Cancel",
                    use_container_width=True
                )
            
            if submitted:
                # Validate and return form data
                form_data = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'date_of_birth': date_of_birth,
                    'gender': gender,
                    'phone': phone,
                    'email': email,
                    'address': address,
                    'allergies': allergies,
                    'medical_conditions': medical_conditions,
                    'emergency_contact': emergency_contact,
                    'emergency_phone': emergency_phone,
                    'insurance_info': insurance_info,
                    'blood_group': blood_group,
                    'weight': weight if weight > 0 else None,
                    'height': height if height > 0 else None,
                    'notes': notes
                }
                
                # Validate form
                validation_errors = self._validate_patient_form(form_data)
                
                if validation_errors:
                    for error in validation_errors:
                        st.error(error)
                    return None
                
                return form_data
            
            if cancelled:
                return {"cancelled": True}
        
        return None
    
    def _validate_patient_form(self, form_data: Dict[str, Any]) -> List[str]:
        """Validate patient form data"""
        errors = []
        
        # Required fields
        if not form_data.get('first_name'):
            errors.append("First name is required")
        
        if not form_data.get('last_name'):
            errors.append("Last name is required")
        
        if not form_data.get('date_of_birth'):
            errors.append("Date of birth is required")
        elif form_data['date_of_birth'] > date.today():
            errors.append("Date of birth cannot be in the future")
        
        if not form_data.get('gender'):
            errors.append("Gender is required")
        
        # Optional field validation
        if form_data.get('email') and not validate_email(form_data['email']).is_valid:
            errors.append("Invalid email format")
        
        if form_data.get('phone') and not validate_phone(form_data['phone']).is_valid:
            errors.append("Invalid phone format")
        
        if form_data.get('emergency_phone') and not validate_phone(form_data['emergency_phone']).is_valid:
            errors.append("Invalid emergency contact phone format")
        
        return errors

class VisitFormComponent:
    """Patient visit form component"""
    
    def __init__(self, patient_data: Dict[str, Any], edit_mode: bool = False, 
                 visit_data: Dict[str, Any] = None):
        self.patient_data = patient_data
        self.edit_mode = edit_mode
        self.visit_data = visit_data or {}
    
    def render(self) -> Dict[str, Any]:
        """Render visit form"""
        with st.form("visit_form"):
            st.subheader(f"📅 Visit for {self.patient_data['first_name']} {self.patient_data['last_name']}")
            
            # Visit Information
            col1, col2 = st.columns(2)
            
            with col1:
                visit_date = st.date_input(
                    "Visit Date*",
                    value=datetime.strptime(self.visit_data.get('visit_date', str(date.today())), '%Y-%m-%d').date() if isinstance(self.visit_data.get('visit_date'), str) else self.visit_data.get('visit_date', date.today()),
                    min_value=date.today() - timedelta(days=30),
                    max_value=date.today() + timedelta(days=90)
                )
                
                visit_type_index = 0
                if self.visit_data.get('visit_type'):
                    try:
                        visit_type_index = VISIT_TYPES.index(self.visit_data['visit_type'])
                    except ValueError:
                        visit_type_index = 0
                
                visit_type = st.selectbox(
                    "Visit Type*",
                    options=VISIT_TYPES,
                    index=visit_type_index
                )
            
            with col2:
                visit_time = st.time_input(
                    "Visit Time",
                    value=datetime.strptime(self.visit_data.get('visit_time', '09:00'), '%H:%M').time() if isinstance(self.visit_data.get('visit_time'), str) else self.visit_data.get('visit_time', datetime.now().time())
                )
                
                is_followup = st.checkbox(
                    "Follow-up Visit",
                    value=self.visit_data.get('is_followup', False)
                )
            
            # Current Problems
            current_problems = st.text_area(
                "Current Problems/Chief Complaint*",
                value=self.visit_data.get('current_problems', ''),
                height=80,
                placeholder="Describe the patient's current symptoms or reason for visit"
            )
            
            # Vital Signs
            st.subheader("🩺 Vital Signs")
            
            col3, col4, col5 = st.columns(3)
            
            with col3:
                blood_pressure = st.text_input(
                    "Blood Pressure",
                    value=self.visit_data.get('blood_pressure', ''),
                    placeholder="120/80",
                    help="Format: systolic/diastolic"
                )
                
                temperature = st.number_input(
                    "Temperature (°F)",
                    value=float(self.visit_data.get('temperature', 0)) if self.visit_data.get('temperature') else 0.0,
                    min_value=90.0,
                    max_value=110.0,
                    step=0.1,
                    format="%.1f"
                )
            
            with col4:
                pulse_rate = st.number_input(
                    "Pulse Rate (bpm)",
                    value=int(self.visit_data.get('pulse_rate', 0)) if self.visit_data.get('pulse_rate') else 0,
                    min_value=30,
                    max_value=200,
                    step=1
                )
                
                respiratory_rate = st.number_input(
                    "Respiratory Rate (/min)",
                    value=int(self.visit_data.get('respiratory_rate', 0)) if self.visit_data.get('respiratory_rate') else 0,
                    min_value=8,
                    max_value=40,
                    step=1
                )
            
            with col5:
                oxygen_saturation = st.number_input(
                    "Oxygen Saturation (%)",
                    value=float(self.visit_data.get('oxygen_saturation', 0)) if self.visit_data.get('oxygen_saturation') else 0.0,
                    min_value=70.0,
                    max_value=100.0,
                    step=0.1,
                    format="%.1f"
                )
            
            # Notes
            notes = st.text_area(
                "Visit Notes",
                value=self.visit_data.get('notes', ''),
                height=100,
                placeholder="Additional observations, examination findings, etc."
            )
            
            # Form submission
            col_submit, col_cancel = st.columns([1, 1])
            
            with col_submit:
                submitted = st.form_submit_button(
                    "Update Visit" if self.edit_mode else "Record Visit",
                    type="primary",
                    use_container_width=True
                )
            
            with col_cancel:
                cancelled = st.form_submit_button(
                    "Cancel",
                    use_container_width=True
                )
            
            if submitted:
                form_data = {
                    'patient_id': self.patient_data['id'],
                    'visit_date': visit_date,
                    'visit_time': visit_time,
                    'visit_type': visit_type,
                    'current_problems': current_problems,
                    'is_followup': is_followup,
                    'blood_pressure': blood_pressure,
                    'temperature': temperature if temperature > 0 else None,
                    'pulse_rate': pulse_rate if pulse_rate > 0 else None,
                    'respiratory_rate': respiratory_rate if respiratory_rate > 0 else None,
                    'oxygen_saturation': oxygen_saturation if oxygen_saturation > 0 else None,
                    'notes': notes
                }
                
                # Validate form
                validation_errors = self._validate_visit_form(form_data)
                
                if validation_errors:
                    for error in validation_errors:
                        st.error(error)
                    return None
                
                return form_data
            
            if cancelled:
                return {"cancelled": True}
        
        return None
    
    def _validate_visit_form(self, form_data: Dict[str, Any]) -> List[str]:
        """Validate visit form data"""
        errors = []
        
        # Required fields
        if not form_data.get('visit_date'):
            errors.append("Visit date is required")
        
        if not form_data.get('visit_type'):
            errors.append("Visit type is required")
        
        if not form_data.get('current_problems'):
            errors.append("Current problems/chief complaint is required")
        
        # Validate vital signs ranges
        if form_data.get('blood_pressure'):
            import re
            bp = form_data['blood_pressure']
            if not re.match(r'^\d{2,3}/\d{2,3}, bp):
                errors.append("Blood pressure must be in format XXX/XX")
            else:
                try:
                    systolic, diastolic = map(int, bp.split('/'))
                    if systolic < 70 or systolic > 250:
                        errors.append("Systolic pressure must be between 70-250 mmHg")
                    if diastolic < 40 or diastolic > 150:
                        errors.append("Diastolic pressure must be between 40-150 mmHg")
                    if systolic <= diastolic:
                        errors.append("Systolic pressure must be higher than diastolic")
                except ValueError:
                    errors.append("Invalid blood pressure format")
        
        return errors

class MedicationFormComponent:
    """Medication form component"""
    
    def __init__(self, edit_mode: bool = False, medication_data: Dict[str, Any] = None):
        self.edit_mode = edit_mode
        self.medication_data = medication_data or {}
    
    def render(self) -> Dict[str, Any]:
        """Render medication form"""
        with st.form("medication_form"):
            st.subheader("💊 Medication Information")
            
            # Basic Information
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input(
                    "Medication Name*",
                    value=self.medication_data.get('name', ''),
                    placeholder="Lisinopril"
                )
                
                generic_name = st.text_input(
                    "Generic Name",
                    value=self.medication_data.get('generic_name', ''),
                    placeholder="Lisinopril"
                )
                
                drug_class_index = 0
                if self.medication_data.get('drug_class'):
                    try:
                        drug_class_index = DRUG_CLASSES.index(self.medication_data['drug_class'])
                    except ValueError:
                        drug_class_index = 0
                
                drug_class = st.selectbox(
                    "Drug Class*",
                    options=DRUG_CLASSES,
                    index=drug_class_index
                )
            
            with col2:
                brand_names = st.text_input(
                    "Brand Names",
                    value=self.medication_data.get('brand_names', ''),
                    placeholder="Prinivil, Zestril",
                    help="Separate multiple brands with commas"
                )
                
                dosage_forms = st.text_input(
                    "Dosage Forms",
                    value=self.medication_data.get('dosage_forms', ''),
                    placeholder="Tablet, Capsule",
                    help="Separate multiple forms with commas"
                )
                
                strengths = st.text_input(
                    "Strengths",
                    value=self.medication_data.get('strengths', ''),
                    placeholder="2.5mg, 5mg, 10mg, 20mg",
                    help="Separate multiple strengths with commas"
                )
            
            # Clinical Information
            st.subheader("🩺 Clinical Information")
            
            indications = st.text_area(
                "Indications",
                value=self.medication_data.get('indications', ''),
                height=80,
                placeholder="Hypertension, heart failure, post-MI"
            )
            
            contraindications = st.text_area(
                "Contraindications",
                value=self.medication_data.get('contraindications', ''),
                height=80,
                placeholder="Pregnancy, angioedema history, bilateral renal artery stenosis"
            )
            
            side_effects = st.text_area(
                "Side Effects",
                value=self.medication_data.get('side_effects', ''),
                height=80,
                placeholder="Dry cough, dizziness, hyperkalemia"
            )
            
            interactions = st.text_area(
                "Drug Interactions",
                value=self.medication_data.get('interactions', ''),
                height=80,
                placeholder="NSAIDs, potassium supplements, lithium"
            )
            
            # Additional Information
            col3, col4 = st.columns(2)
            
            with col3:
                precautions = st.text_area(
                    "Precautions",
                    value=self.medication_data.get('precautions', ''),
                    height=60,
                    placeholder="Monitor blood pressure and kidney function"
                )
                
                manufacturer = st.text_input(
                    "Manufacturer",
                    value=self.medication_data.get('manufacturer', ''),
                    placeholder="Pharmaceutical Company"
                )
            
            with col4:
                dosage_guidelines = st.text_area(
                    "Dosage Guidelines",
                    value=self.medication_data.get('dosage_guidelines', ''),
                    height=60,
                    placeholder="Start 10mg daily, adjust based on response"
                )
                
                storage_conditions = st.text_input(
                    "Storage Conditions",
                    value=self.medication_data.get('storage_conditions', ''),
                    placeholder="Store at room temperature"
                )
            
            is_controlled = st.checkbox(
                "Controlled Substance",
                value=self.medication_data.get('is_controlled', False),
                help="Check if this is a controlled/scheduled medication"
            )
            
            # Form submission
            col_submit, col_cancel = st.columns([1, 1])
            
            with col_submit:
                submitted = st.form_submit_button(
                    "Update Medication" if self.edit_mode else "Add Medication",
                    type="primary",
                    use_container_width=True
                )
            
            with col_cancel:
                cancelled = st.form_submit_button(
                    "Cancel",
                    use_container_width=True
                )
            
            if submitted:
                form_data = {
                    'name': name,
                    'generic_name': generic_name,
                    'brand_names': brand_names,
                    'drug_class': drug_class,
                    'dosage_forms': dosage_forms,
                    'strengths': strengths,
                    'indications': indications,
                    'contraindications': contraindications,
                    'side_effects': side_effects,
                    'interactions': interactions,
                    'precautions': precautions,
                    'dosage_guidelines': dosage_guidelines,
                    'manufacturer': manufacturer,
                    'storage_conditions': storage_conditions,
                    'is_controlled': is_controlled
                }
                
                # Validate form
                validation_errors = self._validate_medication_form(form_data)
                
                if validation_errors:
                    for error in validation_errors:
                        st.error(error)
                    return None
                
                return form_data
            
            if cancelled:
                return {"cancelled": True}
        
        return None
    
    def _validate_medication_form(self, form_data: Dict[str, Any]) -> List[str]:
        """Validate medication form data"""
        errors = []
        
        # Required fields
        if not form_data.get('name'):
            errors.append("Medication name is required")
        
        if not form_data.get('drug_class'):
            errors.append("Drug class is required")
        
        return errors

class SearchFormComponent:
    """Reusable search form component"""
    
    def __init__(self, placeholder: str = "Search...", 
                 filters: List[Dict[str, Any]] = None,
                 show_filters: bool = True):
        self.placeholder = placeholder
        self.filters = filters or []
        self.show_filters = show_filters
    
    def render(self) -> Dict[str, Any]:
        """Render search form"""
        # Search input
        search_term = st.text_input(
            "Search",
            placeholder=self.placeholder,
            label_visibility="collapsed"
        )
        
        search_params = {'search_term': search_term}
        
        # Filters
        if self.show_filters and self.filters:
            with st.expander("🔍 Advanced Filters", expanded=False):
                filter_cols = st.columns(len(self.filters))
                
                for i, filter_config in enumerate(self.filters):
                    with filter_cols[i]:
                        filter_type = filter_config.get('type', 'selectbox')
                        filter_key = filter_config['key']
                        filter_label = filter_config['label']
                        filter_options = filter_config.get('options', [])
                        
                        if filter_type == 'selectbox':
                            search_params[filter_key] = st.selectbox(
                                filter_label,
                                options=['All'] + filter_options,
                                key=f"filter_{filter_key}"
                            )
                        elif filter_type == 'multiselect':
                            search_params[filter_key] = st.multiselect(
                                filter_label,
                                options=filter_options,
                                key=f"filter_{filter_key}"
                            )
                        elif filter_type == 'date_range':
                            col_start, col_end = st.columns(2)
                            with col_start:
                                search_params[f"{filter_key}_start"] = st.date_input(
                                    "Start Date",
                                    key=f"filter_{filter_key}_start"
                                )
                            with col_end:
                                search_params[f"{filter_key}_end"] = st.date_input(
                                    "End Date",
                                    key=f"filter_{filter_key}_end"
                                )
        
        return search_params

class PrescriptionMedicationComponent:
    """Component for adding medications to prescription"""
    
    def __init__(self, medications_list: List[Dict[str, Any]], 
                 available_medications: List[Dict[str, Any]]):
        self.medications_list = medications_list
        self.available_medications = available_medications
    
    def render(self) -> List[Dict[str, Any]]:
        """Render medication selection component"""
        st.subheader("💊 Medications")
        
        # Add new medication
        with st.expander("➕ Add Medication", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Medication search/select
                medication_options = [f"{med['name']} ({med.get('generic_name', 'N/A')})" 
                                    for med in self.available_medications]
                
                selected_medication = st.selectbox(
                    "Select Medication",
                    options=medication_options,
                    key="prescription_medication_select"
                )
                
                if selected_medication:
                    # Get selected medication data
                    med_index = medication_options.index(selected_medication)
                    medication_data = self.available_medications[med_index]
                    
                    # Dosage information
                    col_dose, col_freq, col_dur = st.columns(3)
                    
                    with col_dose:
                        dosage = st.text_input(
                            "Dosage",
                            placeholder="10mg",
                            key="prescription_dosage"
                        )
                    
                    with col_freq:
                        frequency = st.selectbox(
                            "Frequency",
                            options=[
                                "Once daily", "Twice daily", "Three times daily",
                                "Four times daily", "Every 4 hours", "Every 6 hours",
                                "Every 8 hours", "Every 12 hours", "As needed",
                                "Before meals", "After meals", "At bedtime"
                            ],
                            key="prescription_frequency"
                        )
                    
                    with col_dur:
                        duration = st.selectbox(
                            "Duration",
                            options=[
                                "3 days", "5 days", "7 days", "10 days", "14 days",
                                "21 days", "1 month", "2 months", "3 months",
                                "6 months", "Ongoing", "As directed"
                            ],
                            key="prescription_duration"
                        )
                    
                    # Additional fields
                    col_qty, col_refills = st.columns(2)
                    
                    with col_qty:
                        quantity = st.text_input(
                            "Quantity",
                            placeholder="30 tablets",
                            key="prescription_quantity"
                        )
                    
                    with col_refills:
                        refills = st.number_input(
                            "Refills",
                            min_value=0,
                            max_value=12,
                            value=0,
                            key="prescription_refills"
                        )
                    
                    instructions = st.text_area(
                        "Special Instructions",
                        placeholder="Take with food, avoid alcohol, etc.",
                        key="prescription_instructions"
                    )
            
            with col2:
                if st.button("➕ Add to Prescription", type="primary", use_container_width=True):
                    if selected_medication and dosage and frequency and duration:
                        new_medication = {
                            'medication_id': medication_data['id'],
                            'medication_name': medication_data['name'],
                            'generic_name': medication_data.get('generic_name'),
                            'dosage': dosage,
                            'frequency': frequency,
                            'duration': duration,
                            'quantity': quantity,
                            'refills': refills,
                            'instructions': instructions
                        }
                        
                        self.medications_list.append(new_medication)
                        st.success(f"Added {medication_data['name']} to prescription")
                        st.rerun()
                    else:
                        st.error("Please fill in medication, dosage, frequency, and duration")
        
        # Display added medications
        if self.medications_list:
            st.subheader("Added Medications")
            
            for i, med in enumerate(self.medications_list):
                with st.container():
                    col_info, col_remove = st.columns([4, 1])
                    
                    with col_info:
                        st.markdown(f"""
                        **{med['medication_name']}** ({med.get('generic_name', 'N/A')})
                        - Dosage: {med['dosage']} {med['frequency']} for {med['duration']}
                        - Quantity: {med.get('quantity', 'N/A')} | Refills: {med.get('refills', 0)}
                        {f"- Instructions: {med['instructions']}" if med.get('instructions') else ""}
                        """)
                    
                    with col_remove:
                        if st.button("🗑️", key=f"remove_med_{i}", help="Remove medication"):
                            self.medications_list.pop(i)
                            st.rerun()
                    
                    st.divider()
        else:
            st.info("No medications added to prescription yet.")
        
        return self.medications_list

class PrescriptionLabTestComponent:
    """Component for adding lab tests to prescription"""
    
    def __init__(self, lab_tests_list: List[Dict[str, Any]], 
                 available_lab_tests: List[Dict[str, Any]]):
        self.lab_tests_list = lab_tests_list
        self.available_lab_tests = available_lab_tests
    
    def render(self) -> List[Dict[str, Any]]:
        """Render lab test selection component"""
        st.subheader("🧪 Laboratory Tests")
        
        # Add new lab test
        with st.expander("➕ Add Lab Test", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Lab test search/select
                test_options = [f"{test['test_name']} ({test.get('test_category', 'N/A')})" 
                              for test in self.available_lab_tests]
                
                selected_test = st.selectbox(
                    "Select Lab Test",
                    options=test_options,
                    key="prescription_lab_test_select"
                )
                
                if selected_test:
                    # Get selected test data
                    test_index = test_options.index(selected_test)
                    test_data = self.available_lab_tests[test_index]
                    
                    col_urgency, col_fasting = st.columns(2)
                    
                    with col_urgency:
                        urgency = st.selectbox(
                            "Urgency",
                            options=["Routine", "Urgent", "STAT"],
                            key="prescription_lab_urgency"
                        )
                    
                    with col_fasting:
                        fasting_required = st.checkbox(
                            "Fasting Required",
                            key="prescription_lab_fasting"
                        )
                    
                    special_instructions = st.text_area(
                        "Special Instructions",
                        placeholder="Collection time, preparation requirements, etc.",
                        key="prescription_lab_instructions"
                    )
            
            with col2:
                if st.button("➕ Add to Prescription", type="primary", use_container_width=True, key="add_lab_test"):
                    if selected_test:
                        new_lab_test = {
                            'lab_test_id': test_data['id'],
                            'test_name': test_data['test_name'],
                            'test_category': test_data.get('test_category'),
                            'urgency': urgency,
                            'fasting_required': fasting_required,
                            'special_instructions': special_instructions,
                            'normal_range': test_data.get('normal_range'),
                            'preparation_required': test_data.get('preparation_required')
                        }
                        
                        self.lab_tests_list.append(new_lab_test)
                        st.success(f"Added {test_data['test_name']} to prescription")
                        st.rerun()
                    else:
                        st.error("Please select a lab test")
        
        # Display added lab tests
        if self.lab_tests_list:
            st.subheader("Added Lab Tests")
            
            for i, test in enumerate(self.lab_tests_list):
                with st.container():
                    col_info, col_remove = st.columns([4, 1])
                    
                    with col_info:
                        urgency_color = "🔴" if test['urgency'] == "STAT" else "🟡" if test['urgency'] == "Urgent" else "🟢"
                        fasting_text = " (Fasting required)" if test.get('fasting_required') else ""
                        
                        st.markdown(f"""
                        **{test['test_name']}** ({test.get('test_category', 'N/A')})
                        - Urgency: {urgency_color} {test['urgency']}{fasting_text}
                        {f"- Instructions: {test['special_instructions']}" if test.get('special_instructions') else ""}
                        {f"- Normal Range: {test['normal_range']}" if test.get('normal_range') else ""}
                        """)
                    
                    with col_remove:
                        if st.button("🗑️", key=f"remove_test_{i}", help="Remove lab test"):
                            self.lab_tests_list.pop(i)
                            st.rerun()
                    
                    st.divider()
        else:
            st.info("No lab tests added to prescription yet.")
        
        return self.lab_tests_list

# Utility functions for form components
def render_validation_errors(errors: List[str]):
    """Render validation errors in a consistent format"""
    if errors:
        for error in errors:
            st.error(f"❌ {error}")

def create_form_columns(num_columns: int, column_configs: List[Dict[str, Any]] = None):
    """Create form columns with optional configuration"""
    if column_configs and len(column_configs) == num_columns:
        ratios = [config.get('ratio', 1) for config in column_configs]
        return st.columns(ratios)
    else:
        return st.columns(num_columns)

def render_required_field_indicator():
    """Render indicator for required fields"""
    st.caption("* Required fields")

def validate_form_data(form_data: Dict[str, Any], 
                      validation_rules: Dict[str, Callable]) -> List[str]:
    """Generic form validation function"""
    errors = []
    
    for field_name, validator in validation_rules.items():
        if field_name in form_data:
            try:
                result = validator(form_data[field_name])
                if hasattr(result, 'has_errors') and result.has_errors():
                    errors.extend(result.errors)
                elif not result:
                    errors.append(f"Invalid {field_name}")
            except Exception as e:
                errors.append(f"Validation error for {field_name}: {str(e)}")
    
    return errors
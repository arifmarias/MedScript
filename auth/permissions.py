"""
MedScript Pro - Role-Based Access Control System
This file handles permissions and access control for different user roles.
"""

from typing import List, Dict, Any, Optional, Set
from enum import Enum
import streamlit as st
from config.settings import USER_ROLES, ERROR_MESSAGES

class Permission(Enum):
    """Enumeration of all system permissions"""
    
    # User Management
    CREATE_USERS = "create_users"
    READ_USERS = "read_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"
    
    # Patient Management
    CREATE_PATIENTS = "create_patients"
    READ_PATIENTS = "read_patients"
    UPDATE_PATIENTS = "update_patients"
    DELETE_PATIENTS = "delete_patients"
    
    # Patient Visits
    CREATE_VISITS = "create_visits"
    READ_VISITS = "read_visits"
    UPDATE_VISITS = "update_visits"
    DELETE_VISITS = "delete_visits"
    
    # Prescriptions
    CREATE_PRESCRIPTIONS = "create_prescriptions"
    READ_PRESCRIPTIONS = "read_prescriptions"
    UPDATE_PRESCRIPTIONS = "update_prescriptions"
    DELETE_PRESCRIPTIONS = "delete_prescriptions"
    GENERATE_PRESCRIPTION_PDF = "generate_prescription_pdf"
    
    # Medications
    CREATE_MEDICATIONS = "create_medications"
    READ_MEDICATIONS = "read_medications"
    UPDATE_MEDICATIONS = "update_medications"
    DELETE_MEDICATIONS = "delete_medications"
    MARK_FAVORITE_MEDICATIONS = "mark_favorite_medications"
    
    # Lab Tests
    CREATE_LAB_TESTS = "create_lab_tests"
    READ_LAB_TESTS = "read_lab_tests"
    UPDATE_LAB_TESTS = "update_lab_tests"
    DELETE_LAB_TESTS = "delete_lab_tests"
    
    # Templates
    CREATE_TEMPLATES = "create_templates"
    READ_TEMPLATES = "read_templates"
    UPDATE_TEMPLATES = "update_templates"
    DELETE_TEMPLATES = "delete_templates"
    
    # Analytics
    READ_SYSTEM_ANALYTICS = "read_system_analytics"
    READ_USER_ANALYTICS = "read_user_analytics"
    READ_PATIENT_ANALYTICS = "read_patient_analytics"
    
    # System Administration
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"
    VIEW_SYSTEM_LOGS = "view_system_logs"
    MANAGE_SYSTEM_SETTINGS = "manage_system_settings"
    
    # AI Features
    USE_AI_ANALYSIS = "use_ai_analysis"
    
    # Special Access
    TODAY_PATIENTS_DASHBOARD = "today_patients_dashboard"
    COMPLETE_CONSULTATIONS = "complete_consultations"

class RolePermissions:
    """Defines permissions for each user role"""
    
    # Super Admin - Full system access (except prescriptions)
    SUPER_ADMIN_PERMISSIONS = {
        # User Management - Full CRUD
        Permission.CREATE_USERS,
        Permission.READ_USERS,
        Permission.UPDATE_USERS,
        Permission.DELETE_USERS,
        
        # Patient Management - Full CRUD
        Permission.CREATE_PATIENTS,
        Permission.READ_PATIENTS,
        Permission.UPDATE_PATIENTS,
        Permission.DELETE_PATIENTS,
        
        # Patient Visits - Full CRUD
        Permission.CREATE_VISITS,
        Permission.READ_VISITS,
        Permission.UPDATE_VISITS,
        Permission.DELETE_VISITS,
        
        # Medications - Full CRUD
        Permission.CREATE_MEDICATIONS,
        Permission.READ_MEDICATIONS,
        Permission.UPDATE_MEDICATIONS,
        Permission.DELETE_MEDICATIONS,
        
        # Lab Tests - Full CRUD
        Permission.CREATE_LAB_TESTS,
        Permission.READ_LAB_TESTS,
        Permission.UPDATE_LAB_TESTS,
        Permission.DELETE_LAB_TESTS,
        
        # Analytics - System wide
        Permission.READ_SYSTEM_ANALYTICS,
        Permission.READ_USER_ANALYTICS,
        Permission.READ_PATIENT_ANALYTICS,
        
        # System Administration
        Permission.SYSTEM_BACKUP,
        Permission.SYSTEM_RESTORE,
        Permission.VIEW_SYSTEM_LOGS,
        Permission.MANAGE_SYSTEM_SETTINGS,
        
        # NOTE: Super Admin CANNOT create prescriptions (medical safety)
    }
    
    # Doctor - Clinical workflow access
    DOCTOR_PERMISSIONS = {
        # Patient Management - Read only (created by assistants)
        Permission.READ_PATIENTS,
        
        # Patient Visits - Read only (for context)
        Permission.READ_VISITS,
        
        # Prescriptions - Full access
        Permission.CREATE_PRESCRIPTIONS,
        Permission.READ_PRESCRIPTIONS,
        Permission.UPDATE_PRESCRIPTIONS,
        Permission.DELETE_PRESCRIPTIONS,
        Permission.GENERATE_PRESCRIPTION_PDF,
        
        # Medications - Read, Create, Update (no delete)
        Permission.READ_MEDICATIONS,
        Permission.CREATE_MEDICATIONS,
        Permission.UPDATE_MEDICATIONS,
        Permission.MARK_FAVORITE_MEDICATIONS,
        
        # Lab Tests - Read, Create (no edit/delete)
        Permission.READ_LAB_TESTS,
        Permission.CREATE_LAB_TESTS,
        
        # Templates - Full access for own templates
        Permission.CREATE_TEMPLATES,
        Permission.READ_TEMPLATES,
        Permission.UPDATE_TEMPLATES,
        Permission.DELETE_TEMPLATES,
        
        # Analytics - Own data only
        Permission.READ_USER_ANALYTICS,
        Permission.READ_PATIENT_ANALYTICS,
        
        # AI Features
        Permission.USE_AI_ANALYSIS,
        
        # Special Doctor Features
        Permission.TODAY_PATIENTS_DASHBOARD,
        Permission.COMPLETE_CONSULTATIONS,
    }
    
    # Assistant - Patient support functions
    ASSISTANT_PERMISSIONS = {
        # Patient Management - Full CRUD
        Permission.CREATE_PATIENTS,
        Permission.READ_PATIENTS,
        Permission.UPDATE_PATIENTS,
        
        # Patient Visits - Full CRUD
        Permission.CREATE_VISITS,
        Permission.READ_VISITS,
        Permission.UPDATE_VISITS,
        
        # Medications - Read, Create (no edit/delete)
        Permission.READ_MEDICATIONS,
        Permission.CREATE_MEDICATIONS,
        
        # Lab Tests - Read, Create (no edit/delete)
        Permission.READ_LAB_TESTS,
        Permission.CREATE_LAB_TESTS,
        
        # Analytics - Limited to own activities
        Permission.READ_USER_ANALYTICS,
    }
    
    @classmethod
    def get_role_permissions(cls, role: str) -> Set[Permission]:
        """
        Get permissions for a specific role
        
        Args:
            role (str): User role
        
        Returns:
            Set[Permission]: Set of permissions for the role
        """
        role_map = {
            USER_ROLES['SUPER_ADMIN']: cls.SUPER_ADMIN_PERMISSIONS,
            USER_ROLES['DOCTOR']: cls.DOCTOR_PERMISSIONS,
            USER_ROLES['ASSISTANT']: cls.ASSISTANT_PERMISSIONS,
        }
        
        return role_map.get(role, set())

class PermissionChecker:
    """Utility class for checking permissions"""
    
    @staticmethod
    def get_current_user_permissions() -> Set[Permission]:
        """
        Get current user's permissions
        
        Returns:
            Set[Permission]: Current user's permissions
        """
        from auth.authentication import get_current_user_role
        
        user_role = get_current_user_role()
        if not user_role:
            return set()
        
        return RolePermissions.get_role_permissions(user_role)
    
    @staticmethod
    def has_permission(permission: Permission) -> bool:
        """
        Check if current user has a specific permission
        
        Args:
            permission (Permission): Permission to check
        
        Returns:
            bool: True if user has permission
        """
        user_permissions = PermissionChecker.get_current_user_permissions()
        return permission in user_permissions
    
    @staticmethod
    def has_any_permission(permissions: List[Permission]) -> bool:
        """
        Check if current user has any of the specified permissions
        
        Args:
            permissions (List[Permission]): List of permissions to check
        
        Returns:
            bool: True if user has at least one permission
        """
        user_permissions = PermissionChecker.get_current_user_permissions()
        return any(permission in user_permissions for permission in permissions)
    
    @staticmethod
    def has_all_permissions(permissions: List[Permission]) -> bool:
        """
        Check if current user has all specified permissions
        
        Args:
            permissions (List[Permission]): List of permissions to check
        
        Returns:
            bool: True if user has all permissions
        """
        user_permissions = PermissionChecker.get_current_user_permissions()
        return all(permission in user_permissions for permission in permissions)
    
    @staticmethod
    def require_permission(permission: Permission) -> None:
        """
        Require a specific permission (stops execution if not authorized)
        
        Args:
            permission (Permission): Required permission
        """
        if not PermissionChecker.has_permission(permission):
            st.error(ERROR_MESSAGES['ACCESS_DENIED'])
            st.info(f"This action requires the '{permission.value}' permission.")
            st.stop()
    
    @staticmethod
    def require_any_permission(permissions: List[Permission]) -> None:
        """
        Require any of the specified permissions
        
        Args:
            permissions (List[Permission]): List of acceptable permissions
        """
        if not PermissionChecker.has_any_permission(permissions):
            permission_names = [p.value for p in permissions]
            st.error(ERROR_MESSAGES['ACCESS_DENIED'])
            st.info(f"This action requires one of the following permissions: {', '.join(permission_names)}")
            st.stop()
    
    @staticmethod
    def require_role(allowed_roles: List[str]) -> None:
        """
        Require specific user role(s)
        
        Args:
            allowed_roles (List[str]): List of allowed roles
        """
        from auth.authentication import get_current_user_role, require_authentication
        
        require_authentication()
        
        user_role = get_current_user_role()
        if user_role not in allowed_roles:
            st.error(ERROR_MESSAGES['ACCESS_DENIED'])
            st.info(f"This page requires one of the following roles: {', '.join(allowed_roles)}")
            st.stop()

def can_access_user_management() -> bool:
    """Check if current user can access user management"""
    return PermissionChecker.has_any_permission([
        Permission.CREATE_USERS,
        Permission.READ_USERS,
        Permission.UPDATE_USERS,
        Permission.DELETE_USERS
    ])

def can_manage_patients() -> bool:
    """Check if current user can manage patients"""
    return PermissionChecker.has_any_permission([
        Permission.CREATE_PATIENTS,
        Permission.READ_PATIENTS,
        Permission.UPDATE_PATIENTS
    ])

def can_create_prescriptions() -> bool:
    """Check if current user can create prescriptions"""
    return PermissionChecker.has_permission(Permission.CREATE_PRESCRIPTIONS)

def can_view_today_patients() -> bool:
    """Check if current user can view today's patients dashboard"""
    return PermissionChecker.has_permission(Permission.TODAY_PATIENTS_DASHBOARD)

def can_manage_medications() -> bool:
    """Check if current user can manage medications"""
    return PermissionChecker.has_any_permission([
        Permission.CREATE_MEDICATIONS,
        Permission.READ_MEDICATIONS,
        Permission.UPDATE_MEDICATIONS
    ])

def can_manage_lab_tests() -> bool:
    """Check if current user can manage lab tests"""
    return PermissionChecker.has_any_permission([
        Permission.CREATE_LAB_TESTS,
        Permission.READ_LAB_TESTS,
        Permission.UPDATE_LAB_TESTS
    ])

def can_use_templates() -> bool:
    """Check if current user can use templates"""
    return PermissionChecker.has_any_permission([
        Permission.CREATE_TEMPLATES,
        Permission.READ_TEMPLATES,
        Permission.UPDATE_TEMPLATES
    ])

def can_view_analytics() -> bool:
    """Check if current user can view analytics"""
    return PermissionChecker.has_any_permission([
        Permission.READ_SYSTEM_ANALYTICS,
        Permission.READ_USER_ANALYTICS,
        Permission.READ_PATIENT_ANALYTICS
    ])

def can_use_ai_features() -> bool:
    """Check if current user can use AI features"""
    return PermissionChecker.has_permission(Permission.USE_AI_ANALYSIS)

def get_allowed_navigation_items() -> List[Dict[str, Any]]:
    """
    Get navigation items allowed for current user
    
    Returns:
        List[Dict[str, Any]]: List of allowed navigation items
    """
    from auth.authentication import get_current_user_role
    
    user_role = get_current_user_role()
    if not user_role:
        return []
    
    navigation_items = []
    
    # Dashboard is available to all authenticated users
    navigation_items.append({
        'label': '📊 Dashboard',
        'key': 'dashboard',
        'icon': '📊'
    })
    
    # Role-specific navigation
    if user_role == USER_ROLES['SUPER_ADMIN']:
        navigation_items.extend([
            {'label': '👥 User Management', 'key': 'user_management', 'icon': '👥'},
            {'label': '🏥 Patient Management', 'key': 'patient_management', 'icon': '🏥'},
            {'label': '💊 Medication Database', 'key': 'medication_management', 'icon': '💊'},
            {'label': '🧪 Lab Test Database', 'key': 'lab_test_management', 'icon': '🧪'},
            {'label': '📈 System Analytics', 'key': 'system_analytics', 'icon': '📈'}
        ])
    
    elif user_role == USER_ROLES['DOCTOR']:
        navigation_items.extend([
            {'label': '👥 Today\'s Patients', 'key': 'todays_patients', 'icon': '👥'},
            {'label': '📝 Prescriptions', 'key': 'prescriptions', 'icon': '📝'},
            {'label': '📋 Templates', 'key': 'templates', 'icon': '📋'},
            {'label': '💊 Medications', 'key': 'medications', 'icon': '💊'},
            {'label': '🧪 Lab Tests', 'key': 'lab_tests', 'icon': '🧪'},
            {'label': '📊 Analytics', 'key': 'analytics', 'icon': '📊'}
        ])
    
    elif user_role == USER_ROLES['ASSISTANT']:
        navigation_items.extend([
            {'label': '🏥 Patient Management', 'key': 'patient_management', 'icon': '🏥'},
            {'label': '📅 Visit Management', 'key': 'visit_management', 'icon': '📅'},
            {'label': '💊 Medications', 'key': 'medications', 'icon': '💊'},
            {'label': '🧪 Lab Tests', 'key': 'lab_tests', 'icon': '🧪'},
            {'label': '📈 My Activity', 'key': 'analytics', 'icon': '📈'}
        ])
    
    return navigation_items

def filter_data_by_permissions(data: List[Dict[str, Any]], data_type: str) -> List[Dict[str, Any]]:
    """
    Filter data based on user permissions
    
    Args:
        data (List[Dict[str, Any]]): Data to filter
        data_type (str): Type of data ('patients', 'prescriptions', etc.)
    
    Returns:
        List[Dict[str, Any]]: Filtered data
    """
    from auth.authentication import get_current_user_id, get_current_user_role
    
    user_id = get_current_user_id()
    user_role = get_current_user_role()
    
    if not user_id or not user_role:
        return []
    
    # Super admin sees all data
    if user_role == USER_ROLES['SUPER_ADMIN']:
        return data
    
    # Role-specific filtering
    if data_type == 'prescriptions':
        # Doctors see only their own prescriptions
        if user_role == USER_ROLES['DOCTOR']:
            return [item for item in data if item.get('doctor_id') == user_id]
    
    elif data_type == 'templates':
        # Users see only their own templates
        return [item for item in data if item.get('doctor_id') == user_id or item.get('created_by') == user_id]
    
    elif data_type == 'analytics':
        # Non-admin users see only their own analytics
        if user_role != USER_ROLES['SUPER_ADMIN']:
            return [item for item in data if item.get('user_id') == user_id]
    
    return data

def get_permission_summary(user_role: str) -> Dict[str, List[str]]:
    """
    Get a summary of permissions for a role
    
    Args:
        user_role (str): User role
    
    Returns:
        Dict[str, List[str]]: Categorized permissions
    """
    permissions = RolePermissions.get_role_permissions(user_role)
    
    summary = {
        'User Management': [],
        'Patient Management': [],
        'Prescriptions': [],
        'Medications': [],
        'Lab Tests': [],
        'Templates': [],
        'Analytics': [],
        'System Administration': [],
        'Special Features': []
    }
    
    for permission in permissions:
        perm_name = permission.value
        
        if 'user' in perm_name:
            summary['User Management'].append(perm_name)
        elif 'patient' in perm_name:
            summary['Patient Management'].append(perm_name)
        elif 'prescription' in perm_name:
            summary['Prescriptions'].append(perm_name)
        elif 'medication' in perm_name:
            summary['Medications'].append(perm_name)
        elif 'lab_test' in perm_name:
            summary['Lab Tests'].append(perm_name)
        elif 'template' in perm_name:
            summary['Templates'].append(perm_name)
        elif 'analytics' in perm_name:
            summary['Analytics'].append(perm_name)
        elif 'system' in perm_name:
            summary['System Administration'].append(perm_name)
        else:
            summary['Special Features'].append(perm_name)
    
    # Remove empty categories
    return {k: v for k, v in summary.items() if v}

def check_data_ownership(data_item: Dict[str, Any], data_type: str) -> bool:
    """
    Check if current user owns or can access specific data
    
    Args:
        data_item (Dict[str, Any]): Data item to check
        data_type (str): Type of data
    
    Returns:
        bool: True if user can access the data
    """
    from auth.authentication import get_current_user_id, get_current_user_role
    
    user_id = get_current_user_id()
    user_role = get_current_user_role()
    
    if not user_id or not user_role:
        return False
    
    # Super admin can access everything
    if user_role == USER_ROLES['SUPER_ADMIN']:
        return True
    
    # Check ownership based on data type
    if data_type == 'prescription':
        return data_item.get('doctor_id') == user_id
    
    elif data_type == 'template':
        return data_item.get('doctor_id') == user_id
    
    elif data_type == 'patient':
        # Doctors can view patients, assistants can view patients they created
        if user_role == USER_ROLES['DOCTOR']:
            return True  # Doctors can view all patients
        elif user_role == USER_ROLES['ASSISTANT']:
            return data_item.get('created_by') == user_id
    
    elif data_type == 'visit':
        # Users can view visits they created
        return data_item.get('created_by') == user_id
    
    return False

def get_user_role_display_name(role: str) -> str:
    """
    Get display name for user role
    
    Args:
        role (str): User role code
    
    Returns:
        str: Display name
    """
    role_names = {
        USER_ROLES['SUPER_ADMIN']: 'Super Administrator',
        USER_ROLES['DOCTOR']: 'Doctor',
        USER_ROLES['ASSISTANT']: 'Assistant'
    }
    
    return role_names.get(role, role.title())

def get_role_description(role: str) -> str:
    """
    Get description of role capabilities
    
    Args:
        role (str): User role code
    
    Returns:
        str: Role description
    """
    descriptions = {
        USER_ROLES['SUPER_ADMIN']: 
            "Complete system administration access including user management, "
            "patient database, medication/lab test databases, and system analytics. "
            "Cannot create prescriptions for medical safety.",
        
        USER_ROLES['DOCTOR']: 
            "Clinical workflow access including today's patients dashboard, "
            "prescription creation with AI analysis, template management, "
            "and analytics for their own practice.",
        
        USER_ROLES['ASSISTANT']: 
            "Patient support functions including patient registration, "
            "visit management, medication/lab test database viewing, "
            "and limited analytics for their own activities."
    }
    
    return descriptions.get(role, "Unknown role")

# Decorator functions for permission checking
def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            PermissionChecker.require_permission(permission)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_any_permission(permissions: List[Permission]):
    """Decorator to require any of the specified permissions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            PermissionChecker.require_any_permission(permissions)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_role_access(allowed_roles: List[str]):
    """Decorator to require specific role access"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            PermissionChecker.require_role(allowed_roles)
            return func(*args, **kwargs)
        return wrapper
    return decorator
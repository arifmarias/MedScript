"""
MedScript Pro - Authentication System
This file handles user authentication, login/logout functionality, and session management.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import streamlit as st
from config.database import execute_query
from config.settings import (
    SESSION_CONFIG, ERROR_MESSAGES, SUCCESS_MESSAGES,
    USER_ROLES, VALIDATION_RULES
)
from utils.helpers import hash_password, verify_password, generate_session_id
from utils.validators import validate_username, validate_password

class AuthenticationManager:
    """Manages user authentication and session handling"""
    
    def __init__(self):
        self.session_timeout = SESSION_CONFIG['TIMEOUT_MINUTES']
        self.max_failed_attempts = SESSION_CONFIG['MAX_FAILED_ATTEMPTS']
        self.lockout_duration = SESSION_CONFIG['LOCKOUT_DURATION_MINUTES']
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Authenticate user credentials
        
        Args:
            username (str): Username
            password (str): Password
        
        Returns:
            Tuple[bool, Optional[Dict[str, Any]], str]: (success, user_data, message)
        """
        try:
            # Validate input format
            username_validation = validate_username(username)
            password_validation = validate_password(password)
            
            if username_validation.has_errors() or password_validation.has_errors():
                return False, None, ERROR_MESSAGES['VALIDATION_ERROR']
            
            # Check if user exists and get user data
            user_query = """
            SELECT id, username, password_hash, full_name, user_type, 
                   medical_license, specialization, email, phone, 
                   is_active, failed_login_attempts, locked_until, last_login
            FROM users 
            WHERE username = ? AND is_active = 1
            """
            
            user_data = execute_query(user_query, (username,), fetch='one')
            
            if not user_data:
                self._log_failed_attempt(username)
                return False, None, ERROR_MESSAGES['LOGIN_FAILED']
            
            # Check if account is locked
            if self._is_account_locked(user_data):
                return False, None, f"Account is temporarily locked. Try again later."
            
            # Verify password
            if not verify_password(password, user_data['password_hash']):
                self._increment_failed_attempts(user_data['id'])
                return False, None, ERROR_MESSAGES['LOGIN_FAILED']
            
            # Reset failed attempts on successful login
            self._reset_failed_attempts(user_data['id'])
            
            # Update last login
            self._update_last_login(user_data['id'])
            
            # Prepare user session data
            session_user = {
                'id': user_data['id'],
                'username': user_data['username'],
                'full_name': user_data['full_name'],
                'user_type': user_data['user_type'],
                'medical_license': user_data['medical_license'],
                'specialization': user_data['specialization'],
                'email': user_data['email'],
                'phone': user_data['phone'],
                'login_time': datetime.now(),
                'session_id': generate_session_id()
            }
            
            return True, session_user, SUCCESS_MESSAGES['LOGIN_SUCCESS']
        
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            return False, None, ERROR_MESSAGES['DATABASE_ERROR']
    
    def _is_account_locked(self, user_data: Dict[str, Any]) -> bool:
        """Check if user account is locked"""
        if user_data['failed_login_attempts'] >= self.max_failed_attempts:
            if user_data['locked_until']:
                try:
                    locked_until = datetime.fromisoformat(user_data['locked_until'])
                    if datetime.now() < locked_until:
                        return True
                    else:
                        # Lock period expired, reset
                        self._reset_failed_attempts(user_data['id'])
                        return False
                except (ValueError, TypeError):
                    return False
            else:
                # No lock time set, but max attempts reached
                self._set_account_lock(user_data['id'])
                return True
        return False
    
    def _increment_failed_attempts(self, user_id: int) -> None:
        """Increment failed login attempts"""
        try:
            query = """
            UPDATE users 
            SET failed_login_attempts = failed_login_attempts + 1,
                locked_until = CASE 
                    WHEN failed_login_attempts + 1 >= ? 
                    THEN datetime('now', '+{} minutes')
                    ELSE locked_until 
                END
            WHERE id = ?
            """.format(self.lockout_duration)
            
            execute_query(query, (self.max_failed_attempts, user_id))
        except Exception:
            pass  # Silently fail to not break login flow
    
    def _reset_failed_attempts(self, user_id: int) -> None:
        """Reset failed login attempts"""
        try:
            query = """
            UPDATE users 
            SET failed_login_attempts = 0, locked_until = NULL 
            WHERE id = ?
            """
            execute_query(query, (user_id,))
        except Exception:
            pass
    
    def _set_account_lock(self, user_id: int) -> None:
        """Set account lock time"""
        try:
            query = """
            UPDATE users 
            SET locked_until = datetime('now', '+{} minutes')
            WHERE id = ?
            """.format(self.lockout_duration)
            
            execute_query(query, (user_id,))
        except Exception:
            pass
    
    def _update_last_login(self, user_id: int) -> None:
        """Update last login timestamp"""
        try:
            query = "UPDATE users SET last_login = datetime('now') WHERE id = ?"
            execute_query(query, (user_id,))
        except Exception:
            pass
    
    def _log_failed_attempt(self, username: str) -> None:
        """Log failed login attempt for security monitoring"""
        try:
            # Log to analytics if user exists
            user_query = "SELECT id FROM users WHERE username = ?"
            user_data = execute_query(user_query, (username,), fetch='one')
            
            if user_data:
                analytics_query = """
                INSERT INTO analytics (user_id, action_type, metadata, success)
                VALUES (?, 'failed_login', ?, 0)
                """
                metadata = f'{{"username": "{username}", "timestamp": "{datetime.now().isoformat()}"}}'
                execute_query(analytics_query, (user_data['id'], metadata))
        except Exception:
            pass

def initialize_session():
    """Initialize session state variables"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if 'login_time' not in st.session_state:
        st.session_state.login_time = None
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None

def login_user(username: str, password: str) -> bool:
    """
    Login user and establish session
    
    Args:
        username (str): Username
        password (str): Password
    
    Returns:
        bool: True if login successful
    """
    auth_manager = AuthenticationManager()
    success, user_data, message = auth_manager.authenticate_user(username, password)
    
    if success and user_data:
        # Set session state
        st.session_state.user = user_data
        st.session_state.login_time = user_data['login_time']
        st.session_state.session_id = user_data['session_id']
        
        # Log successful login
        log_user_activity(user_data['id'], 'login', 'Authentication successful')
        
        st.success(message)
        return True
    else:
        st.error(message)
        return False

def logout_user():
    """Logout user and clear session"""
    if st.session_state.get('user'):
        user_id = st.session_state.user['id']
        
        # Log logout
        log_user_activity(user_id, 'logout', 'User logged out')
    
    # Clear session state
    st.session_state.user = None
    st.session_state.login_time = None
    st.session_state.session_id = None
    
    # Clear other session variables
    session_keys_to_clear = [
        'prescription_medications', 'prescription_lab_tests',
        'selected_patient', 'current_prescription', 'edit_mode'
    ]
    
    for key in session_keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.success(SUCCESS_MESSAGES['LOGOUT_SUCCESS'])

def is_authenticated() -> bool:
    """
    Check if user is authenticated
    
    Returns:
        bool: True if user is authenticated
    """
    return (
        st.session_state.get('user') is not None and
        st.session_state.get('login_time') is not None and
        not is_session_expired()
    )

def is_session_expired() -> bool:
    """
    Check if session has expired
    
    Returns:
        bool: True if session expired
    """
    if not st.session_state.get('login_time'):
        return True
    
    login_time = st.session_state.login_time
    if isinstance(login_time, str):
        login_time = datetime.fromisoformat(login_time)
    
    session_duration = datetime.now() - login_time
    max_duration = timedelta(minutes=SESSION_CONFIG['TIMEOUT_MINUTES'])
    
    return session_duration > max_duration

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get current authenticated user
    
    Returns:
        Optional[Dict[str, Any]]: Current user data or None
    """
    if is_authenticated():
        return st.session_state.user
    return None

def get_current_user_id() -> Optional[int]:
    """
    Get current user ID
    
    Returns:
        Optional[int]: Current user ID or None
    """
    user = get_current_user()
    return user.get('id') if user else None

def get_current_user_role() -> Optional[str]:
    """
    Get current user role
    
    Returns:
        Optional[str]: Current user role or None
    """
    user = get_current_user()
    return user.get('user_type') if user else None

def require_authentication():
    """Decorator/function to require authentication"""
    if not is_authenticated():
        if is_session_expired():
            st.error(ERROR_MESSAGES['SESSION_EXPIRED'])
            logout_user()
        else:
            st.error(ERROR_MESSAGES['ACCESS_DENIED'])
        
        show_login_page()
        st.stop()

def require_role(allowed_roles: list):
    """
    Require specific user role(s)
    
    Args:
        allowed_roles (list): List of allowed user roles
    """
    require_authentication()
    
    user_role = get_current_user_role()
    if user_role not in allowed_roles:
        st.error(ERROR_MESSAGES['ACCESS_DENIED'])
        st.info(f"This page requires one of the following roles: {', '.join(allowed_roles)}")
        st.stop()

# def show_login_page(): ... (Function moved to app.py)

def check_session_validity():
    """Check and handle session validity"""
    if st.session_state.get('user'):
        if is_session_expired():
            st.warning("Your session has expired. Please log in again.")
            logout_user()
            return False
    return True

def extend_session():
    """Extend current session"""
    if st.session_state.get('user'):
        st.session_state.login_time = datetime.now()

def log_user_activity(user_id: int, action: str, details: str = None):
    """
    Log user activity for security and analytics
    
    Args:
        user_id (int): User ID
        action (str): Action performed
        details (str): Additional details
    """
    try:
        query = """
        INSERT INTO analytics (user_id, action_type, metadata, timestamp)
        VALUES (?, ?, ?, datetime('now'))
        """
        
        metadata = {
            'action': action,
            'details': details,
            'session_id': st.session_state.get('session_id'),
            'user_agent': 'Streamlit App'
        }
        
        import json
        metadata_json = json.dumps(metadata)
        
        execute_query(query, (user_id, action, metadata_json))
    
    except Exception:
        # Silently fail - don't break app functionality
        pass

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get user data by ID
    
    Args:
        user_id (int): User ID
    
    Returns:
        Optional[Dict[str, Any]]: User data or None
    """
    try:
        query = """
        SELECT id, username, full_name, user_type, medical_license,
               specialization, email, phone, is_active, created_at, last_login
        FROM users
        WHERE id = ? AND is_active = 1
        """
        
        return execute_query(query, (user_id,), fetch='one')
    
    except Exception:
        return None

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Get user data by username
    
    Args:
        username (str): Username
    
    Returns:
        Optional[Dict[str, Any]]: User data or None
    """
    try:
        query = """
        SELECT id, username, full_name, user_type, medical_license,
               specialization, email, phone, is_active, created_at, last_login
        FROM users
        WHERE username = ? AND is_active = 1
        """
        
        return execute_query(query, (username,), fetch='one')
    
    except Exception:
        return None

def update_user_password(user_id: int, new_password: str) -> bool:
    """
    Update user password
    
    Args:
        user_id (int): User ID
        new_password (str): New password
    
    Returns:
        bool: True if successful
    """
    try:
        # Validate password
        validation = validate_password(new_password)
        if validation.has_errors():
            return False
        
        # Hash new password
        hashed_password = hash_password(new_password)
        
        # Update in database
        query = "UPDATE users SET password_hash = ? WHERE id = ?"
        execute_query(query, (hashed_password, user_id))
        
        # Log activity
        log_user_activity(user_id, 'password_change', 'Password updated successfully')
        
        return True
    
    except Exception:
        return False

def get_active_sessions_count() -> int:
    """
    Get count of active sessions (simplified implementation)
    
    Returns:
        int: Number of active sessions
    """
    try:
        # This is a simplified implementation
        # In production, you'd track active sessions in database
        query = """
        SELECT COUNT(*) as count 
        FROM analytics 
        WHERE action_type = 'login' 
        AND timestamp > datetime('now', '-{} minutes')
        """.format(SESSION_CONFIG['TIMEOUT_MINUTES'])
        
        result = execute_query(query, fetch='one')
        return result['count'] if result else 0
    
    except Exception:
        return 0

def force_logout_user(user_id: int) -> bool:
    """
    Force logout a specific user (admin function)
    
    Args:
        user_id (int): User ID to logout
    
    Returns:
        bool: True if successful
    """
    try:
        # Log forced logout
        current_user = get_current_user()
        if current_user:
            log_user_activity(
                current_user['id'], 
                'admin_force_logout', 
                f'Force logged out user ID: {user_id}'
            )
        
        # In a full implementation, you'd invalidate the user's session
        # For now, just log the action
        log_user_activity(user_id, 'forced_logout', 'Logged out by administrator')
        
        return True
    
    except Exception:
        return False
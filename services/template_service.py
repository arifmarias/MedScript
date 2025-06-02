"""
MedScript Pro - Template Service
This file handles prescription template management, creation, and application for doctors.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import streamlit as st
from config.database import execute_query
from config.settings import TEMPLATE_CONFIG, USER_ROLES
from auth.authentication import get_current_user_id, get_current_user_role
from auth.permissions import PermissionChecker, Permission
from utils.validators import validate_required_field
from utils.helpers import safe_json_loads, safe_json_dumps

class TemplateService:
    """Service for managing prescription templates"""
    
    def __init__(self):
        self.categories = TEMPLATE_CONFIG['CATEGORIES']
    
    def create_template(self, template_data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new prescription template
        
        Args:
            template_data (Dict[str, Any]): Template data
        
        Returns:
            Tuple[bool, str, Optional[int]]: (success, message, template_id)
        """
        try:
            # Check permissions
            PermissionChecker.require_permission(Permission.CREATE_TEMPLATES)
            
            # Validate required fields
            validation_errors = []
            if not template_data.get('name'):
                validation_errors.append("Template name is required")
            if not template_data.get('category'):
                validation_errors.append("Template category is required")
            if not template_data.get('medications') and not template_data.get('lab_tests'):
                validation_errors.append("Template must include at least one medication or lab test")
            
            if validation_errors:
                return False, "; ".join(validation_errors), None
            
            doctor_id = get_current_user_id()
            if not doctor_id:
                return False, "User authentication required", None
            
            # Check for duplicate template name for this doctor
            duplicate_check = """
            SELECT COUNT(*) as count FROM templates 
            WHERE doctor_id = ? AND name = ? AND is_active = 1
            """
            result = execute_query(duplicate_check, (doctor_id, template_data['name']), fetch='one')
            if result and result['count'] > 0:
                return False, "A template with this name already exists", None
            
            # Prepare template data
            template_json = self._prepare_template_data(template_data)
            
            # Insert template
            query = """
            INSERT INTO templates (
                doctor_id, name, category, description, template_data,
                medications_data, lab_tests_data, diagnosis_template, 
                instructions_template, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """
            
            params = (
                doctor_id,
                template_data['name'],
                template_data.get('category', 'General Medicine'),
                template_data.get('description', ''),
                template_json,
                safe_json_dumps(template_data.get('medications', [])),
                safe_json_dumps(template_data.get('lab_tests', [])),
                template_data.get('diagnosis', ''),
                template_data.get('instructions', '')
            )
            
            template_id = execute_query(query, params)
            
            if template_id:
                # Log the creation
                self._log_template_activity(doctor_id, 'create_template', template_id)
                return True, "Template created successfully", template_id
            else:
                return False, "Failed to create template", None
        
        except Exception as e:
            st.error(f"Error creating template: {str(e)}")
            return False, f"Error creating template: {str(e)}", None
    
    def update_template(self, template_id: int, template_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update an existing template
        
        Args:
            template_id (int): Template ID
            template_data (Dict[str, Any]): Updated template data
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Check permissions
            PermissionChecker.require_permission(Permission.UPDATE_TEMPLATES)
            
            doctor_id = get_current_user_id()
            if not doctor_id:
                return False, "User authentication required"
            
            # Verify ownership
            if not self._check_template_ownership(template_id, doctor_id):
                return False, "You can only update your own templates"
            
            # Validate required fields
            validation_errors = []
            if not template_data.get('name'):
                validation_errors.append("Template name is required")
            if not template_data.get('category'):
                validation_errors.append("Template category is required")
            
            if validation_errors:
                return False, "; ".join(validation_errors)
            
            # Check for duplicate name (excluding current template)
            duplicate_check = """
            SELECT COUNT(*) as count FROM templates 
            WHERE doctor_id = ? AND name = ? AND id != ? AND is_active = 1
            """
            result = execute_query(duplicate_check, (doctor_id, template_data['name'], template_id), fetch='one')
            if result and result['count'] > 0:
                return False, "A template with this name already exists"
            
            # Prepare template data
            template_json = self._prepare_template_data(template_data)
            
            # Update template
            query = """
            UPDATE templates SET
                name = ?, category = ?, description = ?, template_data = ?,
                medications_data = ?, lab_tests_data = ?, diagnosis_template = ?,
                instructions_template = ?, updated_at = datetime('now')
            WHERE id = ? AND doctor_id = ?
            """
            
            params = (
                template_data['name'],
                template_data.get('category', 'General Medicine'),
                template_data.get('description', ''),
                template_json,
                safe_json_dumps(template_data.get('medications', [])),
                safe_json_dumps(template_data.get('lab_tests', [])),
                template_data.get('diagnosis', ''),
                template_data.get('instructions', ''),
                template_id,
                doctor_id
            )
            
            execute_query(query, params)
            
            # Log the update
            self._log_template_activity(doctor_id, 'update_template', template_id)
            
            return True, "Template updated successfully"
        
        except Exception as e:
            st.error(f"Error updating template: {str(e)}")
            return False, f"Error updating template: {str(e)}"
    
    def delete_template(self, template_id: int) -> Tuple[bool, str]:
        """
        Delete a template (soft delete)
        
        Args:
            template_id (int): Template ID
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Check permissions
            PermissionChecker.require_permission(Permission.DELETE_TEMPLATES)
            
            doctor_id = get_current_user_id()
            if not doctor_id:
                return False, "User authentication required"
            
            # Verify ownership
            if not self._check_template_ownership(template_id, doctor_id):
                return False, "You can only delete your own templates"
            
            # Soft delete template
            query = """
            UPDATE templates SET is_active = 0, updated_at = datetime('now')
            WHERE id = ? AND doctor_id = ?
            """
            
            execute_query(query, (template_id, doctor_id))
            
            # Log the deletion
            self._log_template_activity(doctor_id, 'delete_template', template_id)
            
            return True, "Template deleted successfully"
        
        except Exception as e:
            st.error(f"Error deleting template: {str(e)}")
            return False, f"Error deleting template: {str(e)}"
    
    def get_template_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """
        Get template by ID
        
        Args:
            template_id (int): Template ID
        
        Returns:
            Optional[Dict[str, Any]]: Template data or None
        """
        try:
            doctor_id = get_current_user_id()
            if not doctor_id:
                return None
            
            query = """
            SELECT t.*, u.full_name as doctor_name
            FROM templates t
            JOIN users u ON t.doctor_id = u.id
            WHERE t.id = ? AND t.doctor_id = ? AND t.is_active = 1
            """
            
            template = execute_query(query, (template_id, doctor_id), fetch='one')
            
            if template:
                return self._process_template_data(template)
            
            return None
        
        except Exception as e:
            st.error(f"Error getting template: {str(e)}")
            return None
    
    def get_doctor_templates(self, doctor_id: int = None, category: str = None) -> List[Dict[str, Any]]:
        """
        Get templates for a doctor
        
        Args:
            doctor_id (int): Doctor ID (defaults to current user)
            category (str): Filter by category
        
        Returns:
            List[Dict[str, Any]]: List of templates
        """
        try:
            if not doctor_id:
                doctor_id = get_current_user_id()
            
            if not doctor_id:
                return []
            
            # Build query with optional category filter
            base_query = """
            SELECT t.*, u.full_name as doctor_name
            FROM templates t
            JOIN users u ON t.doctor_id = u.id
            WHERE t.doctor_id = ? AND t.is_active = 1
            """
            
            params = [doctor_id]
            
            if category:
                base_query += " AND t.category = ?"
                params.append(category)
            
            base_query += " ORDER BY t.usage_count DESC, t.name ASC"
            
            templates = execute_query(base_query, params, fetch='all')
            
            return [self._process_template_data(template) for template in templates]
        
        except Exception as e:
            st.error(f"Error getting templates: {str(e)}")
            return []
    
    def apply_template_to_prescription(self, template_id: int) -> Optional[Dict[str, Any]]:
        """
        Apply template to create prescription data
        
        Args:
            template_id (int): Template ID
        
        Returns:
            Optional[Dict[str, Any]]: Prescription data from template
        """
        try:
            template = self.get_template_by_id(template_id)
            if not template:
                return None
            
            # Increment usage count
            self._increment_template_usage(template_id)
            
            # Build prescription data from template
            prescription_data = {
                'diagnosis': template.get('diagnosis_template', ''),
                'notes': template.get('instructions_template', ''),
                'medications': template.get('medications', []),
                'lab_tests': template.get('lab_tests', []),
                'template_used': {
                    'id': template_id,
                    'name': template['name'],
                    'category': template['category']
                }
            }
            
            # Log template application
            doctor_id = get_current_user_id()
            self._log_template_activity(doctor_id, 'apply_template', template_id)
            
            return prescription_data
        
        except Exception as e:
            st.error(f"Error applying template: {str(e)}")
            return None
    
    def duplicate_template(self, template_id: int, new_name: str) -> Tuple[bool, str, Optional[int]]:
        """
        Duplicate an existing template
        
        Args:
            template_id (int): Template ID to duplicate
            new_name (str): Name for the new template
        
        Returns:
            Tuple[bool, str, Optional[int]]: (success, message, new_template_id)
        """
        try:
            # Get original template
            original_template = self.get_template_by_id(template_id)
            if not original_template:
                return False, "Template not found", None
            
            # Create new template data
            new_template_data = {
                'name': new_name,
                'category': original_template['category'],
                'description': f"Copy of {original_template['name']}",
                'diagnosis': original_template.get('diagnosis_template', ''),
                'instructions': original_template.get('instructions_template', ''),
                'medications': original_template.get('medications', []),
                'lab_tests': original_template.get('lab_tests', [])
            }
            
            return self.create_template(new_template_data)
        
        except Exception as e:
            st.error(f"Error duplicating template: {str(e)}")
            return False, f"Error duplicating template: {str(e)}", None
    
    def get_template_categories(self) -> List[str]:
        """
        Get list of available template categories
        
        Returns:
            List[str]: List of categories
        """
        return self.categories.copy()
    
    def get_template_statistics(self, doctor_id: int = None) -> Dict[str, Any]:
        """
        Get template usage statistics
        
        Args:
            doctor_id (int): Doctor ID (defaults to current user)
        
        Returns:
            Dict[str, Any]: Template statistics
        """
        try:
            if not doctor_id:
                doctor_id = get_current_user_id()
            
            if not doctor_id:
                return {}
            
            # Total templates
            total_query = """
            SELECT COUNT(*) as count FROM templates 
            WHERE doctor_id = ? AND is_active = 1
            """
            total_result = execute_query(total_query, (doctor_id,), fetch='one')
            total_templates = total_result['count'] if total_result else 0
            
            # Templates by category
            category_query = """
            SELECT category, COUNT(*) as count
            FROM templates
            WHERE doctor_id = ? AND is_active = 1
            GROUP BY category
            ORDER BY count DESC
            """
            category_stats = execute_query(category_query, (doctor_id,), fetch='all')
            
            # Most used templates
            usage_query = """
            SELECT name, usage_count
            FROM templates
            WHERE doctor_id = ? AND is_active = 1
            ORDER BY usage_count DESC
            LIMIT 5
            """
            top_templates = execute_query(usage_query, (doctor_id,), fetch='all')
            
            # Recent templates
            recent_query = """
            SELECT name, created_at
            FROM templates
            WHERE doctor_id = ? AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 5
            """
            recent_templates = execute_query(recent_query, (doctor_id,), fetch='all')
            
            return {
                'total_templates': total_templates,
                'by_category': category_stats,
                'most_used': top_templates,
                'recent': recent_templates
            }
        
        except Exception as e:
            st.error(f"Error getting template statistics: {str(e)}")
            return {}
    
    def search_templates(self, search_term: str, doctor_id: int = None, 
                        category: str = None) -> List[Dict[str, Any]]:
        """
        Search templates by name, description, or content
        
        Args:
            search_term (str): Search term
            doctor_id (int): Doctor ID (defaults to current user)
            category (str): Filter by category
        
        Returns:
            List[Dict[str, Any]]: Matching templates
        """
        try:
            if not doctor_id:
                doctor_id = get_current_user_id()
            
            if not doctor_id or not search_term:
                return []
            
            search_term = f"%{search_term.lower()}%"
            
            base_query = """
            SELECT t.*, u.full_name as doctor_name
            FROM templates t
            JOIN users u ON t.doctor_id = u.id
            WHERE t.doctor_id = ? AND t.is_active = 1
            AND (
                LOWER(t.name) LIKE ? OR 
                LOWER(t.description) LIKE ? OR
                LOWER(t.diagnosis_template) LIKE ?
            )
            """
            
            params = [doctor_id, search_term, search_term, search_term]
            
            if category:
                base_query += " AND t.category = ?"
                params.append(category)
            
            base_query += " ORDER BY t.usage_count DESC, t.name ASC"
            
            templates = execute_query(base_query, params, fetch='all')
            
            return [self._process_template_data(template) for template in templates]
        
        except Exception as e:
            st.error(f"Error searching templates: {str(e)}")
            return []
    
    def export_templates(self, doctor_id: int = None) -> List[Dict[str, Any]]:
        """
        Export templates for backup or sharing
        
        Args:
            doctor_id (int): Doctor ID (defaults to current user)
        
        Returns:
            List[Dict[str, Any]]: Template export data
        """
        try:
            if not doctor_id:
                doctor_id = get_current_user_id()
            
            if not doctor_id:
                return []
            
            templates = self.get_doctor_templates(doctor_id)
            
            # Prepare export data
            export_data = []
            for template in templates:
                export_item = {
                    'name': template['name'],
                    'category': template['category'],
                    'description': template['description'],
                    'diagnosis_template': template.get('diagnosis_template', ''),
                    'instructions_template': template.get('instructions_template', ''),
                    'medications': template.get('medications', []),
                    'lab_tests': template.get('lab_tests', []),
                    'usage_count': template.get('usage_count', 0),
                    'created_at': template.get('created_at', ''),
                    'export_timestamp': datetime.now().isoformat()
                }
                export_data.append(export_item)
            
            return export_data
        
        except Exception as e:
            st.error(f"Error exporting templates: {str(e)}")
            return []
    
    def _prepare_template_data(self, template_data: Dict[str, Any]) -> str:
        """Prepare template data for database storage"""
        data = {
            'name': template_data.get('name', ''),
            'category': template_data.get('category', ''),
            'description': template_data.get('description', ''),
            'diagnosis': template_data.get('diagnosis', ''),
            'instructions': template_data.get('instructions', ''),
            'medications': template_data.get('medications', []),
            'lab_tests': template_data.get('lab_tests', []),
            'created_at': datetime.now().isoformat()
        }
        return safe_json_dumps(data)
    
    def _process_template_data(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """Process template data from database"""
        processed = dict(template)
        
        # Parse JSON data
        template_data = safe_json_loads(template.get('template_data', '{}'), {})
        medications_data = safe_json_loads(template.get('medications_data', '[]'), [])
        lab_tests_data = safe_json_loads(template.get('lab_tests_data', '[]'), [])
        
        # Merge data
        processed.update(template_data)
        processed['medications'] = medications_data
        processed['lab_tests'] = lab_tests_data
        
        return processed
    
    def _check_template_ownership(self, template_id: int, doctor_id: int) -> bool:
        """Check if doctor owns the template"""
        query = "SELECT COUNT(*) as count FROM templates WHERE id = ? AND doctor_id = ?"
        result = execute_query(query, (template_id, doctor_id), fetch='one')
        return result and result['count'] > 0
    
    def _increment_template_usage(self, template_id: int) -> None:
        """Increment template usage count"""
        try:
            query = """
            UPDATE templates SET usage_count = usage_count + 1, updated_at = datetime('now')
            WHERE id = ?
            """
            execute_query(query, (template_id,))
        except Exception:
            pass  # Silently fail - don't break functionality
    
    def _log_template_activity(self, doctor_id: int, action: str, template_id: int) -> None:
        """Log template activity for analytics"""
        try:
            query = """
            INSERT INTO analytics (user_id, action_type, entity_type, entity_id, timestamp)
            VALUES (?, ?, 'template', ?, datetime('now'))
            """
            execute_query(query, (doctor_id, action, template_id))
        except Exception:
            pass  # Silently fail

# Convenience functions for easy access
def create_prescription_template(template_data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
    """
    Create a prescription template (convenience function)
    
    Args:
        template_data (Dict[str, Any]): Template data
    
    Returns:
        Tuple[bool, str, Optional[int]]: (success, message, template_id)
    """
    template_service = TemplateService()
    return template_service.create_template(template_data)

def get_current_user_templates(category: str = None) -> List[Dict[str, Any]]:
    """
    Get templates for current user
    
    Args:
        category (str): Filter by category
    
    Returns:
        List[Dict[str, Any]]: User's templates
    """
    user_id = get_current_user_id()
    user_role = get_current_user_role()
    
    if user_role != USER_ROLES['DOCTOR'] or not user_id:
        return []
    
    template_service = TemplateService()
    return template_service.get_doctor_templates(user_id, category)

def apply_template(template_id: int) -> Optional[Dict[str, Any]]:
    """
    Apply template to prescription (convenience function)
    
    Args:
        template_id (int): Template ID
    
    Returns:
        Optional[Dict[str, Any]]: Prescription data from template
    """
    template_service = TemplateService()
    return template_service.apply_template_to_prescription(template_id)

def get_template_categories() -> List[str]:
    """
    Get available template categories
    
    Returns:
        List[str]: Category list
    """
    template_service = TemplateService()
    return template_service.get_template_categories()

def search_user_templates(search_term: str, category: str = None) -> List[Dict[str, Any]]:
    """
    Search current user's templates
    
    Args:
        search_term (str): Search term
        category (str): Filter by category
    
    Returns:
        List[Dict[str, Any]]: Matching templates
    """
    user_id = get_current_user_id()
    user_role = get_current_user_role()
    
    if user_role != USER_ROLES['DOCTOR'] or not user_id:
        return []
    
    template_service = TemplateService()
    return template_service.search_templates(search_term, user_id, category)

def validate_template_data(template_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate template data
    
    Args:
        template_data (Dict[str, Any]): Template data to validate
    
    Returns:
        Tuple[bool, List[str]]: (is_valid, error_messages)
    """
    errors = []
    
    # Required fields
    if not template_data.get('name', '').strip():
        errors.append("Template name is required")
    
    if not template_data.get('category', '').strip():
        errors.append("Template category is required")
    
    # Check if template has content
    has_medications = bool(template_data.get('medications'))
    has_lab_tests = bool(template_data.get('lab_tests'))
    has_diagnosis = bool(template_data.get('diagnosis', '').strip())
    has_instructions = bool(template_data.get('instructions', '').strip())
    
    if not any([has_medications, has_lab_tests, has_diagnosis, has_instructions]):
        errors.append("Template must include at least one item (medications, lab tests, diagnosis, or instructions)")
    
    # Validate category
    template_service = TemplateService()
    valid_categories = template_service.get_template_categories()
    if template_data.get('category') and template_data['category'] not in valid_categories:
        errors.append(f"Invalid category. Must be one of: {', '.join(valid_categories)}")
    
    # Validate name length
    name = template_data.get('name', '')
    if len(name) > 100:
        errors.append("Template name must be 100 characters or less")
    
    return len(errors) == 0, errors

def get_template_usage_stats() -> Dict[str, Any]:
    """
    Get template usage statistics for current user
    
    Returns:
        Dict[str, Any]: Usage statistics
    """
    user_id = get_current_user_id()
    user_role = get_current_user_role()
    
    if user_role != USER_ROLES['DOCTOR'] or not user_id:
        return {}
    
    template_service = TemplateService()
    return template_service.get_template_statistics(user_id)
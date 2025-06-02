"""
MedScript Pro - Analytics Service
This file handles analytics data processing, metrics calculation, and reporting.
"""

import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import streamlit as st
from config.database import execute_query
from config.settings import ANALYTICS_CONFIG, USER_ROLES
from utils.formatters import format_date_display, format_currency, format_percentage
from auth.authentication import get_current_user_id, get_current_user_role

class AnalyticsService:
    """Service for analytics data processing and reporting"""
    
    def __init__(self):
        self.default_days_range = ANALYTICS_CONFIG['DEFAULT_DAYS_RANGE']
        self.max_days_range = ANALYTICS_CONFIG['MAX_DAYS_RANGE']
        self.chart_colors = ANALYTICS_CONFIG['CHART_COLORS']
    
    def get_dashboard_metrics(self, user_role: str, user_id: int = None, 
                            days_back: int = None) -> Dict[str, Any]:
        """
        Get dashboard metrics based on user role and permissions
        
        Args:
            user_role (str): User role
            user_id (int): User ID for role-based filtering
            days_back (int): Number of days to look back
        
        Returns:
            Dict[str, Any]: Dashboard metrics
        """
        try:
            if not days_back:
                days_back = self.default_days_range
            
            date_filter = f"datetime('now', '-{days_back} days')"
            
            metrics = {}
            
            if user_role == USER_ROLES['SUPER_ADMIN']:
                metrics = self._get_admin_metrics(date_filter)
            elif user_role == USER_ROLES['DOCTOR']:
                metrics = self._get_doctor_metrics(user_id, date_filter)
            elif user_role == USER_ROLES['ASSISTANT']:
                metrics = self._get_assistant_metrics(user_id, date_filter)
            
            # Add time range info
            metrics['time_range'] = {
                'days_back': days_back,
                'start_date': (datetime.now() - timedelta(days=days_back)).date(),
                'end_date': datetime.now().date()
            }
            
            return metrics
        
        except Exception as e:
            st.error(f"Error getting dashboard metrics: {str(e)}")
            return {}
    
    def _get_admin_metrics(self, date_filter: str) -> Dict[str, Any]:
        """Get metrics for super admin dashboard"""
        metrics = {}
        
        # Total counts
        metrics['total_users'] = self._get_count("SELECT COUNT(*) FROM users WHERE is_active = 1")
        metrics['total_patients'] = self._get_count("SELECT COUNT(*) FROM patients WHERE is_active = 1")
        metrics['total_prescriptions'] = self._get_count("SELECT COUNT(*) FROM prescriptions")
        metrics['total_medications'] = self._get_count("SELECT COUNT(*) FROM medications WHERE is_active = 1")
        
        # Recent activity
        recent_query = f"SELECT COUNT(*) FROM prescriptions WHERE created_at >= {date_filter}"
        metrics['recent_prescriptions'] = self._get_count(recent_query)
        
        recent_patients_query = f"SELECT COUNT(*) FROM patients WHERE created_at >= {date_filter}"
        metrics['recent_patients'] = self._get_count(recent_patients_query)
        
        # User activity
        user_activity_query = f"""
        SELECT u.user_type, COUNT(*) as count
        FROM analytics a
        JOIN users u ON a.user_id = u.id
        WHERE a.timestamp >= {date_filter}
        GROUP BY u.user_type
        """
        metrics['user_activity'] = self._execute_analytics_query(user_activity_query)
        
        # Top doctors by prescriptions
        top_doctors_query = f"""
        SELECT u.full_name, COUNT(p.id) as prescription_count
        FROM prescriptions p
        JOIN users u ON p.doctor_id = u.id
        WHERE p.created_at >= {date_filter}
        GROUP BY p.doctor_id, u.full_name
        ORDER BY prescription_count DESC
        LIMIT 5
        """
        metrics['top_doctors'] = self._execute_analytics_query(top_doctors_query)
        
        return metrics
    
    def _get_doctor_metrics(self, doctor_id: int, date_filter: str) -> Dict[str, Any]:
        """Get metrics for doctor dashboard"""
        metrics = {}
        
        # Doctor's prescriptions
        prescriptions_query = f"""
        SELECT COUNT(*) FROM prescriptions 
        WHERE doctor_id = ? AND created_at >= {date_filter}
        """
        metrics['my_prescriptions'] = self._get_count(prescriptions_query, (doctor_id,))
        
        # Today's patients
        today_patients_query = """
        SELECT COUNT(DISTINCT pv.patient_id)
        FROM patient_visits pv
        WHERE pv.visit_date = date('now')
        """
        metrics['todays_patients'] = self._get_count(today_patients_query)
        
        # Completed consultations today
        completed_today_query = """
        SELECT COUNT(*)
        FROM patient_visits pv
        WHERE pv.visit_date = date('now') AND pv.consultation_completed = 1
        """
        metrics['completed_today'] = self._get_count(completed_today_query)
        
        # Pending consultations
        pending_today_query = """
        SELECT COUNT(*)
        FROM patient_visits pv
        WHERE pv.visit_date = date('now') AND pv.consultation_completed = 0
        """
        metrics['pending_today'] = self._get_count(pending_today_query)
        
        # My patients (unique patients prescribed to)
        my_patients_query = f"""
        SELECT COUNT(DISTINCT patient_id) FROM prescriptions 
        WHERE doctor_id = ? AND created_at >= {date_filter}
        """
        metrics['my_patients'] = self._get_count(my_patients_query, (doctor_id,))
        
        # My templates
        templates_query = "SELECT COUNT(*) FROM templates WHERE doctor_id = ? AND is_active = 1"
        metrics['my_templates'] = self._get_count(templates_query, (doctor_id,))
        
        return metrics
    
    def _get_assistant_metrics(self, assistant_id: int, date_filter: str) -> Dict[str, Any]:
        """Get metrics for assistant dashboard"""
        metrics = {}
        
        # Patients registered by this assistant
        patients_query = f"""
        SELECT COUNT(*) FROM patients 
        WHERE created_by = ? AND created_at >= {date_filter}
        """
        metrics['patients_registered'] = self._get_count(patients_query, (assistant_id,))
        
        # Visits recorded by this assistant
        visits_query = f"""
        SELECT COUNT(*) FROM patient_visits 
        WHERE created_by = ? AND created_at >= {date_filter}
        """
        metrics['visits_recorded'] = self._get_count(visits_query, (assistant_id,))
        
        # Today's visits
        today_visits_query = """
        SELECT COUNT(*) FROM patient_visits 
        WHERE created_by = ? AND visit_date = date('now')
        """
        metrics['todays_visits'] = self._get_count(today_visits_query, (assistant_id,))
        
        # Total patients managed
        total_patients_query = "SELECT COUNT(*) FROM patients WHERE created_by = ?"
        metrics['total_patients'] = self._get_count(total_patients_query, (assistant_id,))
        
        return metrics
    
    def get_prescription_analytics(self, user_role: str, user_id: int = None, 
                                 days_back: int = None) -> Dict[str, Any]:
        """
        Get prescription analytics data
        
        Args:
            user_role (str): User role
            user_id (int): User ID for filtering
            days_back (int): Number of days to analyze
        
        Returns:
            Dict[str, Any]: Prescription analytics
        """
        try:
            if not days_back:
                days_back = self.default_days_range
            
            date_filter = f"datetime('now', '-{days_back} days')"
            analytics = {}
            
            # Base query filters based on role
            if user_role == USER_ROLES['DOCTOR'] and user_id:
                doctor_filter = f"AND doctor_id = {user_id}"
            elif user_role == USER_ROLES['ASSISTANT']:
                # Assistants see limited analytics
                return self._get_limited_prescription_analytics(user_id, date_filter)
            else:
                doctor_filter = ""
            
            # Prescriptions over time
            prescriptions_timeline_query = f"""
            SELECT date(created_at) as date, COUNT(*) as count
            FROM prescriptions
            WHERE created_at >= {date_filter} {doctor_filter}
            GROUP BY date(created_at)
            ORDER BY date
            """
            analytics['prescriptions_timeline'] = self._execute_analytics_query(prescriptions_timeline_query)
            
            # Top medications prescribed
            top_medications_query = f"""
            SELECT m.name, COUNT(*) as count
            FROM prescription_items pi
            JOIN medications m ON pi.medication_id = m.id
            JOIN prescriptions p ON pi.prescription_id = p.id
            WHERE p.created_at >= {date_filter} {doctor_filter}
            GROUP BY m.id, m.name
            ORDER BY count DESC
            LIMIT 10
            """
            analytics['top_medications'] = self._execute_analytics_query(top_medications_query)
            
            # Prescription status distribution
            status_query = f"""
            SELECT status, COUNT(*) as count
            FROM prescriptions
            WHERE created_at >= {date_filter} {doctor_filter}
            GROUP BY status
            """
            analytics['status_distribution'] = self._execute_analytics_query(status_query)
            
            # Top diagnoses
            diagnoses_query = f"""
            SELECT diagnosis, COUNT(*) as count
            FROM prescriptions
            WHERE created_at >= {date_filter} {doctor_filter}
            AND diagnosis IS NOT NULL AND diagnosis != ''
            GROUP BY diagnosis
            ORDER BY count DESC
            LIMIT 10
            """
            analytics['top_diagnoses'] = self._execute_analytics_query(diagnoses_query)
            
            # Lab tests frequency
            lab_tests_query = f"""
            SELECT lt.test_name, COUNT(*) as count
            FROM prescription_lab_tests plt
            JOIN lab_tests lt ON plt.lab_test_id = lt.id
            JOIN prescriptions p ON plt.prescription_id = p.id
            WHERE p.created_at >= {date_filter} {doctor_filter}
            GROUP BY lt.id, lt.test_name
            ORDER BY count DESC
            LIMIT 10
            """
            analytics['top_lab_tests'] = self._execute_analytics_query(lab_tests_query)
            
            return analytics
        
        except Exception as e:
            st.error(f"Error getting prescription analytics: {str(e)}")
            return {}
    
    def _get_limited_prescription_analytics(self, assistant_id: int, date_filter: str) -> Dict[str, Any]:
        """Get limited prescription analytics for assistants"""
        analytics = {}
        
        # Only show analytics for patients they registered
        patient_ids_query = f"SELECT id FROM patients WHERE created_by = {assistant_id}"
        patient_ids_result = self._execute_analytics_query(patient_ids_query)
        
        if not patient_ids_result:
            return analytics
        
        patient_ids = [str(row['id']) for row in patient_ids_result]
        patient_filter = f"AND patient_id IN ({','.join(patient_ids)})"
        
        # Prescriptions for their patients
        prescriptions_timeline_query = f"""
        SELECT date(created_at) as date, COUNT(*) as count
        FROM prescriptions
        WHERE created_at >= {date_filter} {patient_filter}
        GROUP BY date(created_at)
        ORDER BY date
        """
        analytics['prescriptions_timeline'] = self._execute_analytics_query(prescriptions_timeline_query)
        
        return analytics
    
    def get_patient_analytics(self, user_role: str, user_id: int = None, 
                            days_back: int = None) -> Dict[str, Any]:
        """
        Get patient analytics data
        
        Args:
            user_role (str): User role
            user_id (int): User ID for filtering
            days_back (int): Number of days to analyze
        
        Returns:
            Dict[str, Any]: Patient analytics
        """
        try:
            if not days_back:
                days_back = self.default_days_range
            
            date_filter = f"datetime('now', '-{days_back} days')"
            analytics = {}
            
            # Role-based filtering
            if user_role == USER_ROLES['ASSISTANT'] and user_id:
                assistant_filter = f"AND created_by = {user_id}"
            elif user_role == USER_ROLES['DOCTOR']:
                # Doctors see all patients but limited details
                assistant_filter = ""
            else:
                assistant_filter = ""
            
            # Patient registrations over time
            registrations_query = f"""
            SELECT date(created_at) as date, COUNT(*) as count
            FROM patients
            WHERE created_at >= {date_filter} {assistant_filter}
            GROUP BY date(created_at)
            ORDER BY date
            """
            analytics['patient_registrations'] = self._execute_analytics_query(registrations_query)
            
            # Age distribution
            age_distribution_query = f"""
            SELECT 
                CASE 
                    WHEN (julianday('now') - julianday(date_of_birth))/365.25 < 18 THEN 'Under 18'
                    WHEN (julianday('now') - julianday(date_of_birth))/365.25 < 35 THEN '18-34'
                    WHEN (julianday('now') - julianday(date_of_birth))/365.25 < 50 THEN '35-49'
                    WHEN (julianday('now') - julianday(date_of_birth))/365.25 < 65 THEN '50-64'
                    ELSE '65+'
                END as age_group,
                COUNT(*) as count
            FROM patients
            WHERE created_at >= {date_filter} {assistant_filter}
            GROUP BY age_group
            """
            analytics['age_distribution'] = self._execute_analytics_query(age_distribution_query)
            
            # Gender distribution
            gender_query = f"""
            SELECT gender, COUNT(*) as count
            FROM patients
            WHERE created_at >= {date_filter} {assistant_filter}
            GROUP BY gender
            """
            analytics['gender_distribution'] = self._execute_analytics_query(gender_query)
            
            # Visit types distribution
            visit_types_query = f"""
            SELECT visit_type, COUNT(*) as count
            FROM patient_visits
            WHERE created_at >= {date_filter}
            GROUP BY visit_type
            ORDER BY count DESC
            """
            analytics['visit_types'] = self._execute_analytics_query(visit_types_query)
            
            return analytics
        
        except Exception as e:
            st.error(f"Error getting patient analytics: {str(e)}")
            return {}
    
    def get_medication_analytics(self, user_role: str, user_id: int = None) -> Dict[str, Any]:
        """
        Get medication analytics data
        
        Args:
            user_role (str): User role
            user_id (int): User ID for filtering
        
        Returns:
            Dict[str, Any]: Medication analytics
        """
        try:
            analytics = {}
            
            # Drug class distribution
            drug_class_query = """
            SELECT drug_class, COUNT(*) as count
            FROM medications
            WHERE is_active = 1
            GROUP BY drug_class
            ORDER BY count DESC
            """
            analytics['drug_class_distribution'] = self._execute_analytics_query(drug_class_query)
            
            # Most prescribed medications (last 30 days)
            most_prescribed_query = """
            SELECT m.name, m.generic_name, COUNT(*) as prescription_count
            FROM prescription_items pi
            JOIN medications m ON pi.medication_id = m.id
            JOIN prescriptions p ON pi.prescription_id = p.id
            WHERE p.created_at >= datetime('now', '-30 days')
            GROUP BY m.id, m.name, m.generic_name
            ORDER BY prescription_count DESC
            LIMIT 15
            """
            analytics['most_prescribed'] = self._execute_analytics_query(most_prescribed_query)
            
            # Favorite medications by doctors
            if user_role == USER_ROLES['DOCTOR'] and user_id:
                favorites_query = """
                SELECT name, generic_name, drug_class
                FROM medications
                WHERE is_favorite = 1 AND created_by = ?
                ORDER BY name
                """
                analytics['doctor_favorites'] = self._execute_analytics_query(favorites_query, (user_id,))
            
            return analytics
        
        except Exception as e:
            st.error(f"Error getting medication analytics: {str(e)}")
            return {}
    
    def get_system_performance_metrics(self) -> Dict[str, Any]:
        """
        Get system performance metrics (admin only)
        
        Returns:
            Dict[str, Any]: System performance metrics
        """
        try:
            metrics = {}
            
            # Database statistics
            from config.database import get_database_stats
            db_stats = get_database_stats()
            metrics['database'] = db_stats
            
            # User activity summary
            activity_query = """
            SELECT 
                action_type,
                COUNT(*) as count,
                DATE(timestamp) as date
            FROM analytics
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY action_type, DATE(timestamp)
            ORDER BY date DESC, count DESC
            """
            metrics['user_activity'] = self._execute_analytics_query(activity_query)
            
            # Error rate
            error_query = """
            SELECT 
                COUNT(CASE WHEN success = 0 THEN 1 END) as errors,
                COUNT(*) as total,
                ROUND(COUNT(CASE WHEN success = 0 THEN 1 END) * 100.0 / COUNT(*), 2) as error_rate
            FROM analytics
            WHERE timestamp >= datetime('now', '-24 hours')
            """
            error_stats = self._execute_analytics_query(error_query)
            metrics['error_rate'] = error_stats[0] if error_stats else {'errors': 0, 'total': 0, 'error_rate': 0}
            
            # Peak usage times
            usage_query = """
            SELECT 
                strftime('%H', timestamp) as hour,
                COUNT(*) as activity_count
            FROM analytics
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY hour
            ORDER BY hour
            """
            metrics['hourly_usage'] = self._execute_analytics_query(usage_query)
            
            return metrics
        
        except Exception as e:
            st.error(f"Error getting system performance metrics: {str(e)}")
            return {}
    
    def get_export_data(self, data_type: str, user_role: str, user_id: int = None, 
                       date_range: Tuple[date, date] = None) -> pd.DataFrame:
        """
        Get data for export based on user permissions
        
        Args:
            data_type (str): Type of data to export
            user_role (str): User role
            user_id (int): User ID for filtering
            date_range (Tuple[date, date]): Date range for filtering
        
        Returns:
            pd.DataFrame: Data for export
        """
        try:
            if not date_range:
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)
                date_range = (start_date, end_date)
            
            start_date, end_date = date_range
            
            if data_type == 'prescriptions':
                return self._export_prescriptions_data(user_role, user_id, start_date, end_date)
            elif data_type == 'patients':
                return self._export_patients_data(user_role, user_id, start_date, end_date)
            elif data_type == 'analytics':
                return self._export_analytics_data(user_role, user_id, start_date, end_date)
            else:
                return pd.DataFrame()
        
        except Exception as e:
            st.error(f"Error exporting data: {str(e)}")
            return pd.DataFrame()
    
    def _export_prescriptions_data(self, user_role: str, user_id: int, 
                                  start_date: date, end_date: date) -> pd.DataFrame:
        """Export prescriptions data"""
        role_filter = ""
        params = [start_date.isoformat(), end_date.isoformat()]
        
        if user_role == USER_ROLES['DOCTOR'] and user_id:
            role_filter = "AND p.doctor_id = ?"
            params.append(user_id)
        
        query = f"""
        SELECT 
            p.prescription_id,
            p.created_at,
            u.full_name as doctor_name,
            pt.first_name || ' ' || pt.last_name as patient_name,
            p.diagnosis,
            p.status,
            COUNT(pi.id) as medication_count,
            COUNT(plt.id) as lab_test_count
        FROM prescriptions p
        JOIN users u ON p.doctor_id = u.id
        JOIN patients pt ON p.patient_id = pt.id
        LEFT JOIN prescription_items pi ON p.id = pi.prescription_id
        LEFT JOIN prescription_lab_tests plt ON p.id = plt.prescription_id
        WHERE date(p.created_at) BETWEEN ? AND ? {role_filter}
        GROUP BY p.id
        ORDER BY p.created_at DESC
        """
        
        results = self._execute_analytics_query(query, params)
        return pd.DataFrame(results)
    
    def _export_patients_data(self, user_role: str, user_id: int, 
                             start_date: date, end_date: date) -> pd.DataFrame:
        """Export patients data"""
        role_filter = ""
        params = [start_date.isoformat(), end_date.isoformat()]
        
        if user_role == USER_ROLES['ASSISTANT'] and user_id:
            role_filter = "AND created_by = ?"
            params.append(user_id)
        
        query = f"""
        SELECT 
            patient_id,
            first_name,
            last_name,
            date_of_birth,
            gender,
            phone,
            email,
            allergies,
            medical_conditions,
            created_at
        FROM patients
        WHERE date(created_at) BETWEEN ? AND ? {role_filter}
        ORDER BY created_at DESC
        """
        
        results = self._execute_analytics_query(query, params)
        return pd.DataFrame(results)
    
    def _export_analytics_data(self, user_role: str, user_id: int, 
                              start_date: date, end_date: date) -> pd.DataFrame:
        """Export analytics data"""
        role_filter = ""
        params = [start_date.isoformat(), end_date.isoformat()]
        
        if user_role != USER_ROLES['SUPER_ADMIN'] and user_id:
            role_filter = "AND user_id = ?"
            params.append(user_id)
        
        query = f"""
        SELECT 
            a.timestamp,
            u.full_name as user_name,
            u.user_type,
            a.action_type,
            a.entity_type,
            a.success
        FROM analytics a
        JOIN users u ON a.user_id = u.id
        WHERE date(a.timestamp) BETWEEN ? AND ? {role_filter}
        ORDER BY a.timestamp DESC
        """
        
        results = self._execute_analytics_query(query, params)
        return pd.DataFrame(results)
    
    def _get_count(self, query: str, params: tuple = None) -> int:
        """Execute count query and return result"""
        try:
            result = execute_query(query, params, fetch='one')
            return list(result.values())[0] if result else 0
        except Exception:
            return 0
    
    def _execute_analytics_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute analytics query and return results"""
        try:
            return execute_query(query, params, fetch='all')
        except Exception as e:
            st.error(f"Analytics query failed: {str(e)}")
            return []

# Convenience functions for easy access
def get_user_dashboard_metrics(days_back: int = None) -> Dict[str, Any]:
    """
    Get dashboard metrics for current user
    
    Args:
        days_back (int): Number of days to analyze
    
    Returns:
        Dict[str, Any]: Dashboard metrics
    """
    user_role = get_current_user_role()
    user_id = get_current_user_id()
    
    if not user_role or not user_id:
        return {}
    
    analytics_service = AnalyticsService()
    return analytics_service.get_dashboard_metrics(user_role, user_id, days_back)

def get_user_prescription_analytics(days_back: int = None) -> Dict[str, Any]:
    """
    Get prescription analytics for current user
    
    Args:
        days_back (int): Number of days to analyze
    
    Returns:
        Dict[str, Any]: Prescription analytics
    """
    user_role = get_current_user_role()
    user_id = get_current_user_id()
    
    if not user_role or not user_id:
        return {}
    
    analytics_service = AnalyticsService()
    return analytics_service.get_prescription_analytics(user_role, user_id, days_back)

def get_user_patient_analytics(days_back: int = None) -> Dict[str, Any]:
    """
    Get patient analytics for current user
    
    Args:
        days_back (int): Number of days to analyze
    
    Returns:
        Dict[str, Any]: Patient analytics
    """
    user_role = get_current_user_role()
    user_id = get_current_user_id()
    
    if not user_role or not user_id:
        return {}
    
    analytics_service = AnalyticsService()
    return analytics_service.get_patient_analytics(user_role, user_id, days_back)

def export_user_data(data_type: str, date_range: Tuple[date, date] = None) -> pd.DataFrame:
    """
    Export data for current user
    
    Args:
        data_type (str): Type of data to export
        date_range (Tuple[date, date]): Date range for export
    
    Returns:
        pd.DataFrame: Export data
    """
    user_role = get_current_user_role()
    user_id = get_current_user_id()
    
    if not user_role or not user_id:
        return pd.DataFrame()
    
    analytics_service = AnalyticsService()
    return analytics_service.get_export_data(data_type, user_role, user_id, date_range)

def log_analytics_event(action_type: str, entity_type: str = None, 
                       entity_id: int = None, metadata: Dict[str, Any] = None, 
                       success: bool = True) -> None:
    """
    Log analytics event
    
    Args:
        action_type (str): Type of action
        entity_type (str): Type of entity
        entity_id (int): Entity ID
        metadata (Dict[str, Any]): Additional metadata
        success (bool): Whether action was successful
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return
        
        query = """
        INSERT INTO analytics (
            user_id, action_type, entity_type, entity_id, 
            metadata, success, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        execute_query(query, (
            user_id, action_type, entity_type, entity_id, 
            metadata_json, success
        ))
    
    except Exception:
        # Silently fail - don't break app functionality
        pass

def get_analytics_summary() -> Dict[str, Any]:
    """
    Get analytics summary for display
    
    Returns:
        Dict[str, Any]: Analytics summary
    """
    try:
        user_role = get_current_user_role()
        if not user_role:
            return {}
        
        analytics_service = AnalyticsService()
        
        # Get basic metrics
        metrics = analytics_service.get_dashboard_metrics(user_role, get_current_user_id())
        
        # Add quick insights
        summary = {
            'metrics': metrics,
            'insights': [],
            'recommendations': []
        }
        
        # Generate insights based on role
        if user_role == USER_ROLES['DOCTOR']:
            if metrics.get('todays_patients', 0) > 0:
                completion_rate = (metrics.get('completed_today', 0) / metrics.get('todays_patients', 1)) * 100
                summary['insights'].append(f"Today's consultation completion rate: {completion_rate:.1f}%")
            
            if metrics.get('my_prescriptions', 0) > 0:
                summary['insights'].append(f"You've written {metrics['my_prescriptions']} prescriptions recently")
        
        elif user_role == USER_ROLES['ASSISTANT']:
            if metrics.get('patients_registered', 0) > 0:
                summary['insights'].append(f"You've registered {metrics['patients_registered']} new patients recently")
            
            if metrics.get('visits_recorded', 0) > 0:
                summary['insights'].append(f"You've recorded {metrics['visits_recorded']} visits recently")
        
        return summary
    
    except Exception as e:
        st.error(f"Error getting analytics summary: {str(e)}")
        return {}
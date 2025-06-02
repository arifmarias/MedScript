"""
MedScript Pro - Database Query Functions
This file contains all database query functions organized by entity type.
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import streamlit as st
from config.database import execute_query, execute_transaction
from utils.helpers import hash_password, generate_unique_id
from utils.formatters import format_date_display

class UserQueries:
    """Database queries for user management"""
    
    @staticmethod
    def create_user(user_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new user
        
        Args:
            user_data (Dict[str, Any]): User information
        
        Returns:
            Optional[int]: User ID if successful, None otherwise
        """
        try:
            # Hash password
            password_hash = hash_password(user_data['password'])
            
            query = """
            INSERT INTO users (
                username, password_hash, full_name, user_type, medical_license,
                specialization, email, phone, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """
            
            params = (
                user_data['username'], password_hash, user_data['full_name'],
                user_data['user_type'], user_data.get('medical_license'),
                user_data.get('specialization'), user_data.get('email'),
                user_data.get('phone')
            )
            
            return execute_query(query, params)
        
        except Exception as e:
            st.error(f"Error creating user: {str(e)}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        query = """
        SELECT id, username, full_name, user_type, medical_license,
               specialization, email, phone, is_active, created_at, last_login
        FROM users WHERE id = ? AND is_active = 1
        """
        return execute_query(query, (user_id,), fetch='one')
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        query = """
        SELECT id, username, password_hash, full_name, user_type, medical_license,
               specialization, email, phone, is_active, failed_login_attempts,
               locked_until, last_login
        FROM users WHERE username = ?
        """
        return execute_query(query, (username,), fetch='one')
    
    @staticmethod
    def get_all_users(include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get all users"""
        query = """
        SELECT id, username, full_name, user_type, medical_license,
               specialization, email, phone, is_active, created_at, last_login
        FROM users
        """
        
        if not include_inactive:
            query += " WHERE is_active = 1"
        
        query += " ORDER BY full_name"
        
        return execute_query(query, fetch='all')
    
    @staticmethod
    def update_user(user_id: int, user_data: Dict[str, Any]) -> bool:
        """Update user information"""
        try:
            query = """
            UPDATE users SET
                full_name = ?, user_type = ?, medical_license = ?,
                specialization = ?, email = ?, phone = ?, updated_at = datetime('now')
            WHERE id = ?
            """
            
            params = (
                user_data['full_name'], user_data['user_type'],
                user_data.get('medical_license'), user_data.get('specialization'),
                user_data.get('email'), user_data.get('phone'), user_id
            )
            
            execute_query(query, params)
            return True
        
        except Exception as e:
            st.error(f"Error updating user: {str(e)}")
            return False
    
    @staticmethod
    def deactivate_user(user_id: int) -> bool:
        """Deactivate user (soft delete)"""
        try:
            query = "UPDATE users SET is_active = 0, updated_at = datetime('now') WHERE id = ?"
            execute_query(query, (user_id,))
            return True
        except Exception as e:
            st.error(f"Error deactivating user: {str(e)}")
            return False
    
    @staticmethod
    def get_users_by_role(role: str) -> List[Dict[str, Any]]:
        """Get users by role"""
        query = """
        SELECT id, username, full_name, medical_license, specialization,
               email, phone, created_at, last_login
        FROM users 
        WHERE user_type = ? AND is_active = 1
        ORDER BY full_name
        """
        return execute_query(query, (role,), fetch='all')

class PatientQueries:
    """Database queries for patient management"""
    
    @staticmethod
    def create_patient(patient_data: Dict[str, Any], created_by: int) -> Optional[int]:
        """Create a new patient"""
        try:
            # Generate patient ID
            patient_id = generate_unique_id('PT')
            
            query = """
            INSERT INTO patients (
                patient_id, first_name, last_name, date_of_birth, gender,
                phone, email, address, allergies, medical_conditions,
                emergency_contact, emergency_phone, insurance_info,
                blood_group, weight, height, notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                patient_id, patient_data['first_name'], patient_data['last_name'],
                patient_data['date_of_birth'], patient_data['gender'],
                patient_data.get('phone'), patient_data.get('email'),
                patient_data.get('address'), patient_data.get('allergies'),
                patient_data.get('medical_conditions'), patient_data.get('emergency_contact'),
                patient_data.get('emergency_phone'), patient_data.get('insurance_info'),
                patient_data.get('blood_group'), patient_data.get('weight'),
                patient_data.get('height'), patient_data.get('notes'), created_by
            )
            
            return execute_query(query, params)
        
        except Exception as e:
            st.error(f"Error creating patient: {str(e)}")
            return None
    
    @staticmethod
    def get_patient_by_id(patient_id: int) -> Optional[Dict[str, Any]]:
        """Get patient by ID"""
        query = """
        SELECT p.*, u.full_name as created_by_name
        FROM patients p
        LEFT JOIN users u ON p.created_by = u.id
        WHERE p.id = ? AND p.is_active = 1
        """
        return execute_query(query, (patient_id,), fetch='one')
    
    @staticmethod
    def get_patient_by_patient_id(patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient by patient ID string"""
        query = """
        SELECT p.*, u.full_name as created_by_name
        FROM patients p
        LEFT JOIN users u ON p.created_by = u.id
        WHERE p.patient_id = ? AND p.is_active = 1
        """
        return execute_query(query, (patient_id,), fetch='one')
    
    @staticmethod
    def search_patients(search_term: str = "", created_by: int = None, 
                       limit: int = 100) -> List[Dict[str, Any]]:
        """Search patients"""
        base_query = """
        SELECT p.*, u.full_name as created_by_name
        FROM patients p
        LEFT JOIN users u ON p.created_by = u.id
        WHERE p.is_active = 1
        """
        
        params = []
        
        if search_term:
            base_query += """ AND (
                LOWER(p.first_name) LIKE ? OR 
                LOWER(p.last_name) LIKE ? OR 
                LOWER(p.patient_id) LIKE ? OR
                LOWER(p.phone) LIKE ?
            )"""
            search_param = f"%{search_term.lower()}%"
            params.extend([search_param, search_param, search_param, search_param])
        
        if created_by:
            base_query += " AND p.created_by = ?"
            params.append(created_by)
        
        base_query += f" ORDER BY p.last_name, p.first_name LIMIT {limit}"
        
        return execute_query(base_query, params, fetch='all')
    
    @staticmethod
    def update_patient(patient_id: int, patient_data: Dict[str, Any]) -> bool:
        """Update patient information"""
        try:
            query = """
            UPDATE patients SET
                first_name = ?, last_name = ?, date_of_birth = ?, gender = ?,
                phone = ?, email = ?, address = ?, allergies = ?,
                medical_conditions = ?, emergency_contact = ?, emergency_phone = ?,
                insurance_info = ?, blood_group = ?, weight = ?, height = ?,
                notes = ?, updated_at = datetime('now')
            WHERE id = ?
            """
            
            params = (
                patient_data['first_name'], patient_data['last_name'],
                patient_data['date_of_birth'], patient_data['gender'],
                patient_data.get('phone'), patient_data.get('email'),
                patient_data.get('address'), patient_data.get('allergies'),
                patient_data.get('medical_conditions'), patient_data.get('emergency_contact'),
                patient_data.get('emergency_phone'), patient_data.get('insurance_info'),
                patient_data.get('blood_group'), patient_data.get('weight'),
                patient_data.get('height'), patient_data.get('notes'), patient_id
            )
            
            execute_query(query, params)
            return True
        
        except Exception as e:
            st.error(f"Error updating patient: {str(e)}")
            return False
    
    @staticmethod
    def get_todays_patients() -> List[Dict[str, Any]]:
        """Get patients with visits scheduled for today"""
        query = """
        SELECT DISTINCT p.*, pv.visit_time, pv.visit_type, pv.current_problems,
               pv.consultation_completed, pv.blood_pressure, pv.temperature,
               pv.pulse_rate, pv.respiratory_rate, pv.oxygen_saturation, pv.notes as visit_notes
        FROM patients p
        JOIN patient_visits pv ON p.id = pv.patient_id
        WHERE pv.visit_date = date('now') AND p.is_active = 1
        ORDER BY pv.visit_time, p.last_name, p.first_name
        """
        return execute_query(query, fetch='all')

class VisitQueries:
    """Database queries for patient visits"""
    
    @staticmethod
    def create_visit(visit_data: Dict[str, Any], created_by: int) -> Optional[int]:
        """Create a new patient visit"""
        try:
            query = """
            INSERT INTO patient_visits (
                patient_id, visit_date, visit_time, visit_type, current_problems,
                is_followup, is_report_consultation, vital_signs, blood_pressure,
                temperature, pulse_rate, respiratory_rate, oxygen_saturation,
                notes, created_by, consultation_completed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """
            
            params = (
                visit_data['patient_id'], visit_data['visit_date'],
                visit_data.get('visit_time'), visit_data['visit_type'],
                visit_data['current_problems'], visit_data.get('is_followup', False),
                visit_data.get('is_report_consultation', False),
                visit_data.get('vital_signs'), visit_data.get('blood_pressure'),
                visit_data.get('temperature'), visit_data.get('pulse_rate'),
                visit_data.get('respiratory_rate'), visit_data.get('oxygen_saturation'),
                visit_data.get('notes'), created_by
            )
            
            return execute_query(query, params)
        
        except Exception as e:
            st.error(f"Error creating visit: {str(e)}")
            return None
    
    @staticmethod
    def get_patient_visits(patient_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get visits for a patient"""
        query = """
        SELECT pv.*, u.full_name as created_by_name
        FROM patient_visits pv
        LEFT JOIN users u ON pv.created_by = u.id
        WHERE pv.patient_id = ?
        ORDER BY pv.visit_date DESC, pv.visit_time DESC
        LIMIT ?
        """
        return execute_query(query, (patient_id, limit), fetch='all')
    
    @staticmethod
    def update_visit(visit_id: int, visit_data: Dict[str, Any]) -> bool:
        """Update visit information"""
        try:
            query = """
            UPDATE patient_visits SET
                visit_date = ?, visit_time = ?, visit_type = ?, current_problems = ?,
                is_followup = ?, is_report_consultation = ?, vital_signs = ?,
                blood_pressure = ?, temperature = ?, pulse_rate = ?,
                respiratory_rate = ?, oxygen_saturation = ?, notes = ?,
                updated_at = datetime('now')
            WHERE id = ?
            """
            
            params = (
                visit_data['visit_date'], visit_data.get('visit_time'),
                visit_data['visit_type'], visit_data['current_problems'],
                visit_data.get('is_followup', False), visit_data.get('is_report_consultation', False),
                visit_data.get('vital_signs'), visit_data.get('blood_pressure'),
                visit_data.get('temperature'), visit_data.get('pulse_rate'),
                visit_data.get('respiratory_rate'), visit_data.get('oxygen_saturation'),
                visit_data.get('notes'), visit_id
            )
            
            execute_query(query, params)
            return True
        
        except Exception as e:
            st.error(f"Error updating visit: {str(e)}")
            return False
    
    @staticmethod
    def mark_consultation_completed(visit_id: int, prescription_id: int = None) -> bool:
        """Mark consultation as completed"""
        try:
            query = """
            UPDATE patient_visits SET
                consultation_completed = 1, prescription_id = ?, updated_at = datetime('now')
            WHERE id = ?
            """
            execute_query(query, (prescription_id, visit_id))
            return True
        except Exception as e:
            st.error(f"Error marking consultation completed: {str(e)}")
            return False

class MedicationQueries:
    """Database queries for medication management"""
    
    @staticmethod
    def create_medication(medication_data: Dict[str, Any], created_by: int) -> Optional[int]:
        """Create a new medication"""
        try:
            query = """
            INSERT INTO medications (
                name, generic_name, brand_names, drug_class, dosage_forms,
                strengths, indications, contraindications, side_effects,
                interactions, precautions, dosage_guidelines, is_controlled,
                manufacturer, storage_conditions, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                medication_data['name'], medication_data.get('generic_name'),
                medication_data.get('brand_names'), medication_data['drug_class'],
                medication_data.get('dosage_forms'), medication_data.get('strengths'),
                medication_data.get('indications'), medication_data.get('contraindications'),
                medication_data.get('side_effects'), medication_data.get('interactions'),
                medication_data.get('precautions'), medication_data.get('dosage_guidelines'),
                medication_data.get('is_controlled', False), medication_data.get('manufacturer'),
                medication_data.get('storage_conditions'), created_by
            )
            
            return execute_query(query, params)
        
        except Exception as e:
            st.error(f"Error creating medication: {str(e)}")
            return None
    
    @staticmethod
    def search_medications(search_term: str = "", drug_class: str = "", 
                          favorites_only: bool = False, created_by: int = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Search medications"""
        base_query = """
        SELECT m.*, u.full_name as created_by_name
        FROM medications m
        LEFT JOIN users u ON m.created_by = u.id
        WHERE m.is_active = 1
        """
        
        params = []
        
        if search_term:
            base_query += """ AND (
                LOWER(m.name) LIKE ? OR 
                LOWER(m.generic_name) LIKE ? OR 
                LOWER(m.brand_names) LIKE ?
            )"""
            search_param = f"%{search_term.lower()}%"
            params.extend([search_param, search_param, search_param])
        
        if drug_class:
            base_query += " AND m.drug_class = ?"
            params.append(drug_class)
        
        if favorites_only and created_by:
            base_query += " AND m.is_favorite = 1 AND m.created_by = ?"
            params.append(created_by)
        
        base_query += f" ORDER BY m.name LIMIT {limit}"
        
        return execute_query(base_query, params, fetch='all')
    
    @staticmethod
    def get_medication_by_id(medication_id: int) -> Optional[Dict[str, Any]]:
        """Get medication by ID"""
        query = """
        SELECT m.*, u.full_name as created_by_name
        FROM medications m
        LEFT JOIN users u ON m.created_by = u.id
        WHERE m.id = ? AND m.is_active = 1
        """
        return execute_query(query, (medication_id,), fetch='one')
    
    @staticmethod
    def update_medication(medication_id: int, medication_data: Dict[str, Any]) -> bool:
        """Update medication information"""
        try:
            query = """
            UPDATE medications SET
                name = ?, generic_name = ?, brand_names = ?, drug_class = ?,
                dosage_forms = ?, strengths = ?, indications = ?,
                contraindications = ?, side_effects = ?, interactions = ?,
                precautions = ?, dosage_guidelines = ?, is_controlled = ?,
                manufacturer = ?, storage_conditions = ?, updated_at = datetime('now')
            WHERE id = ?
            """
            
            params = (
                medication_data['name'], medication_data.get('generic_name'),
                medication_data.get('brand_names'), medication_data['drug_class'],
                medication_data.get('dosage_forms'), medication_data.get('strengths'),
                medication_data.get('indications'), medication_data.get('contraindications'),
                medication_data.get('side_effects'), medication_data.get('interactions'),
                medication_data.get('precautions'), medication_data.get('dosage_guidelines'),
                medication_data.get('is_controlled', False), medication_data.get('manufacturer'),
                medication_data.get('storage_conditions'), medication_id
            )
            
            execute_query(query, params)
            return True
        
        except Exception as e:
            st.error(f"Error updating medication: {str(e)}")
            return False
    
    @staticmethod
    def toggle_favorite_medication(medication_id: int, created_by: int) -> bool:
        """Toggle medication favorite status"""
        try:
            # Get current status
            current_query = "SELECT is_favorite FROM medications WHERE id = ?"
            current = execute_query(current_query, (medication_id,), fetch='one')
            
            if current:
                new_status = not current['is_favorite']
                update_query = """
                UPDATE medications SET is_favorite = ?, updated_at = datetime('now')
                WHERE id = ? AND created_by = ?
                """
                execute_query(update_query, (new_status, medication_id, created_by))
                return True
            
            return False
        
        except Exception as e:
            st.error(f"Error toggling favorite: {str(e)}")
            return False

class LabTestQueries:
    """Database queries for lab test management"""
    
    @staticmethod
    def create_lab_test(test_data: Dict[str, Any], created_by: int) -> Optional[int]:
        """Create a new lab test"""
        try:
            query = """
            INSERT INTO lab_tests (
                test_name, test_code, test_category, normal_range, units,
                description, preparation_required, sample_type, test_method,
                turnaround_time, cost, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                test_data['test_name'], test_data.get('test_code'),
                test_data['test_category'], test_data.get('normal_range'),
                test_data.get('units'), test_data.get('description'),
                test_data.get('preparation_required'), test_data.get('sample_type'),
                test_data.get('test_method'), test_data.get('turnaround_time'),
                test_data.get('cost'), created_by
            )
            
            return execute_query(query, params)
        
        except Exception as e:
            st.error(f"Error creating lab test: {str(e)}")
            return None
    
    @staticmethod
    def search_lab_tests(search_term: str = "", category: str = "",
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Search lab tests"""
        base_query = """
        SELECT lt.*, u.full_name as created_by_name
        FROM lab_tests lt
        LEFT JOIN users u ON lt.created_by = u.id
        WHERE lt.is_active = 1
        """
        
        params = []
        
        if search_term:
            base_query += """ AND (
                LOWER(lt.test_name) LIKE ? OR 
                LOWER(lt.test_code) LIKE ? OR 
                LOWER(lt.description) LIKE ?
            )"""
            search_param = f"%{search_term.lower()}%"
            params.extend([search_param, search_param, search_param])
        
        if category:
            base_query += " AND lt.test_category = ?"
            params.append(category)
        
        base_query += f" ORDER BY lt.test_name LIMIT {limit}"
        
        return execute_query(base_query, params, fetch='all')
    
    @staticmethod
    def get_lab_test_by_id(test_id: int) -> Optional[Dict[str, Any]]:
        """Get lab test by ID"""
        query = """
        SELECT lt.*, u.full_name as created_by_name
        FROM lab_tests lt
        LEFT JOIN users u ON lt.created_by = u.id
        WHERE lt.id = ? AND lt.is_active = 1
        """
        return execute_query(query, (test_id,), fetch='one')

class PrescriptionQueries:
    """Database queries for prescription management"""
    
    @staticmethod
    def create_prescription(prescription_data: Dict[str, Any], doctor_id: int) -> Optional[int]:
        """Create a new prescription"""
        try:
            # Generate prescription ID
            prescription_id = generate_unique_id('RX')
            
            # Start transaction
            queries_and_params = []
            
            # Create prescription
            prescription_query = """
            INSERT INTO prescriptions (
                prescription_id, doctor_id, patient_id, visit_id, diagnosis,
                chief_complaint, notes, status, ai_interaction_analysis,
                follow_up_date, follow_up_instructions, consultation_fee
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            prescription_params = (
                prescription_id, doctor_id, prescription_data['patient_id'],
                prescription_data.get('visit_id'), prescription_data['diagnosis'],
                prescription_data.get('chief_complaint'), prescription_data.get('notes'),
                prescription_data.get('status', 'Active'), prescription_data.get('ai_analysis'),
                prescription_data.get('follow_up_date'), prescription_data.get('follow_up_instructions'),
                prescription_data.get('consultation_fee')
            )
            
            queries_and_params.append((prescription_query, prescription_params))
            
            # Execute transaction
            if execute_transaction(queries_and_params):
                # Get the prescription ID
                get_id_query = "SELECT id FROM prescriptions WHERE prescription_id = ?"
                result = execute_query(get_id_query, (prescription_id,), fetch='one')
                return result['id'] if result else None
            
            return None
        
        except Exception as e:
            st.error(f"Error creating prescription: {str(e)}")
            return None
    
    @staticmethod
    def add_prescription_medication(prescription_id: int, medication_data: Dict[str, Any]) -> bool:
        """Add medication to prescription"""
        try:
            query = """
            INSERT INTO prescription_items (
                prescription_id, medication_id, dosage, frequency, duration,
                quantity, refills, instructions, route_of_administration,
                start_date, end_date, is_substitutable
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                prescription_id, medication_data['medication_id'],
                medication_data['dosage'], medication_data['frequency'],
                medication_data['duration'], medication_data.get('quantity'),
                medication_data.get('refills', 0), medication_data.get('instructions'),
                medication_data.get('route_of_administration'),
                medication_data.get('start_date'), medication_data.get('end_date'),
                medication_data.get('is_substitutable', True)
            )
            
            execute_query(query, params)
            return True
        
        except Exception as e:
            st.error(f"Error adding medication to prescription: {str(e)}")
            return False
    
    @staticmethod
    def add_prescription_lab_test(prescription_id: int, lab_test_data: Dict[str, Any]) -> bool:
        """Add lab test to prescription"""
        try:
            query = """
            INSERT INTO prescription_lab_tests (
                prescription_id, lab_test_id, instructions, urgency,
                sample_collection_date, fasting_required, special_instructions
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                prescription_id, lab_test_data['lab_test_id'],
                lab_test_data.get('instructions'), lab_test_data.get('urgency', 'Routine'),
                lab_test_data.get('sample_collection_date'),
                lab_test_data.get('fasting_required', False),
                lab_test_data.get('special_instructions')
            )
            
            execute_query(query, params)
            return True
        
        except Exception as e:
            st.error(f"Error adding lab test to prescription: {str(e)}")
            return False
    
    @staticmethod
    def get_prescription_details(prescription_id: int) -> Optional[Dict[str, Any]]:
        """Get complete prescription details"""
        try:
            # Get prescription info
            prescription_query = """
            SELECT p.*, 
                   d.full_name as doctor_name, d.medical_license, d.specialization,
                   d.email as doctor_email, d.phone as doctor_phone,
                   pt.first_name, pt.last_name, pt.patient_id, pt.date_of_birth,
                   pt.gender, pt.phone as patient_phone, pt.email as patient_email,
                   pt.address, pt.allergies, pt.medical_conditions
            FROM prescriptions p
            JOIN users d ON p.doctor_id = d.id
            JOIN patients pt ON p.patient_id = pt.id
            WHERE p.id = ?
            """
            
            prescription = execute_query(prescription_query, (prescription_id,), fetch='one')
            if not prescription:
                return None
            
            # Get medications
            medications_query = """
            SELECT pi.*, m.name as medication_name, m.generic_name, m.drug_class
            FROM prescription_items pi
            JOIN medications m ON pi.medication_id = m.id
            WHERE pi.prescription_id = ?
            ORDER BY pi.id
            """
            medications = execute_query(medications_query, (prescription_id,), fetch='all')
            
            # Get lab tests
            lab_tests_query = """
            SELECT plt.*, lt.test_name, lt.test_category, lt.normal_range,
                   lt.preparation_required, lt.sample_type
            FROM prescription_lab_tests plt
            JOIN lab_tests lt ON plt.lab_test_id = lt.id
            WHERE plt.prescription_id = ?
            ORDER BY plt.id
            """
            lab_tests = execute_query(lab_tests_query, (prescription_id,), fetch='all')
            
            # Combine data
            result = dict(prescription)
            result['medications'] = medications
            result['lab_tests'] = lab_tests
            
            return result
        
        except Exception as e:
            st.error(f"Error getting prescription details: {str(e)}")
            return None
    
    @staticmethod
    def get_doctor_prescriptions(doctor_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get prescriptions for a doctor"""
        query = """
        SELECT p.*, pt.first_name, pt.last_name, pt.patient_id
        FROM prescriptions p
        JOIN patients pt ON p.patient_id = pt.id
        WHERE p.doctor_id = ?
        ORDER BY p.created_at DESC
        LIMIT ?
        """
        return execute_query(query, (doctor_id, limit), fetch='all')
    
    @staticmethod
    def search_prescriptions(search_term: str = "", doctor_id: int = None,
                           status: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """Search prescriptions"""
        base_query = """
        SELECT p.*, pt.first_name, pt.last_name, pt.patient_id,
               d.full_name as doctor_name
        FROM prescriptions p
        JOIN patients pt ON p.patient_id = pt.id
        JOIN users d ON p.doctor_id = d.id
        WHERE 1=1
        """
        
        params = []
        
        if search_term:
            base_query += """ AND (
                LOWER(p.prescription_id) LIKE ? OR 
                LOWER(p.diagnosis) LIKE ? OR 
                LOWER(pt.first_name) LIKE ? OR
                LOWER(pt.last_name) LIKE ? OR
                LOWER(pt.patient_id) LIKE ?
            )"""
            search_param = f"%{search_term.lower()}%"
            params.extend([search_param] * 5)
        
        if doctor_id:
            base_query += " AND p.doctor_id = ?"
            params.append(doctor_id)
        
        if status:
            base_query += " AND p.status = ?"
            params.append(status)
        
        base_query += f" ORDER BY p.created_at DESC LIMIT {limit}"
        
        return execute_query(base_query, params, fetch='all')

class TemplateQueries:
    """Database queries for template management"""
    
    @staticmethod
    def create_template(template_data: Dict[str, Any], doctor_id: int) -> Optional[int]:
        """Create a new template"""
        try:
            query = """
            INSERT INTO templates (
                doctor_id, name, category, description, template_data,
                medications_data, lab_tests_data, diagnosis_template,
                instructions_template, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """
            
            params = (
                doctor_id, template_data['name'], template_data['category'],
                template_data.get('description', ''), template_data['template_data'],
                template_data.get('medications_data', '[]'),
                template_data.get('lab_tests_data', '[]'),
                template_data.get('diagnosis_template', ''),
                template_data.get('instructions_template', '')
            )
            
            return execute_query(query, params)
        
        except Exception as e:
            st.error(f"Error creating template: {str(e)}")
            return None
    
    @staticmethod
    def get_doctor_templates(doctor_id: int, category: str = None) -> List[Dict[str, Any]]:
        """Get templates for a doctor"""
        base_query = """
        SELECT * FROM templates 
        WHERE doctor_id = ? AND is_active = 1
        """
        
        params = [doctor_id]
        
        if category:
            base_query += " AND category = ?"
            params.append(category)
        
        base_query += " ORDER BY usage_count DESC, name"
        
        return execute_query(base_query, params, fetch='all')
    
    @staticmethod
    def get_template_by_id(template_id: int) -> Optional[Dict[str, Any]]:
        """Get template by ID"""
        query = "SELECT * FROM templates WHERE id = ? AND is_active = 1"
        return execute_query(query, (template_id,), fetch='one')
    
    @staticmethod
    def update_template(template_id: int, template_data: Dict[str, Any]) -> bool:
        """Update template"""
        try:
            query = """
            UPDATE templates SET
                name = ?, category = ?, description = ?, template_data = ?,
                medications_data = ?, lab_tests_data = ?, diagnosis_template = ?,
                instructions_template = ?, updated_at = datetime('now')
            WHERE id = ?
            """
            
            params = (
                template_data['name'], template_data['category'],
                template_data.get('description', ''), template_data['template_data'],
                template_data.get('medications_data', '[]'),
                template_data.get('lab_tests_data', '[]'),
                template_data.get('diagnosis_template', ''),
                template_data.get('instructions_template', ''), template_id
            )
            
            execute_query(query, params)
            return True
        
        except Exception as e:
            st.error(f"Error updating template: {str(e)}")
            return False
    
    @staticmethod
    def increment_template_usage(template_id: int) -> bool:
        """Increment template usage count"""
        try:
            query = """
            UPDATE templates SET usage_count = usage_count + 1, updated_at = datetime('now')
            WHERE id = ?
            """
            execute_query(query, (template_id,))
            return True
        except Exception:
            return False

class AnalyticsQueries:
    """Database queries for analytics and reporting"""
    
    @staticmethod
    def log_user_activity(user_id: int, action_type: str, entity_type: str = None,
                         entity_id: int = None, metadata: str = None,
                         success: bool = True) -> bool:
        """Log user activity"""
        try:
            query = """
            INSERT INTO analytics (
                user_id, action_type, entity_type, entity_id, metadata,
                success, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """
            
            params = (user_id, action_type, entity_type, entity_id, metadata, success)
            execute_query(query, params)
            return True
        
        except Exception:
            return False
    
    @staticmethod
    def get_user_activity(user_id: int = None, days_back: int = 30,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Get user activity logs"""
        base_query = """
        SELECT a.*, u.full_name as user_name, u.user_type
        FROM analytics a
        JOIN users u ON a.user_id = u.id
        WHERE a.timestamp >= datetime('now', '-{} days')
        """.format(days_back)
        
        params = []
        
        if user_id:
            base_query += " AND a.user_id = ?"
            params.append(user_id)
        
        base_query += f" ORDER BY a.timestamp DESC LIMIT {limit}"
        
        return execute_query(base_query, params, fetch='all')
    
    @staticmethod
    def get_prescription_stats(doctor_id: int = None, days_back: int = 30) -> Dict[str, Any]:
        """Get prescription statistics"""
        date_filter = f"datetime('now', '-{days_back} days')"
        
        base_query = f"""
        SELECT 
            COUNT(*) as total_prescriptions,
            COUNT(CASE WHEN status = 'Active' THEN 1 END) as active_prescriptions,
            COUNT(CASE WHEN status = 'Completed' THEN 1 END) as completed_prescriptions,
            COUNT(DISTINCT patient_id) as unique_patients
        FROM prescriptions
        WHERE created_at >= {date_filter}
        """
        
        params = []
        if doctor_id:
            base_query += " AND doctor_id = ?"
            params.append(doctor_id)
        
        result = execute_query(base_query, params, fetch='one')
        return dict(result) if result else {}
    
    @staticmethod
    def get_patient_stats(created_by: int = None, days_back: int = 30) -> Dict[str, Any]:
        """Get patient statistics"""
        date_filter = f"datetime('now', '-{days_back} days')"
        
        base_query = f"""
        SELECT 
            COUNT(*) as total_patients,
            COUNT(CASE WHEN gender = 'Male' THEN 1 END) as male_patients,
            COUNT(CASE WHEN gender = 'Female' THEN 1 END) as female_patients,
            AVG((julianday('now') - julianday(date_of_birth))/365.25) as avg_age
        FROM patients
        WHERE created_at >= {date_filter} AND is_active = 1
        """
        
        params = []
        if created_by:
            base_query += " AND created_by = ?"
            params.append(created_by)
        
        result = execute_query(base_query, params, fetch='one')
        return dict(result) if result else {}

class DashboardQueries:
    """Database queries for dashboard data"""
    
    @staticmethod
    def get_today_summary() -> Dict[str, Any]:
        """Get today's summary data"""
        try:
            # Today's visits
            visits_query = "SELECT COUNT(*) as count FROM patient_visits WHERE visit_date = date('now')"
            visits_result = execute_query(visits_query, fetch='one')
            
            # Today's prescriptions
            prescriptions_query = "SELECT COUNT(*) as count FROM prescriptions WHERE date(created_at) = date('now')"
            prescriptions_result = execute_query(prescriptions_query, fetch='one')
            
            # Completed consultations today
            completed_query = """
            SELECT COUNT(*) as count FROM patient_visits 
            WHERE visit_date = date('now') AND consultation_completed = 1
            """
            completed_result = execute_query(completed_query, fetch='one')
            
            return {
                'todays_visits': visits_result['count'] if visits_result else 0,
                'todays_prescriptions': prescriptions_result['count'] if prescriptions_result else 0,
                'completed_consultations': completed_result['count'] if completed_result else 0
            }
        
        except Exception as e:
            st.error(f"Error getting today's summary: {str(e)}")
            return {}
    
    @staticmethod
    def get_recent_activity(user_id: int = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activity for dashboard"""
        base_query = """
        SELECT a.*, u.full_name as user_name
        FROM analytics a
        JOIN users u ON a.user_id = u.id
        WHERE a.timestamp >= datetime('now', '-7 days')
        """
        
        params = []
        if user_id:
            base_query += " AND a.user_id = ?"
            params.append(user_id)
        
        base_query += f" ORDER BY a.timestamp DESC LIMIT {limit}"
        
        return execute_query(base_query, params, fetch='all')
    
    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            # Database size
            from config.database import get_database_info
            db_info = get_database_info()
            
            # Error rate (last 24 hours)
            error_query = """
            SELECT 
                COUNT(CASE WHEN success = 0 THEN 1 END) as errors,
                COUNT(*) as total
            FROM analytics
            WHERE timestamp >= datetime('now', '-24 hours')
            """
            error_result = execute_query(error_query, fetch='one')
            
            error_rate = 0
            if error_result and error_result['total'] > 0:
                error_rate = (error_result['errors'] / error_result['total']) * 100
            
            # Active users (last 24 hours)
            active_users_query = """
            SELECT COUNT(DISTINCT user_id) as count
            FROM analytics
            WHERE timestamp >= datetime('now', '-24 hours')
            """
            active_users_result = execute_query(active_users_query, fetch='one')
            
            return {
                'database_size_mb': db_info.get('file_size_mb', 0),
                'error_rate': round(error_rate, 2),
                'active_users_24h': active_users_result['count'] if active_users_result else 0,
                'total_records': db_info.get('total_records', 0)
            }
        
        except Exception as e:
            st.error(f"Error getting system health: {str(e)}")
            return {}

# Convenience functions for common operations
def get_complete_prescription_data(prescription_id: int) -> Optional[Dict[str, Any]]:
    """Get complete prescription data for PDF generation"""
    prescription = PrescriptionQueries.get_prescription_details(prescription_id)
    if not prescription:
        return None
    
    # Format data for PDF
    from utils.helpers import calculate_age
    
    return {
        'prescription_id': prescription['prescription_id'],
        'created_at': prescription['created_at'],
        'status': prescription['status'],
        'diagnosis': prescription['diagnosis'],
        'chief_complaint': prescription.get('chief_complaint'),
        'notes': prescription.get('notes'),
        'follow_up_date': prescription.get('follow_up_date'),
        'follow_up_instructions': prescription.get('follow_up_instructions'),
        'doctor': {
            'id': prescription['doctor_id'],
            'full_name': prescription['doctor_name'],
            'medical_license': prescription['medical_license'],
            'specialization': prescription['specialization'],
            'email': prescription['doctor_email'],
            'phone': prescription['doctor_phone']
        },
        'patient': {
            'patient_id': prescription['patient_id'],
            'first_name': prescription['first_name'],
            'last_name': prescription['last_name'],
            'date_of_birth': prescription['date_of_birth'],
            'age': calculate_age(prescription['date_of_birth']),
            'gender': prescription['gender'],
            'phone': prescription['patient_phone'],
            'email': prescription['patient_email'],
            'address': prescription['address'],
            'allergies': prescription['allergies'],
            'medical_conditions': prescription['medical_conditions']
        },
        'medications': prescription['medications'],
        'lab_tests': prescription['lab_tests']
    }

def create_complete_prescription(prescription_data: Dict[str, Any],
                               medications: List[Dict[str, Any]],
                               lab_tests: List[Dict[str, Any]],
                               doctor_id: int) -> Optional[int]:
    """Create complete prescription with medications and lab tests"""
    try:
        # Create prescription
        prescription_id = PrescriptionQueries.create_prescription(prescription_data, doctor_id)
        if not prescription_id:
            return None
        
        # Add medications
        for medication in medications:
            if not PrescriptionQueries.add_prescription_medication(prescription_id, medication):
                st.warning(f"Failed to add medication: {medication.get('medication_name', 'Unknown')}")
        
        # Add lab tests
        for lab_test in lab_tests:
            if not PrescriptionQueries.add_prescription_lab_test(prescription_id, lab_test):
                st.warning(f"Failed to add lab test: {lab_test.get('test_name', 'Unknown')}")
        
        return prescription_id
    
    except Exception as e:
        st.error(f"Error creating complete prescription: {str(e)}")
        return None

def search_all_entities(search_term: str, entity_types: List[str] = None,
                       user_id: int = None, limit_per_type: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """Search across multiple entity types"""
    if not entity_types:
        entity_types = ['patients', 'medications', 'lab_tests', 'prescriptions']
    
    results = {}
    
    if 'patients' in entity_types:
        results['patients'] = PatientQueries.search_patients(search_term, limit=limit_per_type)
    
    if 'medications' in entity_types:
        results['medications'] = MedicationQueries.search_medications(search_term, limit=limit_per_type)
    
    if 'lab_tests' in entity_types:
        results['lab_tests'] = LabTestQueries.search_lab_tests(search_term, limit=limit_per_type)
    
    if 'prescriptions' in entity_types:
        results['prescriptions'] = PrescriptionQueries.search_prescriptions(
            search_term, doctor_id=user_id, limit=limit_per_type
        )
    
    return results

def get_entity_counts() -> Dict[str, int]:
    """Get counts of all main entities"""
    try:
        counts = {}
        
        # Users
        users_query = "SELECT COUNT(*) as count FROM users WHERE is_active = 1"
        users_result = execute_query(users_query, fetch='one')
        counts['users'] = users_result['count'] if users_result else 0
        
        # Patients
        patients_query = "SELECT COUNT(*) as count FROM patients WHERE is_active = 1"
        patients_result = execute_query(patients_query, fetch='one')
        counts['patients'] = patients_result['count'] if patients_result else 0
        
        # Prescriptions
        prescriptions_query = "SELECT COUNT(*) as count FROM prescriptions"
        prescriptions_result = execute_query(prescriptions_query, fetch='one')
        counts['prescriptions'] = prescriptions_result['count'] if prescriptions_result else 0
        
        # Medications
        medications_query = "SELECT COUNT(*) as count FROM medications WHERE is_active = 1"
        medications_result = execute_query(medications_query, fetch='one')
        counts['medications'] = medications_result['count'] if medications_result else 0
        
        # Lab Tests
        lab_tests_query = "SELECT COUNT(*) as count FROM lab_tests WHERE is_active = 1"
        lab_tests_result = execute_query(lab_tests_query, fetch='one')
        counts['lab_tests'] = lab_tests_result['count'] if lab_tests_result else 0
        
        # Templates
        templates_query = "SELECT COUNT(*) as count FROM templates WHERE is_active = 1"
        templates_result = execute_query(templates_query, fetch='one')
        counts['templates'] = templates_result['count'] if templates_result else 0
        
        return counts
    
    except Exception as e:
        st.error(f"Error getting entity counts: {str(e)}")
        return {}
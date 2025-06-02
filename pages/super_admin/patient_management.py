"""
MedScript Pro - Super Admin Patient Management
This page handles comprehensive patient management for super administrators including CRUD operations,
patient analytics, demographics, medical history, and visit history display.
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import streamlit as st
from config.settings import USER_ROLES, GENDER_OPTIONS
from config.styles import inject_css, inject_component_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access
from components.forms import PatientFormComponent, SearchFormComponent
from components.cards import PatientCard, MetricCard, AnalyticsCard, render_card_grid
from components.charts import PieChart, BarChart, TimeSeriesChart, DonutChart
from database.queries import PatientQueries, VisitQueries, PrescriptionQueries, AnalyticsQueries
from utils.formatters import (
    format_patient_name, format_date_display, format_phone_number,
    format_age_from_birth_date, format_medical_conditions, format_allergies,
    format_relative_date, get_time_ago
)
from utils.helpers import calculate_age
from services.analytics_service import log_analytics_event
import pandas as pd

def show_patient_management():
    """Display the patient management page"""
    # Authentication and permission checks
    require_authentication()
    require_role_access([USER_ROLES['SUPER_ADMIN']])
    
    # Inject CSS
    inject_css()
    inject_component_css('DASHBOARD_CARDS')
    inject_component_css('PATIENT_CARDS')
    
    # Page header
    st.markdown("""
        <div class="main-header">
            <h1>🏥 Patient Management</h1>
            <p>Comprehensive patient database management and analytics</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'selected_patient' not in st.session_state:
        st.session_state.selected_patient = None
    if 'show_create_form' not in st.session_state:
        st.session_state.show_create_form = False
    if 'show_edit_form' not in st.session_state:
        st.session_state.show_edit_form = False
    if 'show_patient_details' not in st.session_state:
        st.session_state.show_patient_details = False
    
    # Main content
    render_patient_management_content()

def render_patient_management_content():
    """Render the main patient management content"""
    try:
        # Create tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Patient List", "📊 Analytics", "👤 Patient Details", "🔍 Advanced Search"
        ])
        
        with tab1:
            render_patient_list_tab()
        
        with tab2:
            render_patient_analytics_tab()
        
        with tab3:
            render_patient_details_tab()
        
        with tab4:
            render_advanced_search_tab()
    
    except Exception as e:
        st.error(f"Error loading patient management: {str(e)}")

def render_patient_list_tab():
    """Render the patient list tab with CRUD operations"""
    # Action buttons
    col_actions = st.columns([1, 1, 1, 1, 3])
    
    with col_actions[0]:
        if st.button("➕ Add Patient", type="primary", use_container_width=True):
            st.session_state.show_create_form = True
            st.session_state.show_edit_form = False
            st.session_state.show_patient_details = False
            st.session_state.selected_patient = None
            st.rerun()
    
    with col_actions[1]:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.selected_patient = None
            st.session_state.show_create_form = False
            st.session_state.show_edit_form = False
            st.session_state.show_patient_details = False
            st.rerun()
    
    with col_actions[2]:
        if st.button("📊 Analytics", use_container_width=True):
            st.session_state.show_patient_details = False
            st.session_state.show_create_form = False
            st.session_state.show_edit_form = False
    
    with col_actions[3]:
        if st.button("📥 Export", use_container_width=True):
            export_patient_data()
    
    # Show appropriate content based on state
    if st.session_state.show_create_form:
        render_create_patient_form()
    elif st.session_state.show_edit_form and st.session_state.selected_patient:
        render_edit_patient_form()
    elif st.session_state.show_patient_details and st.session_state.selected_patient:
        render_patient_details_view()
    else:
        render_patient_search_and_list()

def render_patient_search_and_list():
    """Render patient search and list interface"""
    st.subheader("🏥 Patient Database")
    
    # Search and filters
    col_search, col_filter1, col_filter2 = st.columns([2, 1, 1])
    
    with col_search:
        search_term = st.text_input(
            "Search patients",
            placeholder="Search by name, ID, phone, or email...",
            label_visibility="collapsed"
        )
    
    with col_filter1:
        gender_filter = st.selectbox(
            "Filter by Gender",
            options=["All Genders"] + GENDER_OPTIONS,
            label_visibility="collapsed"
        )
    
    with col_filter2:
        age_filter = st.selectbox(
            "Filter by Age Group",
            options=["All Ages", "0-18", "19-35", "36-50", "51-65", "65+"],
            label_visibility="collapsed"
        )
    
    # Get patients with filters
    all_patients = PatientQueries.search_patients(search_term, limit=500)
    
    if not all_patients:
        st.warning("No patients found in the system")
        return
    
    # Apply filters
    filtered_patients = apply_patient_filters(all_patients, gender_filter, age_filter)
    
    # Patient statistics
    render_patient_statistics(all_patients, filtered_patients)
    
    # Patients display
    if filtered_patients:
        render_patients_display(filtered_patients)
    else:
        st.info("No patients match the current filters")

def apply_patient_filters(patients: List[Dict[str, Any]], gender_filter: str, age_filter: str) -> List[Dict[str, Any]]:
    """Apply filters to patient list"""
    filtered = patients
    
    # Apply gender filter
    if gender_filter != "All Genders":
        filtered = [p for p in filtered if p.get('gender') == gender_filter]
    
    # Apply age filter
    if age_filter != "All Ages":
        age_filtered = []
        for patient in filtered:
            age = calculate_age(patient.get('date_of_birth', ''))
            
            if age_filter == "0-18" and age <= 18:
                age_filtered.append(patient)
            elif age_filter == "19-35" and 19 <= age <= 35:
                age_filtered.append(patient)
            elif age_filter == "36-50" and 36 <= age <= 50:
                age_filtered.append(patient)
            elif age_filter == "51-65" and 51 <= age <= 65:
                age_filtered.append(patient)
            elif age_filter == "65+" and age > 65:
                age_filtered.append(patient)
        
        filtered = age_filtered
    
    return filtered

def render_patient_statistics(all_patients: List[Dict[str, Any]], filtered_patients: List[Dict[str, Any]]):
    """Render patient statistics"""
    st.markdown("### 📊 Patient Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_patients = len(all_patients)
        filtered_count = len(filtered_patients)
        st.metric(
            label="Total Patients",
            value=total_patients,
            delta=f"Showing {filtered_count}" if filtered_count != total_patients else None
        )
    
    with col2:
        male_patients = len([p for p in all_patients if p.get('gender') == 'Male'])
        st.metric(
            label="Male Patients",
            value=male_patients,
            delta=f"{(male_patients/total_patients*100):.1f}%" if total_patients > 0 else "0%"
        )
    
    with col3:
        female_patients = len([p for p in all_patients if p.get('gender') == 'Female'])
        st.metric(
            label="Female Patients",
            value=female_patients,
            delta=f"{(female_patients/total_patients*100):.1f}%" if total_patients > 0 else "0%"
        )
    
    with col4:
        # Calculate average age
        ages = []
        for patient in all_patients:
            age = calculate_age(patient.get('date_of_birth', ''))
            if age > 0:
                ages.append(age)
        
        avg_age = sum(ages) // len(ages) if ages else 0
        st.metric(
            label="Average Age",
            value=f"{avg_age} years"
        )
    
    # Recent registrations
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        # Patients registered in last 30 days
        thirty_days_ago = (datetime.now() - timedelta(days=30)).date()
        recent_patients = len([
            p for p in all_patients 
            if p.get('created_at') and 
            datetime.fromisoformat(p['created_at'].replace('Z', '+00:00')).date() >= thirty_days_ago
        ])
        st.metric(
            label="New (30 days)",
            value=recent_patients
        )
    
    with col6:
        # Patients with allergies
        allergy_patients = len([
            p for p in all_patients 
            if p.get('allergies') and p['allergies'].lower() not in ['none', 'none known', 'nka']
        ])
        st.metric(
            label="With Allergies",
            value=allergy_patients
        )
    
    with col7:
        # Patients with chronic conditions
        condition_patients = len([
            p for p in all_patients 
            if p.get('medical_conditions') and p['medical_conditions'].lower() != 'none'
        ])
        st.metric(
            label="With Conditions",
            value=condition_patients
        )
    
    with col8:
        # Emergency contacts available
        emergency_contacts = len([
            p for p in all_patients 
            if p.get('emergency_contact') and p.get('emergency_phone')
        ])
        st.metric(
            label="Emergency Contacts",
            value=emergency_contacts
        )

def render_patients_display(patients: List[Dict[str, Any]]):
    """Render patients in a list format"""
    st.markdown("### 👥 Patient List")
    
    # View toggle
    view_mode = st.radio(
        "View Mode",
        options=["Table", "Cards"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if view_mode == "Table":
        render_patients_table(patients)
    else:
        render_patients_cards(patients)

def render_patients_table(patients: List[Dict[str, Any]]):
    """Render patients as a data table"""
    # Prepare table data
    table_data = []
    for patient in patients:
        age = calculate_age(patient.get('date_of_birth', ''))
        name = format_patient_name(patient.get('first_name', ''), patient.get('last_name', ''))
        phone = format_phone_number(patient.get('phone', '')) if patient.get('phone') else 'N/A'
        
        # Format medical info
        allergies = patient.get('allergies', 'None known')
        if allergies.lower() in ['none', 'none known', 'nka']:
            allergies = 'None known'
        else:
            allergies = allergies[:30] + "..." if len(allergies) > 30 else allergies
        
        conditions = patient.get('medical_conditions', 'None')
        if conditions.lower() == 'none':
            conditions = 'None'
        else:
            conditions = conditions[:30] + "..." if len(conditions) > 30 else conditions
        
        # Registration date
        created_at = patient.get('created_at', '')
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                reg_date = format_relative_date(created_date)
            except:
                reg_date = created_at[:10]
        else:
            reg_date = 'Unknown'
        
        table_data.append({
            "Patient ID": patient.get('patient_id', 'Unknown'),
            "Name": name,
            "Age": f"{age} years",
            "Gender": patient.get('gender', 'Unknown'),
            "Phone": phone,
            "Allergies": allergies,
            "Conditions": conditions,
            "Registered": reg_date,
            "ID": patient.get('id', 0)  # Hidden ID for actions
        })
    
    if table_data:
        # Display table
        df = pd.DataFrame(table_data)
        
        # Configure table display
        st.dataframe(
            df.drop('ID', axis=1),  # Hide ID column
            use_container_width=True,
            hide_index=True
        )
        
        # Action buttons below table
        st.markdown("### 🔧 Patient Actions")
        
        selected_patient_id = st.selectbox(
            "Select patient for actions",
            options=[patient.get('id') for patient in patients],
            format_func=lambda x: next(
                (format_patient_name(p.get('first_name', ''), p.get('last_name', '')) + 
                 f" (ID: {p.get('patient_id', 'Unknown')})"
                 for p in patients if p.get('id') == x), 
                'Unknown'
            ),
            label_visibility="collapsed"
        )
        
        if selected_patient_id:
            selected_patient = next((p for p in patients if p.get('id') == selected_patient_id), None)
            if selected_patient:
                col_view, col_edit, col_history = st.columns(3)
                
                with col_view:
                    if st.button("👁️ View Details", use_container_width=True):
                        view_patient_callback(selected_patient)
                
                with col_edit:
                    if st.button("✏️ Edit Patient", use_container_width=True):
                        edit_patient_callback(selected_patient)
                
                with col_history:
                    if st.button("📋 Visit History", use_container_width=True):
                        show_visit_history_callback(selected_patient)

def render_patients_cards(patients: List[Dict[str, Any]]):
    """Render patients as cards"""
    # Action callbacks for patient cards
    action_callbacks = {
        "👁️ View": lambda patient: view_patient_callback(patient),
        "✏️ Edit": lambda patient: edit_patient_callback(patient),
        "📋 History": lambda patient: show_visit_history_callback(patient)
    }
    
    # Render cards in groups of 2
    for i in range(0, len(patients), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(patients):
                patient = patients[i + j]
                with col:
                    card = PatientCard(
                        patient_data=patient,
                        action_callbacks=action_callbacks
                    )
                    card.render()
                    st.divider()

def render_create_patient_form():
    """Render the create patient form"""
    st.subheader("➕ Register New Patient")
    
    # Cancel button
    if st.button("← Back to Patient List"):
        st.session_state.show_create_form = False
        st.rerun()
    
    # Patient form
    patient_form = PatientFormComponent(edit_mode=False)
    form_result = patient_form.render()
    
    if form_result:
        if form_result.get('cancelled'):
            st.session_state.show_create_form = False
            st.rerun()
        else:
            # Create patient
            current_user = get_current_user()
            create_result = create_new_patient(form_result, current_user['id'])
            if create_result:
                st.success("✅ Patient registered successfully!")
                log_analytics_event('create_patient', 'patient', create_result)
                st.session_state.show_create_form = False
                st.rerun()

def render_edit_patient_form():
    """Render the edit patient form"""
    patient = st.session_state.selected_patient
    if not patient:
        st.error("No patient selected for editing")
        return
    
    st.subheader(f"✏️ Edit Patient: {format_patient_name(patient.get('first_name', ''), patient.get('last_name', ''))}")
    
    # Cancel button
    if st.button("← Back to Patient List"):
        st.session_state.show_edit_form = False
        st.session_state.selected_patient = None
        st.rerun()
    
    # Patient form with existing data
    patient_form = PatientFormComponent(edit_mode=True, patient_data=patient)
    form_result = patient_form.render()
    
    if form_result:
        if form_result.get('cancelled'):
            st.session_state.show_edit_form = False
            st.session_state.selected_patient = None
            st.rerun()
        else:
            # Update patient
            update_result = update_existing_patient(patient.get('id'), form_result)
            if update_result:
                st.success("✅ Patient updated successfully!")
                log_analytics_event('update_patient', 'patient', patient.get('id'))
                st.session_state.show_edit_form = False
                st.session_state.selected_patient = None
                st.rerun()

def render_patient_details_view():
    """Render detailed patient information view"""
    patient = st.session_state.selected_patient
    if not patient:
        st.error("No patient selected")
        return
    
    # Header
    patient_name = format_patient_name(patient.get('first_name', ''), patient.get('last_name', ''))
    st.subheader(f"👤 Patient Details: {patient_name}")
    
    # Back button
    if st.button("← Back to Patient List"):
        st.session_state.show_patient_details = False
        st.session_state.selected_patient = None
        st.rerun()
    
    # Patient information tabs
    detail_tab1, detail_tab2, detail_tab3, detail_tab4 = st.tabs([
        "📋 Basic Info", "🏥 Medical Info", "📅 Visit History", "📝 Prescriptions"
    ])
    
    with detail_tab1:
        render_patient_basic_info(patient)
    
    with detail_tab2:
        render_patient_medical_info(patient)
    
    with detail_tab3:
        render_patient_visit_history(patient)
    
    with detail_tab4:
        render_patient_prescriptions(patient)

def render_patient_basic_info(patient: Dict[str, Any]):
    """Render patient basic information"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**👤 Personal Information**")
        st.write(f"**Patient ID:** {patient.get('patient_id', 'Unknown')}")
        st.write(f"**Full Name:** {format_patient_name(patient.get('first_name', ''), patient.get('last_name', ''))}")
        
        # Age and birth date
        if patient.get('date_of_birth'):
            age = calculate_age(patient['date_of_birth'])
            birth_date = format_date_display(patient['date_of_birth'])
            st.write(f"**Age:** {age} years old")
            st.write(f"**Date of Birth:** {birth_date}")
        
        st.write(f"**Gender:** {patient.get('gender', 'Unknown')}")
        
        # Physical measurements
        if patient.get('weight'):
            st.write(f"**Weight:** {patient['weight']} kg")
        if patient.get('height'):
            st.write(f"**Height:** {patient['height']} cm")
        if patient.get('blood_group'):
            st.write(f"**Blood Group:** {patient['blood_group']}")
    
    with col2:
        st.markdown("**📞 Contact Information**")
        if patient.get('phone'):
            st.write(f"**Phone:** {format_phone_number(patient['phone'])}")
        if patient.get('email'):
            st.write(f"**Email:** {patient['email']}")
        if patient.get('address'):
            st.write(f"**Address:** {patient['address']}")
        
        st.markdown("**🚨 Emergency Contact**")
        if patient.get('emergency_contact'):
            st.write(f"**Name:** {patient['emergency_contact']}")
        if patient.get('emergency_phone'):
            st.write(f"**Phone:** {format_phone_number(patient['emergency_phone'])}")
        
        if patient.get('insurance_info'):
            st.markdown("**🏥 Insurance**")
            st.write(patient['insurance_info'])
    
    # Registration information
    st.markdown("**📅 Registration Information**")
    col3, col4 = st.columns(2)
    
    with col3:
        if patient.get('created_at'):
            created_date = datetime.fromisoformat(patient['created_at'].replace('Z', '+00:00'))
            st.write(f"**Registered:** {format_date_display(created_date.date())} ({get_time_ago(created_date)})")
        
        if patient.get('created_by_name'):
            st.write(f"**Registered by:** {patient['created_by_name']}")
    
    with col4:
        if patient.get('updated_at'):
            updated_date = datetime.fromisoformat(patient['updated_at'].replace('Z', '+00:00'))
            st.write(f"**Last Updated:** {get_time_ago(updated_date)}")
    
    # Additional notes
    if patient.get('notes'):
        st.markdown("**📝 Additional Notes**")
        st.write(patient['notes'])

def render_patient_medical_info(patient: Dict[str, Any]):
    """Render patient medical information"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**⚠️ Allergies**")
        allergies = patient.get('allergies', 'None known')
        if allergies.lower() in ['none', 'none known', 'nka']:
            st.info("✅ No known allergies")
        else:
            st.error(f"⚠️ {format_allergies(allergies)}")
        
        st.markdown("**🏥 Medical Conditions**")
        conditions = patient.get('medical_conditions', 'None')
        if conditions.lower() == 'none':
            st.info("✅ No reported medical conditions")
        else:
            st.warning(f"📋 {format_medical_conditions(conditions)}")
    
    with col2:
        st.markdown("**📊 Health Metrics**")
        
        # BMI calculation if height and weight available
        if patient.get('height') and patient.get('weight'):
            height_m = float(patient['height']) / 100  # Convert cm to m
            weight_kg = float(patient['weight'])
            bmi = weight_kg / (height_m ** 2)
            
            bmi_category = "Unknown"
            if bmi < 18.5:
                bmi_category = "Underweight"
            elif bmi < 25:
                bmi_category = "Normal weight"
            elif bmi < 30:
                bmi_category = "Overweight"
            else:
                bmi_category = "Obese"
            
            st.metric("BMI", f"{bmi:.1f}", f"{bmi_category}")
        
        # Age category
        if patient.get('date_of_birth'):
            age = calculate_age(patient['date_of_birth'])
            age_category = "Unknown"
            if age < 18:
                age_category = "Pediatric"
            elif age < 65:
                age_category = "Adult"
            else:
                age_category = "Senior"
            
            st.metric("Age Category", age_category)

def render_patient_visit_history(patient: Dict[str, Any]):
    """Render patient visit history"""
    patient_id = patient.get('id')
    if not patient_id:
        st.error("Patient ID not available")
        return
    
    # Get visit history
    visits = VisitQueries.get_patient_visits(patient_id, limit=50)
    
    if not visits:
        st.info("No visit history found for this patient")
        return
    
    st.markdown(f"**📅 Visit History ({len(visits)} visits)**")
    
    # Visit statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_visits = len(visits)
        st.metric("Total Visits", total_visits)
    
    with col2:
        recent_visits = len([v for v in visits if 
                           datetime.fromisoformat(v['created_at'].replace('Z', '+00:00')).date() >= 
                           (datetime.now() - timedelta(days=30)).date()])
        st.metric("Recent (30 days)", recent_visits)
    
    with col3:
        completed_visits = len([v for v in visits if v.get('consultation_completed')])
        st.metric("Completed", completed_visits)
    
    with col4:
        emergency_visits = len([v for v in visits if v.get('visit_type') == 'Emergency'])
        st.metric("Emergency", emergency_visits)
    
    # Visit list
    for visit in visits[:10]:  # Show last 10 visits
        with st.expander(f"📅 {visit.get('visit_type', 'Visit')} - {format_date_display(visit.get('visit_date', ''))}"):
            col_visit1, col_visit2 = st.columns(2)
            
            with col_visit1:
                st.write(f"**Date:** {format_date_display(visit.get('visit_date', ''))}")
                if visit.get('visit_time'):
                    st.write(f"**Time:** {visit['visit_time']}")
                st.write(f"**Type:** {visit.get('visit_type', 'Unknown')}")
                if visit.get('is_followup'):
                    st.write("**Follow-up:** Yes")
                st.write(f"**Status:** {'✅ Completed' if visit.get('consultation_completed') else '⏳ Pending'}")
            
            with col_visit2:
                if visit.get('current_problems'):
                    st.write(f"**Problems:** {visit['current_problems']}")
                
                # Vital signs
                vital_signs = []
                if visit.get('blood_pressure'):
                    vital_signs.append(f"BP: {visit['blood_pressure']}")
                if visit.get('temperature'):
                    vital_signs.append(f"Temp: {visit['temperature']}°F")
                if visit.get('pulse_rate'):
                    vital_signs.append(f"HR: {visit['pulse_rate']}")
                
                if vital_signs:
                    st.write(f"**Vitals:** {' | '.join(vital_signs)}")
            
            if visit.get('notes'):
                st.write(f"**Notes:** {visit['notes']}")

def render_patient_prescriptions(patient: Dict[str, Any]):
    """Render patient prescriptions"""
    patient_id = patient.get('id')
    if not patient_id:
        st.error("Patient ID not available")
        return
    
    # Get prescriptions for this patient
    prescriptions = PrescriptionQueries.search_prescriptions(limit=100)
    patient_prescriptions = [p for p in prescriptions if p.get('patient_id') == patient_id]
    
    if not patient_prescriptions:
        st.info("No prescriptions found for this patient")
        return
    
    st.markdown(f"**📝 Prescriptions ({len(patient_prescriptions)})**")
    
    # Prescription statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_prescriptions = len(patient_prescriptions)
        st.metric("Total Prescriptions", total_prescriptions)
    
    with col2:
        active_prescriptions = len([p for p in patient_prescriptions if p.get('status') == 'Active'])
        st.metric("Active", active_prescriptions)
    
    with col3:
        completed_prescriptions = len([p for p in patient_prescriptions if p.get('status') == 'Completed'])
        st.metric("Completed", completed_prescriptions)
    
    with col4:
        recent_prescriptions = len([p for p in patient_prescriptions if 
                                  datetime.fromisoformat(p['created_at'].replace('Z', '+00:00')).date() >= 
                                  (datetime.now() - timedelta(days=30)).date()])
        st.metric("Recent (30 days)", recent_prescriptions)
    
    # Prescription list
    for prescription in patient_prescriptions[:10]:  # Show last 10 prescriptions
        with st.expander(f"📝 {prescription.get('prescription_id', 'Unknown')} - {format_date_display(prescription.get('created_at', ''))}"):
            col_rx1, col_rx2 = st.columns(2)
            
            with col_rx1:
                st.write(f"**Prescription ID:** {prescription.get('prescription_id', 'Unknown')}")
                st.write(f"**Date:** {format_date_display(prescription.get('created_at', ''))}")
                st.write(f"**Doctor:** {prescription.get('doctor_name', 'Unknown')}")
                st.write(f"**Status:** {prescription.get('status', 'Unknown')}")
            
            with col_rx2:
                if prescription.get('diagnosis'):
                    st.write(f"**Diagnosis:** {prescription['diagnosis']}")
                
                # Get prescription details for medication/lab test counts
                prescription_details = PrescriptionQueries.get_prescription_details(prescription.get('id'))
                if prescription_details:
                    med_count = len(prescription_details.get('medications', []))
                    lab_count = len(prescription_details.get('lab_tests', []))
                    st.write(f"**Medications:** {med_count}")
                    st.write(f"**Lab Tests:** {lab_count}")

def render_patient_analytics_tab():
    """Render patient analytics and demographics"""
    st.subheader("📊 Patient Analytics & Demographics")
    
    # Get all patients for analytics
    all_patients = PatientQueries.search_patients(limit=1000)
    
    if not all_patients:
        st.warning("No patient data available for analytics")
        return
    
    # Time range selector
    col_time1, col_time2 = st.columns([1, 3])
    
    with col_time1:
        time_range = st.selectbox(
            "Analytics Period",
            options=[30, 60, 90, 180, 365],
            index=2,
            format_func=lambda x: f"Last {x} days"
        )
    
    # Filter patients by time range
    cutoff_date = (datetime.now() - timedelta(days=time_range)).date()
    recent_patients = [
        p for p in all_patients 
        if p.get('created_at') and 
        datetime.fromisoformat(p['created_at'].replace('Z', '+00:00')).date() >= cutoff_date
    ]
    
    # Analytics sections
    render_demographic_analytics(all_patients, recent_patients)
    render_registration_trends(all_patients, time_range)
    render_medical_analytics(all_patients)

def render_demographic_analytics(all_patients: List[Dict[str, Any]], recent_patients: List[Dict[str, Any]]):
    """Render demographic analytics charts"""
    st.markdown("### 👥 Demographic Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gender distribution
        gender_counts = {}
        for patient in all_patients:
            gender = patient.get('gender', 'Unknown')
            gender_counts[gender] = gender_counts.get(gender, 0) + 1
        
        if gender_counts:
            chart_data = [{'gender': k, 'count': v} for k, v in gender_counts.items()]
            chart = PieChart(
                data=chart_data,
                labels_field='gender',
                values_field='count',
                title='Patient Distribution by Gender'
            )
            chart.render()
    
    with col2:
        # Age distribution
        age_groups = {'0-18': 0, '19-35': 0, '36-50': 0, '51-65': 0, '65+': 0}
        
        for patient in all_patients:
            age = calculate_age(patient.get('date_of_birth', ''))
            if age <= 18:
                age_groups['0-18'] += 1
            elif age <= 35:
                age_groups['19-35'] += 1
            elif age <= 50:
                age_groups['36-50'] += 1
            elif age <= 65:
                age_groups['51-65'] += 1
            else:
                age_groups['65+'] += 1
        
        chart_data = [{'age_group': k, 'count': v} for k, v in age_groups.items()]
        chart = BarChart(
            data=chart_data,
            x_field='age_group',
            y_field='count',
            title='Patient Distribution by Age Group'
        )
        chart.render()

def render_registration_trends(all_patients: List[Dict[str, Any]], time_range: int):
    """Render patient registration trends"""
    st.markdown("### 📈 Registration Trends")
    
    # Group patients by registration date
    from collections import defaultdict
    daily_registrations = defaultdict(int)
    
    cutoff_date = (datetime.now() - timedelta(days=time_range)).date()
    
    for patient in all_patients:
        if patient.get('created_at'):
            try:
                reg_date = datetime.fromisoformat(patient['created_at'].replace('Z', '+00:00')).date()
                if reg_date >= cutoff_date:
                    daily_registrations[reg_date.strftime('%Y-%m-%d')] += 1
            except:
                continue
    
    if daily_registrations:
        chart_data = [
            {'date': date_str, 'registrations': count}
            for date_str, count in sorted(daily_registrations.items())
        ]
        
        chart = TimeSeriesChart(
            data=chart_data,
            x_field='date',
            y_field='registrations',
            title=f'Patient Registrations - Last {time_range} Days'
        )
        chart.render()
    else:
        st.info("No registrations found in the selected time period")

def render_medical_analytics(all_patients: List[Dict[str, Any]]):
    """Render medical information analytics"""
    st.markdown("### 🏥 Medical Information Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Most common allergies
        st.markdown("**Most Common Allergies**")
        allergy_counts = defaultdict(int)
        
        for patient in all_patients:
            allergies = patient.get('allergies', '')
            if allergies and allergies.lower() not in ['none', 'none known', 'nka']:
                # Split and count individual allergies
                allergy_list = [a.strip().title() for a in allergies.split(',')]
                for allergy in allergy_list:
                    if allergy:
                        allergy_counts[allergy] += 1
        
        if allergy_counts:
            # Show top 10 allergies
            sorted_allergies = sorted(allergy_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            for i, (allergy, count) in enumerate(sorted_allergies, 1):
                st.write(f"{i}. {allergy}: {count} patients")
        else:
            st.info("No allergy data available")
    
    with col2:
        # Most common medical conditions
        st.markdown("**Most Common Medical Conditions**")
        condition_counts = defaultdict(int)
        
        for patient in all_patients:
            conditions = patient.get('medical_conditions', '')
            if conditions and conditions.lower() != 'none':
                # Split and count individual conditions
                condition_list = [c.strip().title() for c in conditions.split(',')]
                for condition in condition_list:
                    if condition:
                        condition_counts[condition] += 1
        
        if condition_counts:
            # Show top 10 conditions
            sorted_conditions = sorted(condition_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            for i, (condition, count) in enumerate(sorted_conditions, 1):
                st.write(f"{i}. {condition}: {count} patients")
        else:
            st.info("No medical condition data available")

def render_advanced_search_tab():
    """Render advanced search interface"""
    st.subheader("🔍 Advanced Patient Search")
    
    with st.form("advanced_search_form"):
        # Search criteria
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name_search = st.text_input("Patient Name", placeholder="First or last name")
            patient_id_search = st.text_input("Patient ID", placeholder="PT-YYYYMMDD-XXXXXX")
            phone_search = st.text_input("Phone Number", placeholder="Phone number")
        
        with col2:
            gender_search = st.selectbox("Gender", options=["Any"] + GENDER_OPTIONS)
            age_min = st.number_input("Minimum Age", min_value=0, max_value=150, value=0)
            age_max = st.number_input("Maximum Age", min_value=0, max_value=150, value=150)
        
        with col3:
            allergy_search = st.text_input("Has Allergy", placeholder="Allergy name")
            condition_search = st.text_input("Has Condition", placeholder="Medical condition")
            
            # Date range
            st.markdown("**Registration Date Range**")
            date_from = st.date_input("From", value=date.today() - timedelta(days=365))
            date_to = st.date_input("To", value=date.today())
        
        # Submit search
        search_submitted = st.form_submit_button("🔍 Search Patients", type="primary")
    
    if search_submitted:
        # Perform advanced search
        search_results = perform_advanced_patient_search({
            'name': name_search,
            'patient_id': patient_id_search,
            'phone': phone_search,
            'gender': gender_search if gender_search != "Any" else None,
            'age_min': age_min,
            'age_max': age_max,
            'allergy': allergy_search,
            'condition': condition_search,
            'date_from': date_from,
            'date_to': date_to
        })
        
        if search_results:
            st.success(f"Found {len(search_results)} patient(s) matching your criteria")
            render_patients_display(search_results)
        else:
            st.info("No patients found matching your search criteria")

def perform_advanced_patient_search(criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Perform advanced patient search with multiple criteria"""
    # Start with all patients
    all_patients = PatientQueries.search_patients(limit=1000)
    results = all_patients
    
    # Apply name filter
    if criteria.get('name'):
        name_lower = criteria['name'].lower()
        results = [
            p for p in results
            if (name_lower in p.get('first_name', '').lower() or 
                name_lower in p.get('last_name', '').lower())
        ]
    
    # Apply patient ID filter
    if criteria.get('patient_id'):
        patient_id_lower = criteria['patient_id'].lower()
        results = [
            p for p in results
            if patient_id_lower in p.get('patient_id', '').lower()
        ]
    
    # Apply phone filter
    if criteria.get('phone'):
        phone_digits = ''.join(filter(str.isdigit, criteria['phone']))
        results = [
            p for p in results
            if phone_digits in ''.join(filter(str.isdigit, p.get('phone', '')))
        ]
    
    # Apply gender filter
    if criteria.get('gender'):
        results = [p for p in results if p.get('gender') == criteria['gender']]
    
    # Apply age range filter
    if criteria.get('age_min') or criteria.get('age_max'):
        age_filtered = []
        for patient in results:
            age = calculate_age(patient.get('date_of_birth', ''))
            if (criteria.get('age_min', 0) <= age <= criteria.get('age_max', 150)):
                age_filtered.append(patient)
        results = age_filtered
    
    # Apply allergy filter
    if criteria.get('allergy'):
        allergy_lower = criteria['allergy'].lower()
        results = [
            p for p in results
            if allergy_lower in p.get('allergies', '').lower()
        ]
    
    # Apply condition filter
    if criteria.get('condition'):
        condition_lower = criteria['condition'].lower()
        results = [
            p for p in results
            if condition_lower in p.get('medical_conditions', '').lower()
        ]
    
    # Apply date range filter
    if criteria.get('date_from') or criteria.get('date_to'):
        date_filtered = []
        for patient in results:
            if patient.get('created_at'):
                try:
                    reg_date = datetime.fromisoformat(patient['created_at'].replace('Z', '+00:00')).date()
                    if (criteria.get('date_from', date.min) <= reg_date <= criteria.get('date_to', date.max)):
                        date_filtered.append(patient)
                except:
                    continue
        results = date_filtered
    
    return results

def create_new_patient(patient_data: Dict[str, Any], created_by: int) -> Optional[int]:
    """Create a new patient"""
    try:
        patient_id = PatientQueries.create_patient(patient_data, created_by)
        
        if patient_id:
            return patient_id
        else:
            st.error("Failed to create patient. Please try again.")
            return None
    
    except Exception as e:
        st.error(f"Error creating patient: {str(e)}")
        return None

def update_existing_patient(patient_id: int, patient_data: Dict[str, Any]) -> bool:
    """Update an existing patient"""
    try:
        success = PatientQueries.update_patient(patient_id, patient_data)
        
        if not success:
            st.error("Failed to update patient. Please try again.")
        
        return success
    
    except Exception as e:
        st.error(f"Error updating patient: {str(e)}")
        return False

def export_patient_data():
    """Export patient data to CSV"""
    try:
        # Get all patients
        all_patients = PatientQueries.search_patients(limit=1000)
        
        if not all_patients:
            st.warning("No patient data to export")
            return
        
        # Prepare export data
        export_data = []
        for patient in all_patients:
            age = calculate_age(patient.get('date_of_birth', ''))
            
            export_data.append({
                'Patient ID': patient.get('patient_id', ''),
                'First Name': patient.get('first_name', ''),
                'Last Name': patient.get('last_name', ''),
                'Date of Birth': patient.get('date_of_birth', ''),
                'Age': age,
                'Gender': patient.get('gender', ''),
                'Phone': patient.get('phone', ''),
                'Email': patient.get('email', ''),
                'Address': patient.get('address', ''),
                'Allergies': patient.get('allergies', ''),
                'Medical Conditions': patient.get('medical_conditions', ''),
                'Emergency Contact': patient.get('emergency_contact', ''),
                'Emergency Phone': patient.get('emergency_phone', ''),
                'Insurance Info': patient.get('insurance_info', ''),
                'Blood Group': patient.get('blood_group', ''),
                'Weight (kg)': patient.get('weight', ''),
                'Height (cm)': patient.get('height', ''),
                'Registration Date': patient.get('created_at', ''),
                'Registered By': patient.get('created_by_name', ''),
                'Notes': patient.get('notes', '')
            })
        
        # Create DataFrame and CSV
        df = pd.DataFrame(export_data)
        csv = df.to_csv(index=False)
        
        # Download button
        st.download_button(
            label="📥 Download Patient Data (CSV)",
            data=csv,
            file_name=f"patients_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        st.success(f"✅ Prepared export file with {len(export_data)} patients")
    
    except Exception as e:
        st.error(f"Error exporting patient data: {str(e)}")

# Callback functions
def view_patient_callback(patient: Dict[str, Any]):
    """Callback for view patient details"""
    st.session_state.selected_patient = patient
    st.session_state.show_patient_details = True
    st.session_state.show_create_form = False
    st.session_state.show_edit_form = False
    st.rerun()

def edit_patient_callback(patient: Dict[str, Any]):
    """Callback for edit patient action"""
    st.session_state.selected_patient = patient
    st.session_state.show_edit_form = True
    st.session_state.show_create_form = False
    st.session_state.show_patient_details = False
    st.rerun()

def show_visit_history_callback(patient: Dict[str, Any]):
    """Callback for showing visit history"""
    st.session_state.selected_patient = patient
    st.session_state.show_patient_details = True
    st.session_state.show_create_form = False
    st.session_state.show_edit_form = False
    st.rerun()

if __name__ == "__main__":
    show_patient_management()
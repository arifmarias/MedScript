import streamlit as st
from datetime import datetime, timedelta

# Config and Auth
from config.settings import USER_ROLES
from config.styles import inject_css #, inject_prescription_css (assuming this might be created later)
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access #, PermissionChecker, Permission (if specific checks are needed later)

# Components
from components.cards import PrescriptionCard # Assuming this component exists
from components.forms import SearchFormComponent, PrescriptionMedicationComponent, PrescriptionLabTestComponent # Assuming these exist

# Database Queries
from database.queries import (
    PatientQueries, 
    MedicationQueries, 
    LabTestQueries, 
    PrescriptionQueries
)

# Services
from services.ai_service import AIAnalysisService, is_ai_available # Assuming these exist
from services.pdf_service import generate_prescription_pdf, get_pdf_filename, create_download_link # Placeholder for future use

# Utils
from utils.helpers import show_error_message, show_success_message # Assuming these exist
from utils.formatters import format_patient_name

# --- Mock Data and Placeholders ---
def get_mock_patients(query: str):
    if not query: return []
    return [
        {'id': 'p001', 'first_name': 'John', 'last_name': 'Doe', 'dob': '1985-01-15', 'gender': 'Male', 'allergies': ['Peanuts'], 'conditions': ['Hypertension']},
        {'id': 'p002', 'first_name': 'Jane', 'last_name': 'Smith', 'dob': '1992-07-22', 'gender': 'Female', 'allergies': [], 'conditions': ['Asthma', 'Migraine']},
    ]

def get_mock_medications(query: str = ""):
    meds = [
        {'id': 'med001', 'name': 'Amoxicillin 250mg', 'category': 'Antibiotic'},
        {'id': 'med002', 'name': 'Paracetamol 500mg', 'category': 'Analgesic'},
        {'id': 'med003', 'name': 'Lisinopril 10mg', 'category': 'Antihypertensive'},
    ]
    if query:
        return [m for m in meds if query.lower() in m['name'].lower()]
    return meds

def get_mock_lab_tests(query: str = ""):
    tests = [
        {'id': 'lab001', 'name': 'Complete Blood Count (CBC)', 'category': 'Hematology'},
        {'id': 'lab002', 'name': 'Lipid Panel', 'category': 'Chemistry'},
        {'id': 'lab003', 'name': 'Urinalysis', 'category': 'Microbiology'},
    ]
    if query:
        return [t for t in tests if query.lower() in t['name'].lower()]
    return tests
    
def get_mock_prescriptions(query: str, doctor_id: str):
    # Simulate a query that might return prescriptions for a doctor
    # In a real scenario, PrescriptionQueries.search_prescriptions would handle filtering by doctor_id
    all_prescriptions = [
        {'prescription_id': 'rx001', 'patient_name': 'John Doe', 'patient_id': 'p001', 'date_issued': '2023-10-01', 'status': 'Active', 'doctor_id': 'docRxMaster', 'medications': [{'name': 'Amoxicillin 250mg'}], 'lab_tests': []},
        {'prescription_id': 'rx002', 'patient_name': 'Jane Smith', 'patient_id': 'p002', 'date_issued': '2023-09-15', 'status': 'Expired', 'doctor_id': 'docRxMaster', 'medications': [], 'lab_tests': [{'name': 'Lipid Panel'}]},
        {'prescription_id': 'rx003', 'patient_name': 'John Doe', 'patient_id': 'p001', 'date_issued': '2023-08-20', 'status': 'Completed', 'doctor_id': 'anotherDoc', 'medications': [{'name': 'Paracetamol 500mg'}], 'lab_tests': []},
    ]
    
    # Filter by doctor_id first
    doctor_prescriptions = [rx for rx in all_prescriptions if rx['doctor_id'] == doctor_id]

    if not query: # If no specific query, return all for the doctor
        return doctor_prescriptions
        
    # Simple text search in patient_name or prescription_id
    query_lower = query.lower()
    return [
        rx for rx in doctor_prescriptions 
        if query_lower in rx['patient_name'].lower() or query_lower in rx['prescription_id'].lower()
    ]


# --- Helper Functions (Placeholders) ---
def handle_ai_analysis(medications, patient_context):
    st.toast("🔬 AI Analysis triggered (placeholder). This may take a moment.")
    # Simulate AI processing
    # In reality, call AIAnalysisService.analyze_prescription(medications, patient_context)
    st.info("AI Analysis Complete: No critical interactions found (mock response).")

def handle_save_prescription(prescription_data, medications, lab_tests, doctor):
    patient_name = format_patient_name(st.session_state.selected_patient_for_rx.get('first_name','N/A'), st.session_state.selected_patient_for_rx.get('last_name',''))
    try:
        # Placeholder for actual save operation using PrescriptionQueries.create_prescription
        # Note: PrescriptionQueries.create_prescription needs to be implemented
        PrescriptionQueries.create_prescription(
            patient_id=st.session_state.selected_patient_for_rx['id'],
            doctor_id=doctor['id'],
            diagnosis=prescription_data['diagnosis'],
            chief_complaint=prescription_data['chief_complaint'],
            notes=prescription_data['general_notes'],
            medications=medications, # List of medication dicts
            lab_tests=lab_tests, # List of lab test dicts
            # visit_id=prescription_data.get('visit_id') # Optional
        )
        show_success_message(f"Prescription for {patient_name} saved successfully!")
        # Clear session state for form items
        st.session_state.rx_medications = []
        st.session_state.rx_lab_tests = []
        # st.session_state.selected_patient_for_rx = None # Optionally clear patient or keep for new Rx
        return True
    except AttributeError: # If PrescriptionQueries.create_prescription doesn't exist
        st.warning(f"Prescription for {patient_name} submitted (mock save). Actual database integration pending.")
        st.session_state.rx_medications = []
        st.session_state.rx_lab_tests = []
        return True # Simulate success for UI flow
    except Exception as e:
        show_error_message(f"Failed to save prescription for {patient_name}: {e}")
        return False


def handle_prescription_action(action: str, rx_data: dict):
    st.toast(f"{action} for Prescription ID: {rx_data.get('prescription_id', 'N/A')} (placeholder).")
    if action == "View PDF":
        # pdf_content = generate_prescription_pdf(rx_data) # Placeholder
        # filename = get_pdf_filename(rx_data) # Placeholder
        # create_download_link(pdf_content, filename, "Download PDF") # Placeholder
        st.info("PDF generation and download link would appear here.")


# --- Tab Rendering Functions ---
def render_create_prescription_tab(doctor: dict):
    st.subheader("⚕️ Create New Prescription")

    # 1. Patient Selection
    st.markdown("#### 1. Select Patient")
    
    try:
        patient_search_fn = PatientQueries.search_patients
    except AttributeError:
        st.warning("Patient search system initializing. Using mock patient data.", icon="⚠️")
        patient_search_fn = get_mock_patients

    patient_search_form = SearchFormComponent(
        search_function=patient_search_fn,
        result_key_prefix="patient_search_",
        form_key="patient_search_form",
        placeholder="Search patient by name or ID...",
        label="Find Patient"
    )
    selected_patient_id = patient_search_form.render() 

    if selected_patient_id and (not st.session_state.get('selected_patient_for_rx') or st.session_state.selected_patient_for_rx['id'] != selected_patient_id) :
        try:
            if patient_search_fn == get_mock_patients: # Using mock
                 all_mock_patients = get_mock_patients("any_query_to_get_all") # Helper to get all mocks
                 patient_data = next((p for p in all_mock_patients if p['id'] == selected_patient_id), None)
            else: # Using actual query
                patient_data = PatientQueries.get_patient_details(selected_patient_id)

            if patient_data:
                st.session_state.selected_patient_for_rx = patient_data
                st.session_state.rx_medications = []
                st.session_state.rx_lab_tests = []
            else:
                show_error_message("Selected patient not found.")
                st.session_state.selected_patient_for_rx = None
        except Exception as e:
            show_error_message(f"Error fetching patient details: {e}")
            st.session_state.selected_patient_for_rx = None
            # patient_search_form.clear_selection() # Consider how to reset SearchFormComponent

    if st.session_state.get('selected_patient_for_rx'):
        patient = st.session_state.selected_patient_for_rx
        patient_name = format_patient_name(patient['first_name'], patient['last_name'])
        st.success(f"Selected Patient: **{patient_name}** (ID: {patient['id']})")
        
        with st.expander("Patient Details", expanded=False):
            st.write(f"**DOB:** {patient.get('dob', 'N/A')}, **Gender:** {patient.get('gender', 'N/A')}")
            st.write(f"**Allergies:** {', '.join(patient.get('allergies', [])) if patient.get('allergies') else 'None reported'}")
            st.write(f"**Existing Conditions:** {', '.join(patient.get('conditions', [])) if patient.get('conditions') else 'None reported'}")
        
        if st.button("Clear Selected Patient", key="clear_patient_btn"):
            st.session_state.selected_patient_for_rx = None
            st.session_state.rx_medications = []
            st.session_state.rx_lab_tests = []
            # patient_search_form.clear_selection() # Needs a method in SearchFormComponent
            st.rerun()

        st.markdown("#### 2. Prescription Details")
        with st.form("create_prescription_form"):
            chief_complaint = st.text_input("Chief Complaint / Reason for Visit", key="rx_chief_complaint")
            diagnosis = st.text_area("Diagnosis / Clinical Impression", key="rx_diagnosis")
            
            st.markdown("##### Medications")
            try:
                available_meds = MedicationQueries.search_medications("")
            except AttributeError:
                available_meds = get_mock_medications()
            
            med_component = PrescriptionMedicationComponent(
                current_medications=st.session_state.get('rx_medications', []),
                available_medications=available_meds,
                key_prefix="rx_med"
            )
            st.session_state.rx_medications = med_component.render()

            st.markdown("##### Lab Tests")
            try:
                available_tests = LabTestQueries.search_lab_tests("")
            except AttributeError:
                available_tests = get_mock_lab_tests()

            test_component = PrescriptionLabTestComponent(
                current_lab_tests=st.session_state.get('rx_lab_tests', []),
                available_lab_tests=available_tests,
                key_prefix="rx_lab"
            )
            st.session_state.rx_lab_tests = test_component.render()
            
            general_notes = st.text_area("General Notes / Advice to Patient", key="rx_general_notes")
            
            # AI Analysis Button (Placeholder) - Placed outside main submit logic if it's not a primary action
            # This button is tricky inside st.form if it's not THE submit button.
            # For now, it will also act as a submit button for the form.
            # A better UX might involve a separate button that calls a function and updates state.
            ai_button_pressed = False
            if is_ai_available():
                 ai_button_pressed = st.form_submit_button("🔬 Analyze with AI (Beta)", use_container_width=False)

            submitted = st.form_submit_button("💾 Save Prescription", use_container_width=True)

            if ai_button_pressed and not submitted: # Prioritize AI analysis if its button was distinct and pressed
                 handle_ai_analysis(st.session_state.rx_medications, patient)
                 # Do not proceed with saving yet, allow user to review AI feedback. Rerun might be needed.
                 # st.rerun() # Could be too disruptive, depends on AI feedback display.

            if submitted:
                if not chief_complaint or not diagnosis:
                    show_error_message("Chief Complaint and Diagnosis are required.")
                elif not st.session_state.rx_medications and not st.session_state.rx_lab_tests:
                     show_error_message("At least one medication or lab test must be added.")
                else:
                    prescription_data = {
                        "chief_complaint": chief_complaint,
                        "diagnosis": diagnosis,
                        "general_notes": general_notes,
                    }
                    if handle_save_prescription(prescription_data, st.session_state.rx_medications, st.session_state.rx_lab_tests, doctor):
                        st.rerun() 
    else:
        st.info("Please search and select a patient to begin creating a prescription.")


def render_view_prescriptions_tab(doctor: dict):
    st.subheader("📋 View Existing Prescriptions")

    try:
        prescription_search_fn = lambda query: PrescriptionQueries.search_prescriptions(query, doctor_id=doctor['id'])
    except AttributeError:
        st.warning("Prescription search system initializing. Using mock prescription data.", icon="⚠️")
        prescription_search_fn = lambda query: get_mock_prescriptions(query, doctor['id'])
        
    # We need a way to trigger the search. A button or on query change.
    # For simplicity, use a text input and a button.
    search_query_prescriptions = st.text_input("Search by Patient Name, Rx ID...", key="rx_search_query_input")
    
    if st.button("Search Prescriptions", key="rx_search_btn") or search_query_prescriptions:
        try:
            prescriptions = prescription_search_fn(search_query_prescriptions)
        except Exception as e:
            show_error_message(f"Error searching prescriptions: {e}")
            prescriptions = []

        if not prescriptions:
            st.info(f"No prescriptions found matching '{search_query_prescriptions}'.")
        else:
            st.write(f"Found {len(prescriptions)} prescription(s):")
            for rx_idx, rx in enumerate(prescriptions):
                actions = {
                    "View PDF": lambda r=rx: handle_prescription_action("View PDF", r),
                    "Edit": lambda r=rx: handle_prescription_action("Edit", r),
                    # "Cancel": lambda r=rx: handle_prescription_action("Cancel", r), # Example
                }
                try:
                    # Ensure PrescriptionCard is robust enough or provide default values
                    PrescriptionCard(
                        prescription_data=rx, 
                        actions=actions, 
                        key=f"rx_card_{rx.get('prescription_id', rx_idx)}" # Ensure unique key
                    )
                except Exception as e:
                    st.error(f"Error rendering prescription card for {rx.get('prescription_id')}: {e}")
                    st.json(rx) 
    else:
        st.info("Enter search terms above and click 'Search Prescriptions' to find existing prescriptions for your patients.")


# --- Main Page Function ---
def show_prescriptions_page():
    require_authentication()
    require_role_access([USER_ROLES['DOCTOR']])
    
    # inject_prescription_css() # If specific CSS for this page exists
    inject_css() # Global CSS

    st.markdown("<h1>📝 Prescription Management</h1>", unsafe_allow_html=True)
    
    current_user = get_current_user()
    if not current_user:
        show_error_message("Unable to retrieve user information. Please log in again.")
        return

    # Initialize session state variables
    if 'selected_patient_for_rx' not in st.session_state:
        st.session_state.selected_patient_for_rx = None
    if 'rx_medications' not in st.session_state:
        st.session_state.rx_medications = []
    if 'rx_lab_tests' not in st.session_state:
        st.session_state.rx_lab_tests = []

    tab_titles = ["➕ Create New Prescription", "📄 View Prescriptions"]
    tab1, tab2 = st.tabs(tab_titles)

    with tab1:
        render_create_prescription_tab(current_user)
    
    with tab2:
        render_view_prescriptions_tab(current_user)

if __name__ == "__main__":
    # Mock session state for isolated testing
    if 'user' not in st.session_state:
        st.session_state.user = {
            'id': 'docRxMaster', 
            'username': 'dr_prescriber', 
            'role': USER_ROLES['DOCTOR'], 
            'full_name': 'Dr. Rx Master',
            'email': 'dr.rx@example.com'
        }
        st.session_state.authenticated = True
        st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)

    if 'selected_patient_for_rx' not in st.session_state:
        st.session_state.selected_patient_for_rx = None # Important for logic
    if 'rx_medications' not in st.session_state:
        st.session_state.rx_medications = []
    if 'rx_lab_tests' not in st.session_state:
        st.session_state.rx_lab_tests = []
    
    # show_prescriptions_page() # Called at module level now

# This call ensures Streamlit runs the page content when navigating
show_prescriptions_page()

import streamlit as st
from datetime import datetime, timedelta, date as py_date # aliasing to avoid conflict
import copy

# Config and Auth
from config.settings import USER_ROLES
from config.styles import inject_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access

# Components
try:
    from components.forms import VisitFormComponent, SearchFormComponent
    COMPONENTS_AVAILABLE = True
except ImportError:
    COMPONENTS_AVAILABLE = False
    # st.warning("VisitFormComponent or SearchFormComponent not found. Using mock implementations.", icon="⚠️") # Moved to __main__
    class SearchFormComponent: # Mock
        def __init__(self, search_function=None, result_key_prefix=None, form_key=None, placeholder="Search...", label="Search", session_state_key="default_search_term", auto_submit=False, button_text="Search"):
            self.placeholder, self.label, self.session_state_key = placeholder, label, session_state_key
        def render(self): 
            st.session_state[self.session_state_key] = st.text_input(self.label, value=st.session_state.get(self.session_state_key, ""), placeholder=self.placeholder, key=f"mock_search_vm_{self.session_state_key}_v3")
            return None 
        def get_search_query(self): return st.session_state.get(self.session_state_key, "")

    class VisitFormComponent: # Mock
        def __init__(self, patient_data, edit_mode=False, visit_data=None, key_prefix="visit_form"):
            self.patient_data = patient_data
            self.edit_mode = edit_mode
            self.visit_data = visit_data if visit_data else {}
            self.key_prefix = key_prefix
            # if not COMPONENTS_AVAILABLE: st.info("Using Mock VisitFormComponent.") # Moved to __main__

        def render(self):
            submitted_data = None
            with st.form(key=f"{self.key_prefix}_form_main_visit_v3"):
                form_data = {}
                st.markdown(f"**Patient:** {self.patient_data.get('first_name','N/A')} {self.patient_data.get('last_name','N/A')}")
                
                current_visit_date_str = self.visit_data.get('visit_date', datetime.now().strftime('%Y-%m-%d'))
                try:
                    current_visit_date = datetime.strptime(current_visit_date_str, '%Y-%m-%d').date()
                except ValueError: # Handle cases where date might be invalid format or None
                    current_visit_date = datetime.now().date()

                form_data['visit_date'] = st.date_input("Visit Date*", value=current_visit_date, key=f"{self.key_prefix}_vdate_v3", min_value=py_date(2000,1,1), max_value=py_date.today() + timedelta(days=365)) # Allow future dates for scheduling
                form_data['visit_type'] = st.selectbox("Visit Type*", options=["Check-up", "Follow-up", "New Complaint", "Vaccination", "Procedure", "Scheduled Consultation"], index=0, key=f"{self.key_prefix}_vtype_v3")
                form_data['doctor_assigned_id'] = st.text_input("Doctor Assigned (ID)", value=self.visit_data.get('doctor_assigned_id','doc1'), key=f"{self.key_prefix}_vdoc_v3") 
                form_data['notes'] = st.text_area("Visit Notes / Chief Complaint", value=self.visit_data.get('notes',''), key=f"{self.key_prefix}_vnotes_v3")
                
                # Vital Signs as a sub-dictionary
                vital_signs_data = self.visit_data.get('vital_signs',{})
                form_data['vital_signs'] = {
                    'bp': st.text_input("Blood Pressure (e.g. 120/80)", value=vital_signs_data.get('bp',''), key=f"{self.key_prefix}_vbp_v3"),
                    'temp_c': st.number_input("Temperature (°C)", value=float(vital_signs_data.get('temp_c',37.0)), step=0.1, format="%.1f", key=f"{self.key_prefix}_vtemp_v3"),
                    'pulse': st.number_input("Pulse (bpm)", value=int(vital_signs_data.get('pulse',0)), step=1, key=f"{self.key_prefix}_vpulse_v3"),
                    'weight_kg': st.number_input("Weight (kg)", value=float(vital_signs_data.get('weight_kg',0.0)), step=0.1, format="%.1f",key=f"{self.key_prefix}_vweight_v3")
                }

                submit_label = "Update Visit" if self.edit_mode else "Record Visit"
                col1, col2 = st.columns([3,1])
                if col1.form_submit_button(submit_label, use_container_width=True, type="primary"):
                    valid = True 
                    if not form_data.get('visit_date') or not form_data.get('visit_type'): valid = False; show_error_message("Visit Date and Type are required.")
                    if valid: submitted_data = {k: (v.isoformat() if isinstance(v, (py_date, datetime)) else v) for k,v in form_data.items()}
                if col2.form_submit_button("Cancel", type="secondary", use_container_width=True):
                    submitted_data = {"cancelled": True}
            return submitted_data

# Database Queries (with Mocks)
try:
    from database.queries import PatientQueries, VisitQueries
    DB_QUERIES_AVAILABLE = True
except ImportError:
    DB_QUERIES_AVAILABLE = False
    # st.warning("PatientQueries or VisitQueries not found. Using mock data stores.", icon="⚠️") # Moved to __main__
    MOCK_PATIENTS_VISIT_PAGE = [ 
        {'id': 'pat_001', 'first_name': 'John', 'last_name': 'Doe', 'dob': '1985-01-15', 'phone_number': '555-0101', 'created_by': 'assistant123'},
        {'id': 'pat_002', 'first_name': 'Jane', 'last_name': 'Smith', 'dob': '1992-07-22', 'phone_number': '555-0202', 'created_by': 'assistant456'},
        {'id': 'pat_003', 'first_name': 'Alice', 'last_name': 'Johnson', 'dob': '1990-05-20', 'phone_number': '555-0303', 'created_by': 'assistant123'},
    ]
    MOCK_VISITS_STORE = [
        {'id': 'visit_001', 'patient_id': 'pat_001', 'patient_name': 'John Doe', 'visit_date': (datetime.now() - timedelta(days=5)).isoformat()[:10], 'visit_type': 'Check-up', 'notes': 'Routine check', 'created_by': 'assistant123', 'doctor_assigned_id': 'doc1', 'vital_signs': {'bp': '120/80', 'temp_c': 37.0, 'pulse': 70, 'weight_kg': 75.0}},
        {'id': 'visit_002', 'patient_id': 'pat_002', 'patient_name': 'Jane Smith', 'visit_date': (datetime.now() - timedelta(days=2)).isoformat()[:10], 'visit_type': 'Follow-up', 'notes': 'Post-op review', 'created_by': 'assistant456', 'doctor_assigned_id': 'doc2', 'vital_signs': {'bp': '110/70', 'temp_c': 36.8, 'pulse': 65, 'weight_kg': 60.2}},
        {'id': 'visit_003', 'patient_id': 'pat_001', 'patient_name': 'John Doe', 'visit_date': datetime.now().isoformat()[:10], 'visit_type': 'New Complaint', 'notes': 'Sore throat', 'created_by': 'assistant123', 'doctor_assigned_id': 'doc1', 'vital_signs': {'bp': '125/85', 'temp_c': 37.5, 'pulse': 72, 'weight_kg': 75.5}},
    ]
    class PatientQueries: 
        @staticmethod
        def search_patients(search_term=None, patient_id=None, created_by=None): 
            results = copy.deepcopy(MOCK_PATIENTS_VISIT_PAGE)
            if patient_id: return [p for p in results if p['id'] == patient_id]
            if search_term:
                term = search_term.lower()
                results = [p for p in results if term in p['first_name'].lower() or term in p['last_name'].lower() or term in p.get('id','').lower()]
            return results # Not filtering by created_by for visit patient selection by default
        @staticmethod
        def get_patient_details(patient_id):
             return next((copy.deepcopy(p) for p in MOCK_PATIENTS_VISIT_PAGE if p['id'] == patient_id), None)

    class VisitQueries: 
        @staticmethod
        def search_visits(search_term=None, created_by=None, patient_id=None):
            results = copy.deepcopy(MOCK_VISITS_STORE)
            if patient_id: results = [v for v in results if v['patient_id'] == patient_id]
            if created_by: results = [v for v in results if v.get('created_by') == created_by] # Filter by who recorded the visit
            if search_term:
                term = search_term.lower()
                results = [v for v in results if term in v.get('patient_name','').lower() or term in v.get('notes','').lower() or term in v.get('id','').lower() or term in v.get('visit_type','').lower()]
            return sorted(results, key=lambda x: x['visit_date'], reverse=True) # Show recent first
        @staticmethod
        def get_visit_details(visit_id):
            return next((copy.deepcopy(v) for v in MOCK_VISITS_STORE if v['id'] == visit_id), None)
        @staticmethod
        def create_visit(data, recorded_by_id):
            new_id = f"visit_{len(MOCK_VISITS_STORE) + 1:03d}_{datetime.now().strftime('%S%f')}"
            patient_details = PatientQueries.get_patient_details(data['patient_id'])
            patient_name = f"{patient_details['first_name']} {patient_details['last_name']}" if patient_details else "N/A"
            new_visit = {'id': new_id, **data, 'recorded_by': recorded_by_id, 'created_at': datetime.now().isoformat(), 'patient_name': patient_name}
            MOCK_VISITS_STORE.append(new_visit)
            return new_visit
        @staticmethod
        def update_visit(visit_id, data, updated_by_id):
            for i, v_item in enumerate(MOCK_VISITS_STORE):
                if v_item['id'] == visit_id:
                    patient_id_for_name = data.get('patient_id', v_item['patient_id'])
                    patient_details_for_name = PatientQueries.get_patient_details(patient_id_for_name)
                    patient_name_for_update = f"{patient_details_for_name['first_name']} {patient_details_for_name['last_name']}" if patient_details_for_name else v_item.get('patient_name', "N/A")
                    MOCK_VISITS_STORE[i] = {**v_item, **data, 'updated_at': datetime.now().isoformat(), 'last_updated_by': updated_by_id, 'patient_name': patient_name_for_update}
                    return MOCK_VISITS_STORE[i]
            return None

# Utils
from utils.formatters import format_patient_name, format_date_display # Make sure these are robust
from utils.helpers import show_error_message, show_success_message, show_info_message

# --- Helper Functions for CRUD ---
def handle_create_visit(data, assistant_id):
    try:
        data['patient_id'] = st.session_state.selected_patient_for_visit['id']
        new_visit = VisitQueries.create_visit(data, recorded_by_id=assistant_id)
        if new_visit:
            show_success_message(f"Visit for {st.session_state.selected_patient_for_visit['first_name']} recorded (ID: {new_visit['id']}).")
            st.session_state.visit_form_data = {} 
            # st.session_state.selected_patient_for_visit = None # Keep patient selected for potential next visit for same patient or clear
            # st.session_state.active_visit_management_tab_key = "View & Manage Visits"; st.rerun()
        else: show_error_message("Failed to record visit.")
    except Exception as e: show_error_message(f"Error: {e}")

def handle_update_visit(visit_id, data, assistant_id):
    try:
        if 'patient_id' not in data and st.session_state.selected_patient_for_visit: data['patient_id'] = st.session_state.selected_patient_for_visit['id']
        updated_visit = VisitQueries.update_visit(visit_id, data, updated_by_id=assistant_id)
        if updated_visit:
            show_success_message(f"Visit ID {updated_visit['id']} updated.")
            st.session_state.editing_visit_id = None; st.session_state.visit_form_data = {}; st.session_state.selected_patient_for_visit = None
            st.session_state.active_visit_management_tab_key = "View & Manage Visits"; st.rerun()
        else: show_error_message("Failed to update visit.")
    except Exception as e: show_error_message(f"Error: {e}")

# --- Tab Rendering Functions ---
def render_view_manage_visits_tab(assistant: dict):
    st.subheader("Search Existing Visits")
    search_form_visits = SearchFormComponent(session_state_key="visit_search_term_main_v3", label="Search Visits (Patient Name, Notes, ID, Type):")
    search_form_visits.render()
    search_term_val = st.session_state.get("visit_search_term_main_v3", "")

    if st.button("🔍 Search Visits", key="search_visits_btn_main_v3"): perform_search = True
    else: perform_search = not search_term_val # Default: show visits by assistant if no term

    visits_data = []
    if perform_search or search_term_val:
        try: visits_data = VisitQueries.search_visits(search_term=search_term_val, created_by=assistant['id'])
        except Exception as e: show_error_message(f"Error: {e}")

    if not visits_data and (perform_search or search_term_val): st.info(f"No visits found for '{search_term_val}' that you recorded.")
    elif not visits_data and not search_term_val: st.info("You have not recorded any visits.")

    for v_item in visits_data:
        def edit_action(visit_data_item=v_item):
            st.session_state.editing_visit_id = visit_data_item['id']
            full_v_details = VisitQueries.get_visit_details(visit_data_item['id'])
            st.session_state.visit_form_data = full_v_details if full_v_details else visit_data_item
            pat_details = PatientQueries.get_patient_details(visit_data_item['patient_id'])
            st.session_state.selected_patient_for_visit = pat_details
            st.session_state.active_visit_management_tab_key = "Record / Edit Visit" 
            st.rerun()

        # Simple display for now, a VisitCard component would be better.
        st.markdown(f"""
        **Patient:** {v_item.get('patient_name', 'N/A')} (ID: {v_item.get('patient_id', 'N/A')})
        **Date:** {format_date_display(v_item.get('visit_date'))} | **Type:** {v_item.get('visit_type', 'N/A')}
        **Doctor:** {v_item.get('doctor_assigned_id', 'N/A')}
        **Notes:** {v_item.get('notes', 'No notes.')[:70]}...
        """)
        if st.button("Edit This Visit", key=f"edit_v_{v_item['id']}_v3", use_container_width=False): edit_action(v_item)
        st.markdown("---")

def render_record_edit_visit_tab(assistant: dict):
    is_edit = st.session_state.editing_visit_id is not None

    if not is_edit and not st.session_state.get('selected_patient_for_visit'):
        st.subheader("Step 1: Select Patient for New Visit")
        search_form_pats = SearchFormComponent(session_state_key="visit_patient_search_term_main_v3", label="Search Patient by Name or ID:")
        search_form_pats.render()
        pat_search_q = st.session_state.get("visit_patient_search_term_main_v3", "")

        if st.button("👤 Search Patients", key="search_pats_for_visit_btn_main_v3"):
            if pat_search_q:
                try: st.session_state.patients_found_for_visit_list = PatientQueries.search_patients(search_term=pat_search_q)
                except Exception as e: show_error_message(f"Error: {e}"); st.session_state.patients_found_for_visit_list = []
            else: st.info("Enter search term."); st.session_state.patients_found_for_visit_list = []
        
        if 'patients_found_for_visit_list' in st.session_state:
            for p_item in st.session_state.patients_found_for_visit_list:
                p_name = format_patient_name(p_item.get('first_name'), p_item.get('last_name'))
                if st.button(f"Select: {p_name} (ID: {p_item['id']})", key=f"sel_pat_v_{p_item['id']}_v3"):
                    st.session_state.selected_patient_for_visit = PatientQueries.get_patient_details(p_item['id'])
                    st.session_state.patients_found_for_visit_list = [] 
                    st.rerun()
            if not st.session_state.patients_found_for_visit_list and pat_search_q: st.info("No patients found.")

    elif st.session_state.get('selected_patient_for_visit'):
        p_name_disp = format_patient_name(st.session_state.selected_patient_for_visit.get('first_name'), st.session_state.selected_patient_for_visit.get('last_name'))
        header = f"Step 2: Edit Visit for {p_name_disp}" if is_edit else f"Step 2: Record New Visit for {p_name_disp}"
        st.subheader(header)

        visit_form = VisitFormComponent(patient_data=st.session_state.selected_patient_for_visit, edit_mode=is_edit, visit_data=st.session_state.visit_form_data, key_prefix="main_visit_form_v3")
        submitted_data = visit_form.render()

        if submitted_data:
            if submitted_data.get("cancelled"):
                show_info_message("Operation cancelled.")
                st.session_state.editing_visit_id = None; st.session_state.visit_form_data = {}; st.session_state.selected_patient_for_visit = None
                st.session_state.active_visit_management_tab_key = "View & Manage Visits"; st.rerun()
            elif is_edit: handle_update_visit(st.session_state.editing_visit_id, submitted_data, assistant['id'])
            else: handle_create_visit(submitted_data, assistant['id'])
        
        cancel_label = "Cancel Edit Mode" if is_edit else "Change Selected Patient / Cancel"
        if st.button(cancel_label, key="cancel_visit_form_btn_main_v3"):
            st.session_state.editing_visit_id = None; st.session_state.visit_form_data = {}; st.session_state.selected_patient_for_visit = None
            st.session_state.active_visit_management_tab_key = "View & Manage Visits" if is_edit else "Record / Edit Visit"
            st.rerun()
    else: st.info("Please select a patient to record or edit a visit.")


def show_visit_management_page():
    require_authentication()
    require_role_access([USER_ROLES['ASSISTANT']])
    inject_css()
    st.markdown("<h1>🗓️ Patient Visit Management</h1>", unsafe_allow_html=True)
    
    curr_user = get_current_user()
    if not curr_user: show_error_message("User data not found."); return

    # Initialize session states
    for key, default_val in [('selected_patient_for_visit', None), ('editing_visit_id', None),
                             ('visit_form_data', {}), ('visit_search_term_main_v3', ""), 
                             ('visit_patient_search_term_main_v3', ""), 
                             ('active_visit_management_tab_key', "View & Manage Visits"),
                             ('patients_found_for_visit_list', [])]:
        if key not in st.session_state: st.session_state[key] = default_val
    
    tab_list = ["View & Manage Visits", "Record / Edit Visit"]
    if st.session_state.editing_visit_id or st.session_state.selected_patient_for_visit:
        st.session_state.active_visit_management_tab_key = tab_list[1] # Default to this tab if state implies it
    
    # This simple tab switch method relies on reruns caused by other actions setting the state.
    # More direct tab switching in Streamlit is complex.
    active_tab_index = tab_list.index(st.session_state.active_visit_management_tab_key) if st.session_state.active_visit_management_tab_key in tab_list else 0
    
    # We are not using default_index in st.tabs as it's not a direct parameter.
    # The content within tabs will handle visibility based on session state.
    tabs_display = st.tabs(tab_list) 

    with tabs_display[0]: render_view_manage_visits_tab(curr_user)
    with tabs_display[1]: render_record_edit_visit_tab(curr_user)

if __name__ == "__main__":
    if 'user' not in st.session_state:
        st.session_state.user = {'id': 'assistant123', 'username': 'med_assistant_jane', 'role': USER_ROLES['ASSISTANT'], 'full_name': 'Jane Doe (Assistant)'}
        st.session_state.authenticated = True; st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)

    for key, default_val in [('selected_patient_for_visit', None), ('editing_visit_id', None),
                             ('visit_form_data', {}), ('visit_search_term_main_v3', ""), 
                             ('visit_patient_search_term_main_v3', ""), 
                             ('active_visit_management_tab_key', "View & Manage Visits"),
                             ('patients_found_for_visit_list', [])]:
        if key not in st.session_state: st.session_state[key] = default_val

    if not COMPONENTS_AVAILABLE: st.sidebar.warning("Using MOCK UI components for Visit Mgt.")
    if not DB_QUERIES_AVAILABLE: st.sidebar.warning("Using MOCK DB Queries for Visit Mgt.")
    
    # Ensure mock formatters are available if not imported from utils
    if 'format_patient_name' not in globals() or not callable(globals()['format_patient_name']):
        def format_patient_name(first, last): return f"{first or ''} {last or ''}".strip()
    if 'format_date_display' not in globals() or not callable(globals()['format_date_display']):
        def format_date_display(date_str_or_obj):
            if isinstance(date_str_or_obj, str): return date_str_or_obj[:10] if date_str_or_obj else "N/A"
            if isinstance(date_str_or_obj, (datetime, py_date)): return date_str_or_obj.strftime("%Y-%m-%d")
            return "N/A"

    # show_visit_management_page() # Called at module level now

# This call ensures Streamlit runs the page content when navigating
show_visit_management_page()

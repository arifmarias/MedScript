import streamlit as st
from datetime import datetime, timedelta, date as py_date
import copy

# Config and Auth
from config.settings import USER_ROLES
from config.styles import inject_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access

# Components (with Mocks)
try:
    from components.forms import PatientFormComponent, SearchFormComponent
    COMPONENTS_AVAILABLE = True
except ImportError:
    COMPONENTS_AVAILABLE = False
    class SearchFormComponent:
        def __init__(self, search_function=None, result_key_prefix=None, form_key=None, placeholder="Search...", label="Search", session_state_key="default_search_term", auto_submit=False, button_text="Search"):
            self.placeholder, self.label, self.session_state_key = placeholder, label, session_state_key
        def render(self):
            st.session_state[self.session_state_key] = st.text_input(self.label, value=st.session_state.get(self.session_state_key, ""), placeholder=self.placeholder, key=f"mock_search_sa_pat_{self.session_state_key}_v2") # Key updated
            return None
        def get_search_query(self): return st.session_state.get(self.session_state_key, "")

    class PatientFormComponent:
        def __init__(self, edit_mode=False, patient_data=None, key_prefix="sa_patient_form", required_fields=None):
            self.edit_mode = edit_mode
            self.patient_data = patient_data if patient_data else {}
            self.key_prefix = key_prefix
            self.required_fields = required_fields or ['first_name', 'last_name', 'dob', 'phone_number']
            # if not COMPONENTS_AVAILABLE: st.info("Using Mock PatientFormComponent for SA.") # In __main__

        def render(self):
            submitted_data = None
            with st.form(key=f"{self.key_prefix}_form_main_sa_v2"): # Key updated
                form_data = {}
                form_data['first_name'] = st.text_input("First Name*", value=self.patient_data.get('first_name', ''), key=f"{self.key_prefix}_fname_sa_v2") # Key updated
                form_data['last_name'] = st.text_input("Last Name*", value=self.patient_data.get('last_name', ''), key=f"{self.key_prefix}_lname_sa_v2") # Key updated

                dob_val = self.patient_data.get('dob')
                if isinstance(dob_val, str):
                    try: dob_val = datetime.strptime(dob_val, '%Y-%m-%d').date()
                    except ValueError: dob_val = None
                elif isinstance(dob_val, datetime): dob_val = dob_val.date()
                elif not isinstance(dob_val, py_date) : dob_val = None

                form_data['dob'] = st.date_input("Date of Birth*", value=dob_val, key=f"{self.key_prefix}_dob_sa_v2", min_value=py_date(1900,1,1), max_value=py_date.today()) # Key updated
                form_data['phone_number'] = st.text_input("Phone Number*", value=self.patient_data.get('phone_number', ''), key=f"{self.key_prefix}_phone_sa_v2") # Key updated
                form_data['email'] = st.text_input("Email Address", value=self.patient_data.get('email', ''), key=f"{self.key_prefix}_email_sa_v2") # Key updated
                form_data['address'] = st.text_area("Address", value=self.patient_data.get('address', ''), key=f"{self.key_prefix}_address_sa_v2") # Key updated
                st.caption(f"Original Creator ID (Read-only): {self.patient_data.get('created_by', 'N/A')}")
                form_data['allergies'] = st.text_area("Allergies", value=self.patient_data.get('allergies', ''), key=f"{self.key_prefix}_allergies_sa_v2")
                form_data['medical_history'] = st.text_area("Medical History Summary", value=self.patient_data.get('medical_history', ''), key=f"{self.key_prefix}_medhist_sa_v2")


                submit_btn_label = "Update Patient Details"
                col1, col2 = st.columns([3,1])
                if col1.form_submit_button(submit_btn_label, use_container_width=True, type="primary"):
                    valid = True
                    for field in self.required_fields:
                        if not form_data.get(field): valid = False; show_error_message(f"{field.replace('_',' ').title()} is required.")
                    if valid: submitted_data = {k: (v.isoformat() if isinstance(v, (py_date, datetime)) else v) for k,v in form_data.items()}
                if col2.form_submit_button("Cancel Edit", type="secondary", use_container_width=True):
                    submitted_data = {"cancelled": True}
            return submitted_data

try:
    from components.cards import PatientCard
except ImportError:
    def PatientCard(patient_data, actions, key):
        st.markdown(f"**{patient_data.get('first_name', 'N/A')} {patient_data.get('last_name', 'N/A')}** (ID: {patient_data.get('id', 'N/A')})")
        st.caption(f"DOB: {patient_data.get('dob', 'N/A')} | Phone: {patient_data.get('phone_number', 'N/A')} | Created By: {patient_data.get('created_by', 'N/A')}")
        for action_label, action_func in actions.items():
            if st.button(action_label, key=f"{key}_{action_label.lower().replace(' ', '_')}_sa_card_v2"): action_func() # Key updated

# Database Queries (with Mocks)
try:
    from database.queries import PatientQueries
    DB_QUERIES_AVAILABLE = True
except ImportError:
    DB_QUERIES_AVAILABLE = False
    MOCK_PATIENTS_STORE_SA = [
        {'id': 'pat_001', 'first_name': 'John', 'last_name': 'Doe', 'dob': '1985-01-15', 'phone_number': '555-0101', 'email': 'john.doe@example.com', 'created_by': 'assistant123', 'address': '123 Main St', 'emergency_contact_name': 'Jane Doe', 'emergency_contact_phone': '555-0102', 'allergies': 'Peanuts', 'medical_history': 'Hypertension'},
        {'id': 'pat_002', 'first_name': 'Jane', 'last_name': 'Smith', 'dob': '1992-07-22', 'phone_number': '555-0202', 'email': 'jane.smith@example.com', 'created_by': 'assistant456', 'address': '456 Oak Ave', 'emergency_contact_name': 'John Smith', 'emergency_contact_phone': '555-0201', 'allergies': 'None', 'medical_history': 'Asthma'},
        {'id': 'pat_003', 'first_name': 'Alice', 'last_name': 'Wonder', 'dob': '1978-11-05', 'phone_number': '555-0303', 'email': 'alice.wonder@example.com', 'created_by': 'doctor789', 'address': '789 Pine Ln', 'emergency_contact_name': 'Bob Wonder', 'emergency_contact_phone': '555-0304', 'allergies': 'Aspirin', 'medical_history': 'Migraines'},
        {'id': 'pat_004', 'first_name': 'Robert', 'last_name': 'Paulson', 'dob': '1960-03-10', 'phone_number': '555-0404', 'email': 'robert.p@example.com', 'created_by': 'assistant123', 'address': '101 Fight Club Rd', 'emergency_contact_name': 'Marla Singer', 'emergency_contact_phone': '555-0405', 'allergies': 'Soy', 'medical_history': 'Insomnia'},
    ]
    class PatientQueries:
        @staticmethod
        def search_patients(search_term=None, patient_id=None, created_by=None):
            results = copy.deepcopy(MOCK_PATIENTS_STORE_SA)
            if patient_id: return [p for p in results if p['id'] == patient_id]
            if search_term: # Super Admin search ignores created_by
                term = search_term.lower()
                results = [p for p in results if term in p['first_name'].lower() or term in p['last_name'].lower() or term in p.get('phone_number','') or term in p.get('email','')]
            return results
        @staticmethod
        def get_patient_details(patient_id):
            return next((copy.deepcopy(p) for p in MOCK_PATIENTS_STORE_SA if p['id'] == patient_id), None)
        @staticmethod
        def update_patient(patient_id, data, updated_by_id):
            for i, p_item in enumerate(MOCK_PATIENTS_STORE_SA):
                if p_item['id'] == patient_id:
                    original_creator = p_item.get('created_by')
                    MOCK_PATIENTS_STORE_SA[i] = {**p_item, **data, 'last_updated_by': updated_by_id, 'updated_at': datetime.now().isoformat()}
                    if 'created_by' not in data: MOCK_PATIENTS_STORE_SA[i]['created_by'] = original_creator
                    return MOCK_PATIENTS_STORE_SA[i]
            return None

# Utils
from utils.helpers import show_error_message, show_success_message, show_info_message

# --- Helper Functions for CRUD ---
def handle_sa_update_patient(patient_id, data, admin_id):
    try:
        updated_patient = PatientQueries.update_patient(patient_id, data, updated_by_id=admin_id)
        if updated_patient:
            show_success_message(f"Patient {updated_patient['first_name']} {updated_patient['last_name']} updated by Admin.")
            st.session_state.sa_editing_patient_id_v2 = None
            st.session_state.sa_patient_form_data_v2 = {}
            st.session_state.active_sa_patient_management_tab_v2 = "Search & Manage Patients"
            st.rerun()
        else: show_error_message("Failed to update patient information.")
    except Exception as e: show_error_message(f"Error updating patient: {e}")

# --- Tab Rendering Functions ---
def render_sa_search_manage_patients_tab(admin_user: dict):
    st.subheader("Search All Patient Records")
    search_form = SearchFormComponent(session_state_key="sa_patient_search_term_v2", label="Search by Name, ID, Phone, or Email:") # Key updated
    search_form.render()
    search_query = st.session_state.get("sa_patient_search_term_v2", "")

    if st.button("🔍 Search All Patients", key="sa_search_patients_btn_v2"): perform_search_now = True # Key updated
    else: perform_search_now = bool(search_query) # Search if term exists, otherwise show all (or some default)

    patients_data = []
    if perform_search_now or not search_query: # If button clicked or no search query (show all)
        try: patients_data = PatientQueries.search_patients(search_term=search_query)
        except Exception as e: show_error_message(f"Error searching patients: {e}")

    total_system_patients = len(PatientQueries.search_patients())
    st.caption(f"Displaying {len(patients_data)} of {total_system_patients} total patients in system.")

    if not patients_data and search_query: st.info(f"No patients found matching '{search_query}'.")
    elif not patients_data and not search_query : st.info("No patients in the system yet.") # Only if DB is empty

    for p_item_data in patients_data:
        def edit_action_sa(patient_data_item=p_item_data):
            st.session_state.sa_editing_patient_id_v2 = patient_data_item['id'] # Key updated
            full_details_sa = PatientQueries.get_patient_details(patient_data_item['id'])
            st.session_state.sa_patient_form_data_v2 = full_details_sa if full_details_sa else patient_data_item # Key updated
            st.session_state.active_sa_patient_management_tab_v2 = "Edit Patient Details"  # Key updated
            st.rerun()

        actions_for_card = {"Edit Patient Details": edit_action_sa}
        PatientCard(patient_data=p_item_data, actions=actions_for_card, key=f"sa_pat_card_{p_item_data['id']}_v2") # Key updated
        st.markdown("---")

def render_sa_edit_patient_tab(admin_user: dict):
    if not st.session_state.sa_editing_patient_id_v2: # Key updated
        st.info("No patient selected for editing. Please select a patient from the 'Search & Manage Patients' tab.")
        if st.button("Back to Search", key="sa_back_to_search_v2"): # Key updated
            st.session_state.active_sa_patient_management_tab_v2 = "Search & Manage Patients" # Key updated
            st.rerun()
        return

    patient_name = f"{st.session_state.sa_patient_form_data_v2.get('first_name', '')} {st.session_state.sa_patient_form_data_v2.get('last_name', '')}" # Key updated
    st.subheader(f"Edit Patient Record: {patient_name} (ID: {st.session_state.sa_editing_patient_id_v2})") # Key updated

    patient_form_sa = PatientFormComponent(edit_mode=True, patient_data=st.session_state.sa_patient_form_data_v2, key_prefix="sa_edit_patient_form_v2") # Key updated
    submitted_patient_data = patient_form_sa.render()

    if submitted_patient_data:
        if submitted_patient_data.get("cancelled"):
            show_info_message("Edit operation cancelled.")
            st.session_state.sa_editing_patient_id_v2 = None; st.session_state.sa_patient_form_data_v2 = {} # Keys updated
            st.session_state.active_sa_patient_management_tab_v2 = "Search & Manage Patients"; st.rerun() # Key updated
        else:
            handle_sa_update_patient(st.session_state.sa_editing_patient_id_v2, submitted_patient_data, admin_user['id']) # Key updated

# --- Main Page Function ---
def show_sa_patient_management_page():
    require_authentication()
    require_role_access([USER_ROLES['SUPER_ADMIN']])
    inject_css()
    st.markdown("<h1>👥 All Patients (Super Admin View)</h1>", unsafe_allow_html=True)

    admin = get_current_user()
    if not admin: show_error_message("Admin user data not found."); return

    # Initialize session state variables with 'sa_' prefix and versioned keys
    if 'sa_editing_patient_id_v2' not in st.session_state: st.session_state.sa_editing_patient_id_v2 = None
    if 'sa_patient_form_data_v2' not in st.session_state: st.session_state.sa_patient_form_data_v2 = {}
    if 'sa_patient_search_term_v2' not in st.session_state: st.session_state.sa_patient_search_term_v2 = ""
    if 'active_sa_patient_management_tab_v2' not in st.session_state:
        st.session_state.active_sa_patient_management_tab_v2 = "Search & Manage Patients"

    tab_titles_sa = ["Search & Manage Patients", "Edit Patient Details"]

    # Logic to determine which tab should be "active" based on session state
    # This doesn't directly set st.tabs' active tab, but ensures content is ready for when user clicks or page reruns
    if st.session_state.sa_editing_patient_id_v2:
        # If editing, we expect the "Edit Patient Details" tab to be the focus.
        # Streamlit's st.tabs doesn't have a programmatic way to set the active tab after initial render without workarounds.
        # The content of the tabs will be conditional on session state.
        pass # The content of render_sa_edit_patient_tab will handle being visible.

    tab1_sa, tab2_sa = st.tabs(tab_titles_sa)

    with tab1_sa:
        render_sa_search_manage_patients_tab(admin)

    with tab2_sa:
        render_sa_edit_patient_tab(admin)


if __name__ == "__main__":
    if 'user' not in st.session_state:
        st.session_state.user = {'id': 'superadmin002', 'username': 'sa_godmode_v2', 'role': USER_ROLES['SUPER_ADMIN'], 'full_name': 'Super Admin Prime v2'} # Updated details
        st.session_state.authenticated = True; st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)

    # Ensure all versioned session state keys are initialized for standalone run
    if 'sa_editing_patient_id_v2' not in st.session_state: st.session_state.sa_editing_patient_id_v2 = None
    if 'sa_patient_form_data_v2' not in st.session_state: st.session_state.sa_patient_form_data_v2 = {}
    if 'sa_patient_search_term_v2' not in st.session_state: st.session_state.sa_patient_search_term_v2 = ""
    if 'active_sa_patient_management_tab_v2' not in st.session_state: st.session_state.active_sa_patient_management_tab_v2 = "Search & Manage Patients"

    if not COMPONENTS_AVAILABLE: st.sidebar.warning("Using MOCK UI components for SA Patient Mgt.")
    if not DB_QUERIES_AVAILABLE: st.sidebar.warning("Using MOCK DB Queries for SA Patient Mgt.")

    show_sa_patient_management_page()

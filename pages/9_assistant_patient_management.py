import streamlit as st
from datetime import datetime, timedelta
import copy

# Config and Auth
from config.settings import USER_ROLES
from config.styles import inject_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access # , PermissionChecker, Permission (if more granular needed)

# Components
try:
    from components.forms import PatientFormComponent, SearchFormComponent
    COMPONENTS_AVAILABLE = True
except ImportError:
    COMPONENTS_AVAILABLE = False
    # Mock SearchFormComponent
    class SearchFormComponent:
        def __init__(self, search_function=None, result_key_prefix=None, form_key=None, placeholder="Search...", label="Search", session_state_key="default_search_term", auto_submit=False, button_text="Search"):
            self.search_function = search_function
            self.placeholder = placeholder
            self.label = label
            self.session_state_key = session_state_key
            self.auto_submit = auto_submit # Not used in this simple mock
            self.button_text = button_text # Not used in this simple mock

        def render(self):
            st.session_state[self.session_state_key] = st.text_input(self.label,
                                                                    value=st.session_state.get(self.session_state_key, ""),
                                                                    placeholder=self.placeholder,
                                                                    key=f"mock_search_ssf_{self.session_state_key}")
            return None
        def get_search_query(self):
             return st.session_state.get(self.session_state_key, "")

    # Mock PatientFormComponent
    class PatientFormComponent:
        def __init__(self, edit_mode=False, patient_data=None, key_prefix="patient_form", required_fields=None):
            self.edit_mode = edit_mode
            self.patient_data = patient_data if patient_data else {}
            self.key_prefix = key_prefix
            self.required_fields = required_fields or ['first_name', 'last_name', 'dob', 'phone_number']
            if not COMPONENTS_AVAILABLE: st.info("Using Mock PatientFormComponent.")


        def render(self):
            submitted_data = None
            with st.form(key=f"{self.key_prefix}_form_main"): # Changed key
                form_data = {}
                form_data['first_name'] = st.text_input("First Name*", value=self.patient_data.get('first_name', ''), key=f"{self.key_prefix}_fname_main")
                form_data['last_name'] = st.text_input("Last Name*", value=self.patient_data.get('last_name', ''), key=f"{self.key_prefix}_lname_main")

                dob_val = self.patient_data.get('dob')
                if isinstance(dob_val, str):
                    try: dob_val = datetime.strptime(dob_val, '%Y-%m-%d').date()
                    except ValueError: dob_val = None
                elif isinstance(dob_val, datetime):
                    dob_val = dob_val.date()

                form_data['dob'] = st.date_input("Date of Birth*", value=dob_val, key=f"{self.key_prefix}_dob_main", min_value=date(1900,1,1), max_value=date.today())
                form_data['phone_number'] = st.text_input("Phone Number*", value=self.patient_data.get('phone_number', ''), key=f"{self.key_prefix}_phone_main")
                form_data['email'] = st.text_input("Email Address", value=self.patient_data.get('email', ''), key=f"{self.key_prefix}_email_main")
                form_data['address'] = st.text_area("Address", value=self.patient_data.get('address', ''), key=f"{self.key_prefix}_address_main")
                form_data['emergency_contact_name'] = st.text_input("Emergency Contact Name", value=self.patient_data.get('emergency_contact_name', ''), key=f"{self.key_prefix}_econtact_name_main")
                form_data['emergency_contact_phone'] = st.text_input("Emergency Contact Phone", value=self.patient_data.get('emergency_contact_phone', ''), key=f"{self.key_prefix}_econtact_phone_main")
                form_data['allergies'] = st.text_area("Allergies", value=self.patient_data.get('allergies', ''), key=f"{self.key_prefix}_allergies_main")
                form_data['medical_history'] = st.text_area("Medical History Summary", value=self.patient_data.get('medical_history', ''), key=f"{self.key_prefix}_medhist_main")


                submit_btn_label = "Update Patient" if self.edit_mode else "Register Patient"
                col1, col2 = st.columns([3,1])
                with col1:
                    if st.form_submit_button(submit_btn_label, use_container_width=True, type="primary"):
                        # Basic validation for mock
                        valid = True
                        for field in self.required_fields:
                            if not form_data.get(field):
                                show_error_message(f"{field.replace('_',' ').title()} is required.")
                                valid = False
                        if valid:
                             submitted_data = {k: (v.isoformat() if isinstance(v, (date, datetime)) else v) for k,v in form_data.items()}
                with col2:
                    if st.form_submit_button("Cancel", type="secondary", use_container_width=True):
                        submitted_data = {"cancelled": True}
            return submitted_data

try:
    from components.cards import PatientCard
except ImportError:
    def PatientCard(patient_data, actions, key):
        st.markdown(f"**{patient_data.get('first_name', 'N/A')} {patient_data.get('last_name', 'N/A')}** (ID: {patient_data.get('id', 'N/A')})")
        st.caption(f"DOB: {patient_data.get('dob', 'N/A')}, Phone: {patient_data.get('phone_number', 'N/A')}")
        for action_label, action_func in actions.items():
            if st.button(action_label, key=f"{key}_{action_label.lower().replace(' ', '_')}_cardbtn"):
                action_func()

from datetime import date # ensure date is imported for PatientFormComponent mock

# Database Queries (with Mocks)
try:
    from database.queries import PatientQueries
    DB_QUERIES_AVAILABLE = True
except ImportError:
    DB_QUERIES_AVAILABLE = False
    MOCK_PATIENTS_STORE = [
        {'id': 'pat_001', 'first_name': 'John', 'last_name': 'Doe', 'dob': '1985-01-15', 'phone_number': '555-0101', 'email': 'john.doe@example.com', 'created_by': 'assistant123', 'address': '123 Main St', 'emergency_contact_name': 'Jane Doe', 'emergency_contact_phone': '555-0102', 'allergies': 'Peanuts', 'medical_history': 'Hypertension'},
        {'id': 'pat_002', 'first_name': 'Jane', 'last_name': 'Smith', 'dob': '1992-07-22', 'phone_number': '555-0202', 'email': 'jane.smith@example.com', 'created_by': 'assistant456', 'address': '456 Oak Ave', 'emergency_contact_name': 'John Smith', 'emergency_contact_phone': '555-0201', 'allergies': 'None', 'medical_history': 'Asthma'},
    ]
    class PatientQueries:
        @staticmethod
        def search_patients(search_term=None, created_by=None, patient_id=None):
            results = copy.deepcopy(MOCK_PATIENTS_STORE)
            if patient_id: return [p for p in results if p['id'] == patient_id]
            if created_by: results = [p for p in results if p.get('created_by') == created_by]
            if search_term:
                term = search_term.lower()
                results = [p for p in results if term in p['first_name'].lower() or term in p['last_name'].lower() or term in p.get('phone_number','')]
            return results
        @staticmethod
        def get_patient_details(patient_id):
            return next((copy.deepcopy(p) for p in MOCK_PATIENTS_STORE if p['id'] == patient_id), None)
        @staticmethod
        def create_patient(data, created_by_id):
            new_id = f"pat_{len(MOCK_PATIENTS_STORE) + 1:03d}_{datetime.now().strftime('%S%f')}"
            new_patient = {'id': new_id, **data, 'created_by': created_by_id, 'created_at': datetime.now().isoformat()}
            MOCK_PATIENTS_STORE.append(new_patient)
            return new_patient
        @staticmethod
        def update_patient(patient_id, data, updated_by_id):
            for i, p in enumerate(MOCK_PATIENTS_STORE):
                if p['id'] == patient_id:
                    original_created_by = p.get('created_by')
                    MOCK_PATIENTS_STORE[i] = {**p, **data, 'updated_at': datetime.now().isoformat(), 'last_updated_by': updated_by_id}
                    if 'created_by' not in data : MOCK_PATIENTS_STORE[i]['created_by'] = original_created_by
                    return MOCK_PATIENTS_STORE[i]
            return None

from utils.helpers import show_error_message, show_success_message, show_warning_message, show_info_message

def handle_create_patient(data, assistant_id):
    try:
        new_patient = PatientQueries.create_patient(data, created_by_id=assistant_id)
        if new_patient:
            show_success_message(f"Patient {new_patient['first_name']} {new_patient['last_name']} registered (ID: {new_patient['id']}).")
            st.session_state.patient_form_data = {}
        else: show_error_message("Failed to register patient.")
    except Exception as e: show_error_message(f"Error: {e}")

def handle_update_patient(patient_id, data, assistant_id):
    try:
        updated_patient = PatientQueries.update_patient(patient_id, data, updated_by_id=assistant_id)
        if updated_patient:
            show_success_message(f"Patient {updated_patient['first_name']} {updated_patient['last_name']} updated.")
            st.session_state.editing_patient_id = None
            st.session_state.patient_form_data = {}
            st.session_state.active_patient_management_tab_key = "Search & Manage Patients" # Request tab switch
            st.rerun()
        else: show_error_message("Failed to update patient.")
    except Exception as e: show_error_message(f"Error: {e}")

def render_search_manage_patients_tab(assistant: dict):
    st.subheader("Search Patients")
    # Note: SearchFormComponent mock directly uses session_state.patient_search_term_main
    search_form = SearchFormComponent(session_state_key="patient_search_term_main", label="Search by Name, ID, or Phone:")
    search_form.render()

    search_term_val = st.session_state.get("patient_search_term_main", "")

    if st.button("🔍 Search Patients", key="search_patients_btn_main"):
        perform_search = True
    elif not search_term_val: # If no search term, show all managed by assistant by default
        perform_search = True
    else: # Only search if term exists (button not strictly needed if we want live search, but good for explicit action)
        perform_search = False

    patients_list = []
    if perform_search or search_term_val: # Search if button clicked OR if there's a search term already
        try:
            patients_list = PatientQueries.search_patients(search_term=search_term_val, created_by=assistant['id'])
        except Exception as e:
            show_error_message(f"Error searching: {e}")

    if not patients_list and (perform_search or search_term_val):
        st.info(f"No patients found matching '{search_term_val}' that you manage.")
    elif not patients_list and not search_term_val :
         st.info("You have not registered any patients yet. Use the 'Register New Patient' tab.")


    for patient_item in patients_list:
        def edit_action_fn(p_data=patient_item):
            st.session_state.editing_patient_id = p_data['id']
            full_details = PatientQueries.get_patient_details(p_data['id'])
            st.session_state.patient_form_data = full_details if full_details else p_data
            st.session_state.active_patient_management_tab_key = "Register / Edit Patient"
            st.rerun()

        PatientCard(patient_data=patient_item, actions={"Edit Details": edit_action_fn}, key=f"pat_card_{patient_item['id']}")
        st.markdown("---")

def render_register_edit_patient_tab(assistant: dict):
    edit_mode_flag = st.session_state.editing_patient_id is not None

    header_txt = f"Edit Patient: {st.session_state.patient_form_data.get('first_name', '')} {st.session_state.patient_form_data.get('last_name', '')}" if edit_mode_flag else "Register New Patient"
    st.subheader(header_txt)

    patient_form_component = PatientFormComponent(
        edit_mode=edit_mode_flag,
        patient_data=st.session_state.patient_form_data,
        key_prefix="main_pat_form"
    )
    submitted_form_data = patient_form_component.render()

    if submitted_form_data:
        if submitted_form_data.get("cancelled"):
            show_info_message("Operation cancelled.")
            st.session_state.editing_patient_id = None
            st.session_state.patient_form_data = {}
            st.session_state.active_patient_management_tab_key = "Search & Manage Patients"
            st.rerun()
        elif edit_mode_flag:
            handle_update_patient(st.session_state.editing_patient_id, submitted_form_data, assistant['id'])
        else:
            handle_create_patient(submitted_form_data, assistant['id'])
            # Form data is cleared within handle_create_patient. To switch tab:
            # st.session_state.active_patient_management_tab_key = "Search & Manage Patients"; st.rerun()

    # "Cancel Edit" button if in edit mode and form hasn't been submitted for cancellation yet
    if edit_mode_flag and not submitted_form_data:
        if st.button("Cancel Edit Mode", key="cancel_edit_mode_btn_main"):
            st.session_state.editing_patient_id = None
            st.session_state.patient_form_data = {}
            st.session_state.active_patient_management_tab_key = "Search & Manage Patients"
            st.rerun()

def show_patient_management_page():
    require_authentication()
    require_role_access([USER_ROLES['ASSISTANT']])
    inject_css()
    st.markdown("<h1>👤 Patient Management</h1>", unsafe_allow_html=True)

    current_user = get_current_user()
    if not current_user:
        show_error_message("Assistant user data not found."); return

    if 'editing_patient_id' not in st.session_state: st.session_state.editing_patient_id = None
    if 'patient_form_data' not in st.session_state: st.session_state.patient_form_data = {}
    if 'patient_search_term_main' not in st.session_state: st.session_state.patient_search_term_main = "" # Specific key for search
    if 'active_patient_management_tab_key' not in st.session_state:
        st.session_state.active_patient_management_tab_key = "Search & Manage Patients"

    tab_titles_list = ["Search & Manage Patients", "Register / Edit Patient"]

    # Determine default tab based on state
    if st.session_state.editing_patient_id: # If editing, force to second tab
        st.session_state.active_patient_management_tab_key = tab_titles_list[1]

    # Create tabs. Streamlit's default tab is always the first unless keys change or it's handled differently.
    # The programmatic switch is tricky. Best user experience is often to let user click.
    # Forcing tab switch on action (like 'Edit') is done by st.rerun() after setting state.

    # Use a non-persisted variable for default_index for st.tabs if needed, but st.tabs doesn't have it.
    # Instead, we rely on the fact that when "Edit" is clicked, a rerun happens,
    # and the content of the "Register / Edit Patient" tab will reflect the edit mode.

    tab1, tab2 = st.tabs(tab_titles_list)

    with tab1:
        render_search_manage_patients_tab(current_user)

    with tab2:
        render_register_edit_patient_tab(current_user)

if __name__ == "__main__":
    if 'user' not in st.session_state:
        st.session_state.user = {
            'id': 'assistant123', 'username': 'med_assistant_jane',
            'role': USER_ROLES['ASSISTANT'], 'full_name': 'Jane Doe (Assistant)',
            'email': 'jane.assistant@example.com'}
        st.session_state.authenticated = True
        st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)

    if 'editing_patient_id' not in st.session_state: st.session_state.editing_patient_id = None
    if 'patient_form_data' not in st.session_state: st.session_state.patient_form_data = {}
    if 'patient_search_term_main' not in st.session_state: st.session_state.patient_search_term_main = ""
    if 'active_patient_management_tab_key' not in st.session_state:
        st.session_state.active_patient_management_tab_key = "Search & Manage Patients"

    if not COMPONENTS_AVAILABLE: st.sidebar.warning("Using MOCK UI components.")
    if not DB_QUERIES_AVAILABLE: st.sidebar.warning("Using MOCK DB Queries.")

    # show_patient_management_page() # Called at module level now

# This call ensures Streamlit runs the page content when navigating
show_patient_management_page()

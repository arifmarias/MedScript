import streamlit as st
from datetime import datetime, timedelta
import copy

# Config and Auth
from config.settings import USER_ROLES, DRUG_CLASSES
from config.styles import inject_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access

# Components (with Mocks)
try:
    from components.forms import MedicationFormComponent, SearchFormComponent
    from components.cards import MedicationCard
    COMPONENTS_AVAILABLE = True
except ImportError:
    COMPONENTS_AVAILABLE = False
    class SearchFormComponent:
        def __init__(self, search_function=None,result_key_prefix=None,form_key=None,placeholder="Search...",label="Search",session_state_key="default_search_term",auto_submit=False,button_text="Search"):
            self.placeholder, self.label, self.session_state_key = placeholder, label, session_state_key
        def render(self):
            st.session_state[self.session_state_key] = st.text_input(self.label, value=st.session_state.get(self.session_state_key, ""), placeholder=self.placeholder, key=f"mock_search_sa_med_mgt_{self.session_state_key}_v2") # Key updated
            return None
        def get_search_query(self): return st.session_state.get(self.session_state_key, "")

    class MedicationFormComponent:
        def __init__(self, edit_mode=False, medication_data=None, key_prefix="sa_med_form", required_fields=None):
            self.edit_mode = edit_mode
            self.med_data = medication_data if medication_data else {}
            self.key_prefix = key_prefix
            self.required = required_fields or ['name', 'generic_name', 'drug_class', 'form', 'strength']
            # if not COMPONENTS_AVAILABLE: st.info("Using Mock MedicationFormComponent for SA Med Mgt.") # In __main__

        def render(self):
            submitted_data = None
            with st.form(key=f"{self.key_prefix}_form_main_sa_med_v2"): # Key updated
                form_data = {}
                form_data['name'] = st.text_input("Medication Name*", value=self.med_data.get('name', ''), key=f"{self.key_prefix}_name_v2") # Key updated
                form_data['generic_name'] = st.text_input("Generic Name*", value=self.med_data.get('generic_name', ''), key=f"{self.key_prefix}_gen_name_v2") # Key updated

                available_drug_classes = DRUG_CLASSES if isinstance(DRUG_CLASSES, list) and DRUG_CLASSES else ["Analgesics", "Antibiotics", "NSAIDs", "ACE Inhibitors", "Other"]
                current_drug_class_idx = 0
                if self.med_data.get('drug_class') in available_drug_classes:
                    current_drug_class_idx = available_drug_classes.index(self.med_data['drug_class'])
                form_data['drug_class'] = st.selectbox("Drug Class*", options=available_drug_classes, index=current_drug_class_idx, key=f"{self.key_prefix}_drug_class_v2") # Key updated

                form_data['form'] = st.text_input("Form (e.g., Tablet, Capsule)*", value=self.med_data.get('form', ''), key=f"{self.key_prefix}_form_v2") # Key updated
                form_data['strength'] = st.text_input("Strength (e.g., 10mg, 500mg/5ml)*", value=self.med_data.get('strength', ''), key=f"{self.key_prefix}_strength_v2") # Key updated
                form_data['manufacturer'] = st.text_input("Manufacturer", value=self.med_data.get('manufacturer', ''), key=f"{self.key_prefix}_mfr_v2") # Key updated
                form_data['indications'] = st.text_area("Indications (comma-separated)", value=', '.join(self.med_data.get('indications', [])), key=f"{self.key_prefix}_ind_v2") # Key updated
                form_data['contraindications'] = st.text_area("Contraindications (comma-separated)", value=', '.join(self.med_data.get('contraindications', [])), key=f"{self.key_prefix}_contra_v2") # Key updated
                form_data['storage_conditions'] = st.text_input("Storage Conditions", value=self.med_data.get('storage_conditions', 'Room temperature'), key=f"{self.key_prefix}_storage_v2") # Key updated
                form_data['is_otc'] = st.checkbox("Is Over-The-Counter (OTC)?", value=self.med_data.get('is_otc', False), key=f"{self.key_prefix}_otc_v2") # Key updated
                form_data['notes'] = st.text_area("Additional Notes", value=self.med_data.get('notes', ''), key=f"{self.key_prefix}_notes_v2") # Key updated
                form_data['is_active'] = st.checkbox("Is Active in Database?", value=self.med_data.get('is_active', True), key=f"{self.key_prefix}_is_active_v2") # Key updated

                submit_label = "Update Medication" if self.edit_mode else "Add Medication to Database"
                col1, col2 = st.columns([3,1])
                if col1.form_submit_button(submit_label, use_container_width=True, type="primary"):
                    valid = True
                    for field in self.required:
                        if not form_data.get(field): valid = False; show_error_message(f"{field.replace('_',' ').title()} is required.")
                    if valid:
                        form_data['indications'] = [i.strip() for i in form_data['indications'].split(',') if i.strip()]
                        form_data['contraindications'] = [c.strip() for c in form_data['contraindications'].split(',') if c.strip()]
                        submitted_data = form_data
                if col2.form_submit_button("Cancel", type="secondary", use_container_width=True):
                    submitted_data = {"cancelled": True}
            return submitted_data

    def MedicationCard(medication_data, actions, key, show_actions=True):
        status = "Active" if medication_data.get('is_active', True) else "Inactive"
        st.markdown(f"**{medication_data.get('name', 'N/A')}** ({status})")
        st.caption(f"Generic: {medication_data.get('generic_name', 'N/A')} | Class: {medication_data.get('drug_class', 'N/A')}")
        if show_actions and actions:
            action_cols = st.columns(len(actions))
            for i, (action_label, action_func) in enumerate(actions.items()):
                if action_cols[i].button(action_label, key=f"{key}_{action_label.lower().replace(' ', '_')}_sa_med_card_v2", use_container_width=True): action_func() # Key updated

# Database Queries (with Mocks)
try:
    from database.queries import MedicationQueries
    DB_QUERIES_AVAILABLE = True
except ImportError:
    DB_QUERIES_AVAILABLE = False
    MOCK_MEDS_DB_SA = [
        {'id': 'med_sa_001', 'name': 'SuperDrug A 100mg', 'generic_name': 'GenericSuperA', 'drug_class': DRUG_CLASSES[0] if DRUG_CLASSES and isinstance(DRUG_CLASSES, list) and len(DRUG_CLASSES)>0 else 'DefaultClass1', 'form': 'Tablet', 'strength': '100mg', 'manufacturer': 'AdminPharma', 'indications': ['General Use'], 'contraindications': [], 'is_otc': False, 'storage_conditions': 'Cool, dry place', 'notes': 'For admin use only.', 'is_active': True, 'created_by': 'sa_godmode', 'created_at': datetime.now().isoformat()},
        {'id': 'med_sa_002', 'name': 'MediTonic B 50ml', 'generic_name': 'GenericTonicB', 'drug_class': DRUG_CLASSES[1] if DRUG_CLASSES and isinstance(DRUG_CLASSES, list) and len(DRUG_CLASSES)>1 else 'DefaultClass2', 'form': 'Syrup', 'strength': '50mg/5ml', 'manufacturer': 'SystemMeds', 'indications': ['Specific conditions'], 'contraindications': ['Allergy to B'], 'is_otc': True, 'storage_conditions': 'Refrigerate', 'notes': '', 'is_active': True, 'created_by': 'sa_godmode', 'created_at': (datetime.now() - timedelta(days=10)).isoformat()},
        {'id': 'med_sa_003', 'name': 'InactivePill C', 'generic_name': 'GenericInactiveC', 'drug_class': 'DefaultClass1', 'form': 'Pill', 'strength': '10mg', 'manufacturer': 'OldMeds', 'indications': [], 'contraindications': [], 'is_otc': False, 'storage_conditions': 'Room temp', 'notes': 'Phased out.', 'is_active': False, 'created_by': 'sa_godmode', 'created_at': (datetime.now() - timedelta(days=100)).isoformat()},
    ]
    class MedicationQueries:
        @staticmethod
        def search_medications(search_term=None, drug_class=None, is_active=None, favorites_only=None, doctor_id=None):
            results = copy.deepcopy(MOCK_MEDS_DB_SA)
            if search_term: term = search_term.lower(); results = [m for m in results if term in m['name'].lower() or term in m.get('generic_name','').lower()]
            if drug_class and drug_class != "All": results = [m for m in results if m.get('drug_class') == drug_class]
            if is_active is not None: results = [m for m in results if m.get('is_active') == is_active]
            return sorted(results, key=lambda x: x['name']) # Sort alphabetically
        @staticmethod
        def get_medication_details(medication_id):
            return next((copy.deepcopy(m) for m in MOCK_MEDS_DB_SA if m['id'] == medication_id), None)
        @staticmethod
        def create_medication(data, created_by_id):
            new_id = f"med_sa_{len(MOCK_MEDS_DB_SA) + 1:03d}_{datetime.now().strftime('%S%f')}"
            new_med = {'id': new_id, **data, 'created_by': created_by_id, 'created_at': datetime.now().isoformat()}
            if 'is_active' not in new_med: new_med['is_active'] = True
            MOCK_MEDS_DB_SA.append(new_med)
            return new_med
        @staticmethod
        def update_medication(medication_id, data, updated_by_id):
            for i, m_item in enumerate(MOCK_MEDS_DB_SA):
                if m_item['id'] == medication_id:
                    MOCK_MEDS_DB_SA[i] = {**m_item, **data, 'last_updated_by': updated_by_id, 'updated_at': datetime.now().isoformat()}
                    return MOCK_MEDS_DB_SA[i]
            return None
        @staticmethod
        def set_medication_status(medication_id, is_active_status, updated_by_id): # Renamed for clarity
            for i, m_item in enumerate(MOCK_MEDS_DB_SA):
                if m_item['id'] == medication_id:
                    MOCK_MEDS_DB_SA[i]['is_active'] = is_active_status
                    MOCK_MEDS_DB_SA[i]['last_updated_by'] = updated_by_id
                    MOCK_MEDS_DB_SA[i]['updated_at'] = datetime.now().isoformat()
                    return MOCK_MEDS_DB_SA[i]
            return None

# Utils
from utils.helpers import show_error_message, show_success_message, show_info_message

# --- Helper Functions for CRUD ---
def handle_sa_create_medication(data, admin_id):
    try:
        new_med = MedicationQueries.create_medication(data, created_by_id=admin_id)
        if new_med:
            show_success_message(f"Medication '{new_med['name']}' added (ID: {new_med['id']}).")
            st.session_state.sa_med_form_data_v2 = {}
            st.session_state.sa_editing_med_id_v2 = None # Go back to manage view after adding
            st.session_state.active_sa_med_management_tab_v2 = "Manage Medications"; st.rerun()
        else: show_error_message("Failed to add medication.")
    except Exception as e: show_error_message(f"Error: {e}")

def handle_sa_update_medication(med_id, data, admin_id):
    try:
        updated_med = MedicationQueries.update_medication(med_id, data, updated_by_id=admin_id)
        if updated_med:
            show_success_message(f"Medication '{updated_med['name']}' updated.")
            st.session_state.sa_editing_med_id_v2 = None; st.session_state.sa_med_form_data_v2 = {}
            st.session_state.active_sa_med_management_tab_v2 = "Manage Medications"; st.rerun()
        else: show_error_message("Failed to update medication.")
    except Exception as e: show_error_message(f"Error: {e}")

def handle_sa_toggle_med_status(med_id, current_is_active_status, admin_id):
    try:
        updated_med = MedicationQueries.set_medication_status(med_id, not current_is_active_status, updated_by_id=admin_id)
        if updated_med:
            action = "activated" if updated_med['is_active'] else "deactivated"
            show_success_message(f"Medication '{updated_med['name']}' has been {action}.")
            st.rerun() # Refresh list
        else: show_error_message("Failed to toggle medication status.")
    except Exception as e: show_error_message(f"Error: {e}")


# --- Tab Rendering Functions ---
def render_sa_manage_medications_tab(admin_user: dict):
    st.subheader("Browse & Manage Central Medication Database")
    if st.button("➕ Add New Medication to Database", key="sa_add_new_med_btn_v2"): # Key updated
        st.session_state.sa_editing_med_id_v2 = 'new' # Key updated
        st.session_state.sa_med_form_data_v2 = {'is_active': True} # Key updated
        st.session_state.active_sa_med_management_tab_v2 = "Add/Edit Medication" # Key updated
        st.rerun()
    st.markdown("---")

    search_form = SearchFormComponent(session_state_key="sa_med_search_term_v2", label="Search by Name or Generic Name:") # Key updated
    search_form.render()
    search_query = st.session_state.get("sa_med_search_term_v2", "")

    filter_cols = st.columns(2)
    with filter_cols[0]:
        default_drug_classes = ["Other"] # Fallback if DRUG_CLASSES is empty or not a list
        available_drug_classes_list = DRUG_CLASSES if isinstance(DRUG_CLASSES, list) and DRUG_CLASSES else default_drug_classes
        all_drug_classes_options = ["All"] + sorted(list(set(available_drug_classes_list)))

        current_drug_class_filter = st.session_state.get('sa_med_drug_class_filter_v2', "All") # Key updated
        if current_drug_class_filter not in all_drug_classes_options: current_drug_class_filter = "All" # Ensure valid default
        st.session_state.sa_med_drug_class_filter_v2 = st.selectbox("Filter by Drug Class:", options=all_drug_classes_options, index=all_drug_classes_options.index(current_drug_class_filter), key="sa_med_class_filter_dd_v2") # Key updated
    with filter_cols[1]:
        status_options_map = {"All": None, "Active": True, "Inactive": False}
        current_status_label = st.session_state.get('sa_med_status_filter_label_v2', "All") # Key updated
        st.session_state.sa_med_status_filter_label_v2 = st.radio("Filter by Status:", options=list(status_options_map.keys()), index=list(status_options_map.keys()).index(current_status_label), horizontal=True, key="sa_med_status_radio_v2") # Key updated

    if st.button("🔍 Apply Filters / Search", key="sa_apply_med_filters_btn_v2"): st.rerun() # Key updated

    meds_data_list = []
    try:
        active_filter_val = status_options_map[st.session_state.sa_med_status_filter_label_v2] # Key updated
        meds_data_list = MedicationQueries.search_medications(search_term=search_query, drug_class=st.session_state.sa_med_drug_class_filter_v2, is_active=active_filter_val) # Key updated
    except Exception as e: show_error_message(f"Error: {e}")

    st.caption(f"Displaying {len(meds_data_list)} medication(s).")
    if not meds_data_list and (search_query or st.session_state.sa_med_drug_class_filter_v2 != "All" or st.session_state.sa_med_status_filter_label_v2 != "All"): # Key updated for filters
        st.info("No medications found matching current filters.")

    for med_item_data in meds_data_list:
        def edit_action_fn(m_data_item=med_item_data):
            st.session_state.sa_editing_med_id_v2 = m_data_item['id'] # Key updated
            st.session_state.sa_med_form_data_v2 = MedicationQueries.get_medication_details(m_data_item['id']) or m_data_item # Key updated
            st.session_state.active_sa_med_management_tab_v2 = "Add/Edit Medication"; st.rerun() # Key updated

        def toggle_status_action_fn(m_id_val=med_item_data['id'], current_active_status=med_item_data.get('is_active', True)):
            handle_sa_toggle_med_status(m_id_val, current_active_status, admin_user['id'])

        card_actions = {"Edit": edit_action_fn,
                        f"{'Deactivate' if med_item_data.get('is_active', True) else 'Activate'}": toggle_status_action_fn}
        MedicationCard(medication_data=med_item_data, actions=card_actions, key=f"sa_med_card_{med_item_data['id']}_v2") # Key updated
        st.markdown("---")

def render_sa_add_edit_medication_tab(admin_user: dict):
    if not st.session_state.sa_editing_med_id_v2: # Key updated
        st.info("Select 'Add New Medication' or 'Edit' a medication from the 'Manage Medications' tab to proceed.")
        if st.button("Back to Manage Medications", key="sa_med_back_to_mgt_v2"): # Key updated
            st.session_state.active_sa_med_management_tab_v2 = "Manage Medications"; st.rerun() # Key updated
        return

    is_new_med_mode = st.session_state.sa_editing_med_id_v2 == 'new' # Key updated
    header_txt = "Add New Medication to Database" if is_new_med_mode else f"Edit Medication: {st.session_state.sa_med_form_data_v2.get('name', '')}" # Key updated
    st.subheader(header_txt)

    med_form_component_sa = MedicationFormComponent(edit_mode=(not is_new_med_mode), medication_data=st.session_state.sa_med_form_data_v2, key_prefix="sa_med_edit_form_v2") # Key updated
    submitted_med_data = med_form_component_sa.render()

    if submitted_med_data:
        if submitted_med_data.get("cancelled"):
            show_info_message("Operation cancelled.")
            st.session_state.sa_editing_med_id_v2 = None; st.session_state.sa_med_form_data_v2 = {} # Keys updated
            st.session_state.active_sa_med_management_tab_v2 = "Manage Medications"; st.rerun() # Key updated
        elif is_new_med_mode: handle_sa_create_medication(submitted_med_data, admin_user['id'])
        else: handle_sa_update_medication(st.session_state.sa_editing_med_id_v2, submitted_med_data, admin_user['id']) # Key updated

# --- Main Page Function ---
def show_sa_medication_management_page():
    require_authentication()
    require_role_access([USER_ROLES['SUPER_ADMIN']])
    inject_css()
    st.markdown("<h1>💊 Medication Database Management (Admin)</h1>", unsafe_allow_html=True)

    admin = get_current_user()
    if not admin: show_error_message("Admin user data not found."); return

    # Initialize session state keys with _v2 suffix
    for key, default_val in [('sa_editing_med_id_v2', None), ('sa_med_form_data_v2', {}),
                             ('sa_med_search_term_v2', ""), ('sa_med_drug_class_filter_v2', "All"),
                             ('sa_med_status_filter_label_v2', "All"),
                             ('active_sa_med_management_tab_v2', "Manage Medications")]:
        if key not in st.session_state: st.session_state[key] = default_val

    tab_titles_list = ["Manage Medications", "Add/Edit Medication"]
    if st.session_state.sa_editing_med_id_v2:
        st.session_state.active_sa_med_management_tab_v2 = tab_titles_list[1]

    tabs_obj_list = st.tabs(tab_titles_list)

    with tabs_obj_list[0]: render_sa_manage_medications_tab(admin)
    with tabs_obj_list[1]: render_sa_add_edit_medication_tab(admin)

if __name__ == "__main__":
    if 'user' not in st.session_state:
        st.session_state.user = {'id': 'superadmin004', 'username': 'sa_medmaster_v2', 'role': USER_ROLES['SUPER_ADMIN'], 'full_name': 'Super Admin MedMaster V2'} # Updated details
        st.session_state.authenticated = True; st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)

    for key, default_val in [('sa_editing_med_id_v2', None), ('sa_med_form_data_v2', {}),
                             ('sa_med_search_term_v2', ""), ('sa_med_drug_class_filter_v2', "All"),
                             ('sa_med_status_filter_label_v2', "All"),
                             ('active_sa_med_management_tab_v2', "Manage Medications")]:
        if key not in st.session_state: st.session_state[key] = default_val

    if not COMPONENTS_AVAILABLE: st.sidebar.warning("Using MOCK UI components for SA Med Mgt.")
    if not DB_QUERIES_AVAILABLE: st.sidebar.warning("Using MOCK DB Queries for SA Med Mgt.")

    show_sa_medication_management_page()

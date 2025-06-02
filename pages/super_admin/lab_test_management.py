import streamlit as st
from datetime import datetime, timedelta
import copy

# Config and Auth
from config.settings import USER_ROLES, LAB_TEST_CONFIG # LAB_TEST_CONFIG for categories
from config.styles import inject_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access

# Components (with Mocks)
try:
    from components.forms import LabTestFormComponent # Assuming this will be created
    from components.forms import SearchFormComponent
    from components.cards import LabTestCard
    COMPONENTS_AVAILABLE = True
except ImportError:
    COMPONENTS_AVAILABLE = False
    # Mock SearchFormComponent
    class SearchFormComponent:
        def __init__(self, search_function=None,result_key_prefix=None,form_key=None,placeholder="Search...",label="Search",session_state_key="default_search_term",auto_submit=False,button_text="Search"):
            self.placeholder, self.label, self.session_state_key = placeholder, label, session_state_key
        def render(self):
            st.session_state[self.session_state_key] = st.text_input(self.label, value=st.session_state.get(self.session_state_key, ""), placeholder=self.placeholder, key=f"mock_search_sa_lab_mgt_{self.session_state_key}_v2") # Key updated
            return None
        def get_search_query(self): return st.session_state.get(self.session_state_key, "")

    # Define LabTestFormComponent inline as requested if not available
    class LabTestFormComponent:
        def __init__(self, edit_mode=False, lab_test_data=None, key_prefix="sa_lab_test_form", required_fields=None):
            self.edit_mode = edit_mode
            self.test_data = lab_test_data if lab_test_data else {}
            self.key_prefix = key_prefix
            self.required = required_fields or ['name', 'test_code', 'category', 'sample_type']
            # if not COMPONENTS_AVAILABLE: st.info("Using Mock LabTestFormComponent for SA Lab Test Mgt.") # In __main__

        def render(self):
            submitted_data = None
            with st.form(key=f"{self.key_prefix}_form_main_sa_lab_v2"): # Key updated
                form_data = {}
                form_data['name'] = st.text_input("Test Name*", value=self.test_data.get('name', ''), key=f"{self.key_prefix}_name_v2") # Key updated
                form_data['test_code'] = st.text_input("Test Code (e.g., CPT/LOINC)*", value=self.test_data.get('test_code', ''), key=f"{self.key_prefix}_code_v2") # Key updated

                default_categories = ["Hematology", "Chemistry", "Microbiology", "Endocrinology", "Other"]
                available_categories = LAB_TEST_CONFIG.get('CATEGORIES', default_categories)
                if not isinstance(available_categories, list) or not available_categories: available_categories = default_categories

                current_category_idx = 0
                if self.test_data.get('category') in available_categories:
                    current_category_idx = available_categories.index(self.test_data['category'])
                form_data['category'] = st.selectbox("Category*", options=available_categories, index=current_category_idx, key=f"{self.key_prefix}_cat_v2") # Key updated

                form_data['sample_type'] = st.text_input("Sample Type (e.g., Blood, Urine, Serum)*", value=self.test_data.get('sample_type', ''), key=f"{self.key_prefix}_sample_v2") # Key updated
                form_data['normal_range'] = st.text_area("Normal Range", value=self.test_data.get('normal_range', ''), key=f"{self.key_prefix}_range_v2") # Key updated
                form_data['units'] = st.text_input("Units", value=self.test_data.get('units', ''), key=f"{self.key_prefix}_units_v2") # Key updated
                form_data['cost'] = st.number_input("Cost ($)", value=float(self.test_data.get('cost', 0.0)), min_value=0.0, step=0.01, format="%.2f", key=f"{self.key_prefix}_cost_v2") # Key updated
                form_data['preparation_required'] = st.text_area("Preparation Required", value=self.test_data.get('preparation_required', 'None'), key=f"{self.key_prefix}_prep_v2") # Key updated
                form_data['description'] = st.text_area("Description / Clinical Significance", value=self.test_data.get('description', ''), key=f"{self.key_prefix}_desc_v2") # Key updated
                form_data['is_active'] = st.checkbox("Is Active in Database?", value=self.test_data.get('is_active', True), key=f"{self.key_prefix}_is_active_v2") # Key updated

                submit_label = "Update Lab Test" if self.edit_mode else "Add Lab Test to Database"
                col1, col2 = st.columns([3,1])
                if col1.form_submit_button(submit_label, use_container_width=True, type="primary"):
                    valid = True
                    for field in self.required:
                        if not form_data.get(field): valid = False; show_error_message(f"{field.replace('_',' ').title()} is required.")
                    if valid: submitted_data = form_data
                if col2.form_submit_button("Cancel", type="secondary", use_container_width=True):
                    submitted_data = {"cancelled": True}
            return submitted_data

    # Mock LabTestCard
    def LabTestCard(lab_test_data, actions, key, show_actions=True):
        status = "Active" if lab_test_data.get('is_active', True) else "Inactive"
        st.markdown(f"**{lab_test_data.get('name', 'N/A')} ({lab_test_data.get('test_code', 'N/A')})** - {status}")
        st.caption(f"Category: {lab_test_data.get('category', 'N/A')} | Sample: {lab_test_data.get('sample_type', 'N/A')}")
        if show_actions and actions:
            action_cols = st.columns(len(actions)) # Create columns for buttons
            for i, (action_label, action_func) in enumerate(actions.items()):
                if action_cols[i].button(action_label, key=f"{key}_{action_label.lower().replace(' ', '_')}_sa_lab_card_v2", use_container_width=True): action_func() # Key updated

# Database Queries (with Mocks)
try:
    from database.queries import LabTestQueries
    DB_QUERIES_AVAILABLE = True
except ImportError:
    DB_QUERIES_AVAILABLE = False
    MOCK_LAB_TESTS_DB_SA = [
        {'id': 'lt_sa_001', 'name': 'Complete Blood Count (CBC)', 'test_code': 'CBC001', 'category': LAB_TEST_CONFIG.get('CATEGORIES', ['Hematology'])[0], 'sample_type': 'Whole Blood', 'normal_range': 'Varies', 'units': '', 'cost': 25.00, 'preparation_required': 'None', 'description': 'General health screen', 'is_active': True, 'created_by': 'sa_godmode', 'created_at': datetime.now().isoformat()},
        {'id': 'lt_sa_002', 'name': 'Lipid Panel', 'test_code': 'LIPID01', 'category': LAB_TEST_CONFIG.get('CATEGORIES', ['Chemistry'])[1] if len(LAB_TEST_CONFIG.get('CATEGORIES', ['Chemistry'])) > 1 else 'Chemistry', 'sample_type': 'Serum', 'normal_range': 'TC < 200 mg/dL', 'units': 'mg/dL', 'cost': 40.00, 'preparation_required': 'Fasting 9-12 hours', 'description': 'Cardiovascular risk assessment', 'is_active': True, 'created_by': 'sa_godmode', 'created_at': (datetime.now() - timedelta(days=20)).isoformat()},
        {'id': 'lt_sa_003', 'name': 'Old Inactive Test', 'test_code': 'OLD00X', 'category': 'Other', 'sample_type': 'Varies', 'normal_range': '', 'units': '', 'cost': 10.00, 'preparation_required': '', 'description': 'No longer used.', 'is_active': False, 'created_by': 'sa_godmode', 'created_at': (datetime.now() - timedelta(days=200)).isoformat()},
    ]
    class LabTestQueries:
        @staticmethod
        def search_lab_tests(search_term=None, category=None, is_active=None):
            results = copy.deepcopy(MOCK_LAB_TESTS_DB_SA)
            if search_term: term = search_term.lower(); results = [lt for lt in results if term in lt['name'].lower() or term in lt.get('test_code','').lower()]
            if category and category != "All": results = [lt for lt in results if lt.get('category') == category]
            if is_active is not None: results = [lt for lt in results if lt.get('is_active') == is_active]
            return sorted(results, key=lambda x: x['name'])
        @staticmethod
        def get_lab_test_details(lab_test_id):
            return next((copy.deepcopy(lt) for lt in MOCK_LAB_TESTS_DB_SA if lt['id'] == lab_test_id), None)
        @staticmethod
        def create_lab_test(data, created_by_id):
            new_id = f"lt_sa_{len(MOCK_LAB_TESTS_DB_SA) + 1:03d}_{datetime.now().strftime('%S%f')}"
            new_test = {'id': new_id, **data, 'created_by': created_by_id, 'created_at': datetime.now().isoformat()}
            if 'is_active' not in new_test: new_test['is_active'] = True
            MOCK_LAB_TESTS_DB_SA.append(new_test)
            return new_test
        @staticmethod
        def update_lab_test(lab_test_id, data, updated_by_id):
            for i, lt_item in enumerate(MOCK_LAB_TESTS_DB_SA):
                if lt_item['id'] == lab_test_id:
                    MOCK_LAB_TESTS_DB_SA[i] = {**lt_item, **data, 'last_updated_by': updated_by_id, 'updated_at': datetime.now().isoformat()}
                    return MOCK_LAB_TESTS_DB_SA[i]
            return None
        @staticmethod
        def set_lab_test_status(lab_test_id, is_active_status, updated_by_id): # Renamed for clarity
            for i, lt_item in enumerate(MOCK_LAB_TESTS_DB_SA):
                if lt_item['id'] == lab_test_id:
                    MOCK_LAB_TESTS_DB_SA[i]['is_active'] = is_active_status
                    MOCK_LAB_TESTS_DB_SA[i]['last_updated_by'] = updated_by_id
                    MOCK_LAB_TESTS_DB_SA[i]['updated_at'] = datetime.now().isoformat()
                    return MOCK_LAB_TESTS_DB_SA[i]
            return None

# Utils
from utils.helpers import show_error_message, show_success_message, show_info_message

# --- Helper Functions for CRUD ---
def handle_sa_create_lab_test(data, admin_id):
    try:
        new_test = LabTestQueries.create_lab_test(data, created_by_id=admin_id)
        if new_test:
            show_success_message(f"Lab Test '{new_test['name']}' added (ID: {new_test['id']}).")
            st.session_state.sa_lab_test_form_data_v2 = {} # Key updated
            st.session_state.sa_editing_lab_test_id_v2 = None  # Key updated
            st.session_state.active_sa_lab_test_management_tab_v2 = "Manage Lab Tests"; st.rerun() # Key updated
        else: show_error_message("Failed to add lab test.")
    except Exception as e: show_error_message(f"Error: {e}")

def handle_sa_update_lab_test(test_id, data, admin_id):
    try:
        updated_test = LabTestQueries.update_lab_test(test_id, data, updated_by_id=admin_id)
        if updated_test:
            show_success_message(f"Lab Test '{updated_test['name']}' updated.")
            st.session_state.sa_editing_lab_test_id_v2 = None; st.session_state.sa_lab_test_form_data_v2 = {} # Keys updated
            st.session_state.active_sa_lab_test_management_tab_v2 = "Manage Lab Tests"; st.rerun() # Key updated
        else: show_error_message("Failed to update lab test.")
    except Exception as e: show_error_message(f"Error: {e}")

def handle_sa_toggle_lab_test_status(test_id, current_is_active, admin_id):
    try:
        updated_test = LabTestQueries.set_lab_test_status(test_id, not current_is_active, updated_by_id=admin_id)
        if updated_test:
            action = "activated" if updated_test['is_active'] else "deactivated"
            show_success_message(f"Lab Test '{updated_test['name']}' has been {action}.")
            st.rerun() # Refresh list
        else: show_error_message("Failed to toggle lab test status.")
    except Exception as e: show_error_message(f"Error: {e}")

# --- Tab Rendering Functions ---
def render_sa_manage_lab_tests_tab(admin_user: dict):
    st.subheader("Browse & Manage Central Lab Test Database")
    if st.button("➕ Add New Lab Test to Database", key="sa_add_new_lab_test_btn_v2"): # Key updated
        st.session_state.sa_editing_lab_test_id_v2 = 'new' # Key updated
        st.session_state.sa_lab_test_form_data_v2 = {'is_active': True}  # Key updated
        st.session_state.active_sa_lab_test_management_tab_v2 = "Add/Edit Lab Test" # Key updated
        st.rerun()
    st.markdown("---")

    search_form = SearchFormComponent(session_state_key="sa_lab_test_search_term_v2", label="Search by Name or Test Code:") # Key updated
    search_form.render()
    search_query = st.session_state.get("sa_lab_test_search_term_v2", "")

    filter_cols = st.columns(2)
    with filter_cols[0]:
        default_cats = LAB_TEST_CONFIG.get('DEFAULT_CATEGORIES', ["Other"]) # Use a config default or hardcoded
        cats_list = LAB_TEST_CONFIG.get('CATEGORIES', default_cats)
        if not isinstance(cats_list, list) or not cats_list: cats_list = default_cats
        all_cats_options = ["All"] + sorted(list(set(cats_list)))

        current_cat_filter = st.session_state.get('sa_lab_test_category_filter_v2', "All") # Key updated
        if current_cat_filter not in all_cats_options: current_cat_filter = "All"
        st.session_state.sa_lab_test_category_filter_v2 = st.selectbox("Filter by Category:", options=all_cats_options, index=all_cats_options.index(current_cat_filter), key="sa_lab_cat_filter_dd_v2") # Key updated
    with filter_cols[1]:
        status_options = {"All": None, "Active": True, "Inactive": False}
        current_status_label = st.session_state.get('sa_lab_test_status_filter_label_v2', "All") # Key updated
        st.session_state.sa_lab_test_status_filter_label_v2 = st.radio("Filter by Status:", options=list(status_options.keys()), index=list(status_options.keys()).index(current_status_label), horizontal=True, key="sa_lab_status_radio_v2") # Key updated

    if st.button("🔍 Apply Filters / Search", key="sa_apply_lab_filters_btn_v2"): st.rerun() # Key updated

    lab_tests_list_data = []
    try:
        is_active_val = status_options[st.session_state.sa_lab_test_status_filter_label_v2] # Key updated
        lab_tests_list_data = LabTestQueries.search_lab_tests(search_term=search_query, category=st.session_state.sa_lab_test_category_filter_v2, is_active=is_active_val) # Key updated
    except Exception as e: show_error_message(f"Error: {e}")

    st.caption(f"Displaying {len(lab_tests_list_data)} lab test(s).")
    if not lab_tests_list_data and (search_query or st.session_state.sa_lab_test_category_filter_v2 != "All" or st.session_state.sa_lab_test_status_filter_label_v2 != "All"): # Keys updated for filters
        st.info("No lab tests found matching current filters.")

    for lt_item_data in lab_tests_list_data:
        def edit_lt_action_fn(lt_data_item=lt_item_data):
            st.session_state.sa_editing_lab_test_id_v2 = lt_data_item['id'] # Key updated
            st.session_state.sa_lab_test_form_data_v2 = LabTestQueries.get_lab_test_details(lt_data_item['id']) or lt_data_item # Key updated
            st.session_state.active_sa_lab_test_management_tab_v2 = "Add/Edit Lab Test"; st.rerun() # Key updated

        def toggle_lt_status_action_fn(lt_id_val=lt_item_data['id'], current_active_status=lt_item_data.get('is_active', True)):
            handle_sa_toggle_lab_test_status(lt_id_val, current_active_status, admin_user['id'])

        lt_actions_dict = {"Edit": edit_lt_action_fn, f"{'Deactivate' if lt_item_data.get('is_active', True) else 'Activate'}": toggle_lt_status_action_fn}
        LabTestCard(lab_test_data=lt_item_data, actions=lt_actions_dict, key=f"sa_lt_card_{lt_item_data['id']}_v2") # Key updated
        st.markdown("---")

def render_sa_add_edit_lab_test_tab(admin_user: dict):
    if not st.session_state.sa_editing_lab_test_id_v2: # Key updated
        st.info("Select 'Add New Lab Test' or 'Edit' a lab test from the 'Manage Lab Tests' tab to proceed.")
        if st.button("Back to Manage Lab Tests", key="sa_lab_back_to_mgt_v2"): # Key updated
            st.session_state.active_sa_lab_test_management_tab_v2 = "Manage Lab Tests"; st.rerun() # Key updated
        return

    is_new_lt_mode_flag = st.session_state.sa_editing_lab_test_id_v2 == 'new' # Key updated
    header_text_val = "Add New Lab Test to Database" if is_new_lt_mode_flag else f"Edit Lab Test: {st.session_state.sa_lab_test_form_data_v2.get('name', '')}" # Key updated
    st.subheader(header_text_val)

    lt_form_sa_component = LabTestFormComponent(edit_mode=(not is_new_lt_mode_flag), lab_test_data=st.session_state.sa_lab_test_form_data_v2, key_prefix="sa_lab_edit_form_v2") # Key updated
    submitted_lt_data_val = lt_form_sa_component.render()

    if submitted_lt_data_val:
        if submitted_lt_data_val.get("cancelled"):
            show_info_message("Operation cancelled.")
            st.session_state.sa_editing_lab_test_id_v2 = None; st.session_state.sa_lab_test_form_data_v2 = {} # Keys updated
            st.session_state.active_sa_lab_test_management_tab_v2 = "Manage Lab Tests"; st.rerun() # Key updated
        elif is_new_lt_mode_flag: handle_sa_create_lab_test(submitted_lt_data_val, admin_user['id'])
        else: handle_sa_update_lab_test(st.session_state.sa_editing_lab_test_id_v2, submitted_lt_data_val, admin_user['id']) # Key updated

# --- Main Page Function ---
def show_sa_lab_test_management_page():
    require_authentication()
    require_role_access([USER_ROLES['SUPER_ADMIN']])
    inject_css()
    st.markdown("<h1>🧪 Lab Test Database Management (Admin)</h1>", unsafe_allow_html=True)

    admin = get_current_user()
    if not admin: show_error_message("Admin user data not found."); return

    # Initialize session state keys with _v2 suffix
    for key, default_val in [('sa_editing_lab_test_id_v2', None), ('sa_lab_test_form_data_v2', {}),
                             ('sa_lab_test_search_term_v2', ""), ('sa_lab_test_category_filter_v2', "All"),
                             ('sa_lab_test_status_filter_label_v2', "All"),
                             ('active_sa_lab_test_management_tab_v2', "Manage Lab Tests")]:
        if key not in st.session_state: st.session_state[key] = default_val

    tab_titles_list = ["Manage Lab Tests", "Add/Edit Lab Test"]
    if st.session_state.sa_editing_lab_test_id_v2:  # Key updated
        st.session_state.active_sa_lab_test_management_tab_v2 = tab_titles_list[1] # Key updated

    tabs_obj_list = st.tabs(tab_titles_list)
    with tabs_obj_list[0]: render_sa_manage_lab_tests_tab(admin)
    with tabs_obj_list[1]: render_sa_add_edit_lab_test_tab(admin)

if __name__ == "__main__":
    if 'user' not in st.session_state:
        st.session_state.user = {'id': 'superadmin006', 'username': 'sa_labmaster_v2', 'role': USER_ROLES['SUPER_ADMIN'], 'full_name': 'Super Admin LabMaster V2'} # Updated details
        st.session_state.authenticated = True; st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)

    for key, default_val in [('sa_editing_lab_test_id_v2', None), ('sa_lab_test_form_data_v2', {}),
                             ('sa_lab_test_search_term_v2', ""), ('sa_lab_test_category_filter_v2', "All"),
                             ('sa_lab_test_status_filter_label_v2', "All"),
                             ('active_sa_lab_test_management_tab_v2', "Manage Lab Tests")]: # Key updated
        if key not in st.session_state: st.session_state[key] = default_val

    if not COMPONENTS_AVAILABLE: st.sidebar.warning("Using MOCK UI components for SA Lab Test Mgt.")
    if not DB_QUERIES_AVAILABLE: st.sidebar.warning("Using MOCK DB Queries for SA Lab Test Mgt.")

    show_sa_lab_test_management_page()

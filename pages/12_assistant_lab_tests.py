import streamlit as st
from datetime import datetime, timedelta
import copy

# Config and Auth
from config.settings import USER_ROLES, LAB_TEST_CONFIG
from config.styles import inject_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access

# Components
try:
    from components.cards import LabTestCard
    from components.forms import SearchFormComponent
    COMPONENTS_AVAILABLE = True
except ImportError:
    COMPONENTS_AVAILABLE = False
    # Mock SearchFormComponent
    class SearchFormComponent: 
        def __init__(self, search_function=None, result_key_prefix=None, form_key=None, placeholder="Search...", label="Search", session_state_key="default_search_term", auto_submit=False, button_text="Search"):
            self.placeholder, self.label, self.session_state_key = placeholder, label, session_state_key
        def render(self): 
            st.session_state[self.session_state_key] = st.text_input(self.label, value=st.session_state.get(self.session_state_key, ""), placeholder=self.placeholder, key=f"mock_search_asst_lab_{self.session_state_key}_v2")
            return None 
        def get_search_query(self): return st.session_state.get(self.session_state_key, "")

    # Mock LabTestCard - simplified for assistant view
    def LabTestCard(lab_test_data, actions=None, key=None, show_actions=True): 
        st.markdown(f"**{lab_test_data.get('name', 'N/A')}**")
        st.caption(f"Category: {lab_test_data.get('category', 'N/A')} | Specimen: {lab_test_data.get('specimen_type', 'N/A')}")
        if show_actions and actions: # This part won't be used for assistant if actions=None or show_actions=False
             for action_label, action_func in actions.items():
                if st.button(action_label, key=f"{key}_{action_label.lower().replace(' ', '_')}_asst_lab_card_v2"):
                    action_func()
        with st.expander("More Info (Mock)", expanded=False): # Default to collapsed for assistant
            st.write(f"**Description:** {lab_test_data.get('description', 'N/A')}")
            st.write(f"**Turnaround Time:** {lab_test_data.get('turnaround_time', 'N/A')}")
            st.write(f"**Preparation:** {lab_test_data.get('preparation_instructions', 'N/A')}")


# Database Queries (with Mocks)
try:
    from database.queries import LabTestQueries
    DB_QUERIES_AVAILABLE = True
except ImportError:
    DB_QUERIES_AVAILABLE = False
    MOCK_LAB_TESTS_STORE_ASST = [
        {'id': 'lab001', 'name': 'Complete Blood Count (CBC)', 'category': 'Hematology', 'specimen_type': 'Whole blood', 'turnaround_time': '2-4 hours', 'description': 'Measures different components of blood.', 'preparation_instructions': 'None typically required.'},
        {'id': 'lab002', 'name': 'Lipid Panel', 'category': 'Chemistry', 'specimen_type': 'Serum', 'turnaround_time': '4-6 hours', 'description': 'Measures cholesterol and triglycerides.', 'preparation_instructions': '9-12 hour fast recommended.'},
        {'id': 'lab003', 'name': 'Urinalysis (UA)', 'category': 'Microbiology', 'specimen_type': 'Urine', 'turnaround_time': '1-3 hours', 'description': 'Screens for various substances in urine.', 'preparation_instructions': 'Clean catch midstream sample preferred.'},
        {'id': 'lab004', 'name': 'TSH (Thyroid Stimulating Hormone)', 'category': 'Endocrinology', 'specimen_type': 'Serum', 'turnaround_time': '24 hours', 'description': 'Assesses thyroid function.', 'preparation_instructions': 'None.'},
        {'id': 'lab005', 'name': 'Glucose, Fasting', 'category': 'Chemistry', 'specimen_type': 'Plasma', 'turnaround_time': '1-2 hours', 'description': 'Measures blood sugar levels after fasting.', 'preparation_instructions': '8-10 hour fast required.'},
    ]
    class LabTestQueries:
        @staticmethod
        def search_lab_tests(search_term=None, category=None):
            results = copy.deepcopy(MOCK_LAB_TESTS_STORE_ASST)
            if search_term:
                term = search_term.lower()
                results = [lt for lt in results if term in lt['name'].lower() or term in lt.get('description','').lower()]
            if category and category != "All":
                results = [lt for lt in results if lt.get('category') == category]
            return results

# Utils
from utils.helpers import show_error_message, show_success_message, show_warning_message

# --- UI Rendering Functions ---
def render_assistant_lab_test_search():
    st.subheader("🔍 Search & Filter Lab Tests")
    
    search_form = SearchFormComponent(session_state_key="asst_lab_search_term_v2", label="Search by Name or Description:")
    search_form.render()

    filter_cols = st.columns([2, 1])
    with filter_cols[0]:
        default_categories = ["Hematology", "Chemistry", "Microbiology", "Endocrinology", "Immunology", "Pathology", "Other"]
        config_categories = LAB_TEST_CONFIG.get('CATEGORIES', default_categories)
        if not isinstance(config_categories, list) or not config_categories:
            available_categories = default_categories
        else:
            available_categories = config_categories
            
        all_category_options = ["All"] + sorted(list(set(available_categories)))
        
        current_category = st.session_state.get('asst_lab_category_v2', "All")
        if current_category not in all_category_options: current_category_index = 0
        else: current_category_index = all_category_options.index(current_category)
        
        st.session_state.asst_lab_category_v2 = st.selectbox(
            "Filter by Test Category:", 
            options=all_category_options, 
            index=current_category_index,
            key="asst_lab_category_filter_v2"
        )
    with filter_cols[1]:
        st.markdown("<div>&nbsp;</div>", unsafe_allow_html=True) 
        if st.button("🔄 Refresh / Apply", key="asst_lab_refresh_btn_v2", use_container_width=True):
            st.rerun()
    st.markdown("---")

def render_assistant_lab_tests_list():
    st.subheader("Lab Test Listings")
    
    search_term_val = st.session_state.get('asst_lab_search_term_v2', "")
    category_filter_val = st.session_state.get('asst_lab_category_v2', "All")

    try:
        lab_tests_data = LabTestQueries.search_lab_tests(
            search_term=search_term_val, 
            category=category_filter_val
        )
    except AttributeError: 
        show_warning_message("Lab Test query service initializing. Using mock data.", icon="⚠️")
        lab_tests_data = LabTestQueries.search_lab_tests(search_term_val, category_filter_val)
    except Exception as e:
        show_error_message(f"Error fetching lab tests: {e}")
        lab_tests_data = []

    if not lab_tests_data:
        st.info("No lab tests found matching your criteria.")
        return

    num_cols = 3 
    item_cols = st.columns(num_cols)
    for i, test_data_item in enumerate(lab_tests_data):
        with item_cols[i % num_cols]:
            try:
                # For assistants, show_actions=False ensures no interactive elements are displayed.
                LabTestCard(lab_test_data=test_data_item, actions=None, key=f"asst_lab_card_{test_data_item['id']}_v2", show_actions=False)
            except TypeError: # Fallback if the card component doesn't support 'show_actions'
                 LabTestCard(lab_test_data=test_data_item, key=f"asst_lab_card_{test_data_item['id']}_alt_v2")
            except Exception as e:
                st.error(f"Error rendering card for {test_data_item.get('name')}: {e}")
                st.json(test_data_item)

# --- Main Page Function ---
def show_assistant_lab_tests_page():
    require_authentication()
    require_role_access([USER_ROLES['ASSISTANT']])
    inject_css()

    st.markdown("<h1>🧪 Lab Tests Database (Assistant View)</h1>", unsafe_allow_html=True)
    st.caption("This is a read-only view of the lab tests database.")
    
    if 'asst_lab_search_term_v2' not in st.session_state: st.session_state.asst_lab_search_term_v2 = ""
    if 'asst_lab_category_v2' not in st.session_state: st.session_state.asst_lab_category_v2 = "All"

    render_assistant_lab_test_search()
    render_assistant_lab_tests_list()

if __name__ == "__main__":
    if 'user' not in st.session_state:
        st.session_state.user = {
            'id': 'asstLabBrowser008', 'username': 'asst_labview008', 
            'role': USER_ROLES['ASSISTANT'], 'full_name': 'Alex LabView (Med Asst)',
            'email': 'alex.medasst.labview@example.com' # Unique email
        }
        st.session_state.authenticated = True
        st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)

    if 'asst_lab_search_term_v2' not in st.session_state: st.session_state.asst_lab_search_term_v2 = ""
    if 'asst_lab_category_v2' not in st.session_state: st.session_state.asst_lab_category_v2 = "All"
    
    if not COMPONENTS_AVAILABLE: st.sidebar.warning("Using MOCK UI components for Asst. Lab Tests.")
    if not DB_QUERIES_AVAILABLE: st.sidebar.warning("Using MOCK DB Queries for Asst. Lab Tests.")

    # show_assistant_lab_tests_page() # Called at module level now

# This call ensures Streamlit runs the page content when navigating
show_assistant_lab_tests_page()

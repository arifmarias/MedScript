import streamlit as st
from datetime import datetime, timedelta
import copy

# Config and Auth
from config.settings import USER_ROLES, LAB_TEST_CONFIG
from config.styles import inject_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access

# Components
from components.cards import LabTestCard # Assuming this component exists
from components.forms import SearchFormComponent # Assuming this component exists

# Database & Services
from database.queries import LabTestQueries # Assuming this exists

# Utils
from utils.helpers import show_error_message, show_success_message, show_warning_message

# --- Mock Data Store ---
MOCK_LAB_TESTS_DB = [
    {'id': 'lab001', 'name': 'Complete Blood Count (CBC)', 'category': 'Hematology', 'specimen_type': 'Whole blood', 'turnaround_time': '2-4 hours', 'reference_range': 'Varies by parameter', 'description': 'Measures different components of blood.', 'preparation_instructions': 'None typically required.'},
    {'id': 'lab002', 'name': 'Lipid Panel', 'category': 'Chemistry', 'specimen_type': 'Serum', 'turnaround_time': '4-6 hours', 'reference_range': 'TC <200mg/dL, LDL <100mg/dL, HDL >40mg/dL', 'description': 'Measures cholesterol and triglycerides.', 'preparation_instructions': '9-12 hour fast recommended.'},
    {'id': 'lab003', 'name': 'Urinalysis (UA)', 'category': 'Microbiology', 'specimen_type': 'Urine', 'turnaround_time': '1-3 hours', 'reference_range': 'Varies', 'description': 'Screens for various substances in urine.', 'preparation_instructions': 'Clean catch midstream sample preferred.'},
    {'id': 'lab004', 'name': 'Thyroid Stimulating Hormone (TSH)', 'category': 'Endocrinology', 'specimen_type': 'Serum', 'turnaround_time': '24 hours', 'reference_range': '0.4-4.0 mIU/L', 'description': 'Screens for thyroid disorders.', 'preparation_instructions': 'None typically required.'},
    {'id': 'lab005', 'name': 'Basic Metabolic Panel (BMP)', 'category': 'Chemistry', 'specimen_type': 'Serum', 'turnaround_time': '2-4 hours', 'reference_range': 'Varies by parameter', 'description': 'Measures electrolytes, kidney function, blood sugar.', 'preparation_instructions': 'Fasting may be required for glucose.'},
    {'id': 'lab006', 'name': 'Hemoglobin A1c (HbA1c)', 'category': 'Endocrinology', 'specimen_type': 'Whole blood', 'turnaround_time': '24-48 hours', 'reference_range': '<5.7% (non-diabetic)', 'description': 'Average blood glucose over past 2-3 months.', 'preparation_instructions': 'None typically required.'}
]

def get_mock_lab_tests(search_term: str, category: str):
    results = copy.deepcopy(MOCK_LAB_TESTS_DB)

    if search_term:
        search_term_lower = search_term.lower()
        results = [
            lt for lt in results if
            search_term_lower in lt['name'].lower() or
            search_term_lower in lt.get('description', '').lower()
        ]

    if category != "All":
        results = [lt for lt in results if lt.get('category') == category]

    return results

# --- UI Rendering Functions ---
def render_lab_test_search_and_filters():
    st.subheader("🔍 Search & Filter Lab Tests")

    st.session_state.lab_search_term = st.text_input(
        "Search by Name or Description:",
        value=st.session_state.get('lab_search_term', ""),
        key="lab_search_input_main_v2" # Changed key to avoid conflict if old one is stuck
    )

    filter_cols = st.columns([2, 1])
    with filter_cols[0]:
        default_categories = ["Hematology", "Chemistry", "Microbiology", "Endocrinology", "Immunology", "Pathology"]
        # Use LAB_TEST_CONFIG if available and is a list, otherwise use default
        config_categories = LAB_TEST_CONFIG.get('CATEGORIES', default_categories)
        if not isinstance(config_categories, list) or not config_categories:
            available_categories = default_categories
        else:
            available_categories = config_categories

        all_category_options = ["All"] + sorted(list(set(available_categories)))

        current_category = st.session_state.get('lab_test_category', "All")
        if current_category not in all_category_options:
            current_category_index = 0
        else:
            current_category_index = all_category_options.index(current_category)

        st.session_state.lab_test_category = st.selectbox(
            "Filter by Test Category:",
            options=all_category_options,
            index=current_category_index,
            key="lab_category_filter_main_v2" # Changed key
        )
    with filter_cols[1]:
        st.markdown("<div>&nbsp;</div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh / Apply", key="lab_refresh_btn_main_v2", use_container_width=True): # Changed key
            st.rerun()

    st.markdown("---")


def render_lab_tests_list():
    st.subheader("Lab Test Listings")

    search_term = st.session_state.get('lab_search_term', "")
    category_filter = st.session_state.get('lab_test_category', "All")

    try:
        # lab_tests_list_data = LabTestQueries.search_lab_tests(
        #     search_term=search_term,
        #     category=category_filter if category_filter != "All" else None,
        # ) # Actual
        lab_tests_list_data = get_mock_lab_tests(search_term, category_filter) # Mock
    except AttributeError:
        show_warning_message("Lab Test query service initializing. Using mock data.", icon="⚠️")
        lab_tests_list_data = get_mock_lab_tests(search_term, category_filter)
    except Exception as e:
        show_error_message(f"Error fetching lab tests: {e}")
        lab_tests_list_data = []

    if not lab_tests_list_data:
        st.info("No lab tests found matching your criteria. Try adjusting your search or filters.")
        return

    num_columns = 3
    item_cols = st.columns(num_columns)
    for i, test_item_data_obj in enumerate(lab_tests_list_data):
        with item_cols[i % num_columns]:
            card_actions = {
                "View Details": lambda t_name=test_item_data_obj['name']: st.toast(f"Details for {t_name} (placeholder).")
            }
            try:
                LabTestCard(lab_test_data=test_item_data_obj, actions=card_actions, key=f"lab_test_card_{test_item_data_obj['id']}")
            except Exception as e:
                st.error(f"Error rendering card for {test_item_data_obj.get('name')}: {e}")
                st.json(test_item_data_obj)


# --- Main Page Function ---
def show_lab_tests_page():
    require_authentication()
    require_role_access([USER_ROLES['DOCTOR']])
    inject_css()

    st.markdown("<h1>🧪 Lab Tests Database</h1>", unsafe_allow_html=True)

    if 'lab_search_term' not in st.session_state: st.session_state.lab_search_term = ""
    if 'lab_test_category' not in st.session_state: st.session_state.lab_test_category = "All"

    render_lab_test_search_and_filters()
    render_lab_tests_list()

if __name__ == "__main__":
    if 'user' not in st.session_state:
        st.session_state.user = {
            'id': 'docLabBrowser',
            'username': 'dr_labsearch',
            'role': USER_ROLES['DOCTOR'],
            'full_name': 'Dr. Lab Browser',
            'email': 'dr.labs@example.com'
        }
        st.session_state.authenticated = True
        st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)

    if 'lab_search_term' not in st.session_state: st.session_state.lab_search_term = ""
    if 'lab_test_category' not in st.session_state: st.session_state.lab_test_category = "All"

    show_lab_tests_page()

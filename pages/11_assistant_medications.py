import streamlit as st
from datetime import datetime, timedelta
import copy

# Config and Auth
from config.settings import USER_ROLES, DRUG_CLASSES
from config.styles import inject_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access

# Components
try:
    from components.cards import MedicationCard
    from components.forms import SearchFormComponent
    COMPONENTS_AVAILABLE = True
except ImportError:
    COMPONENTS_AVAILABLE = False
    # Mock SearchFormComponent
    class SearchFormComponent: 
        def __init__(self, search_function=None, result_key_prefix=None, form_key=None, placeholder="Search...", label="Search", session_state_key="default_search_term", auto_submit=False, button_text="Search"):
            self.placeholder, self.label, self.session_state_key = placeholder, label, session_state_key
        def render(self): 
            st.session_state[self.session_state_key] = st.text_input(self.label, value=st.session_state.get(self.session_state_key, ""), placeholder=self.placeholder, key=f"mock_search_asst_med_{self.session_state_key}_v2")
            return None 
        def get_search_query(self): return st.session_state.get(self.session_state_key, "")

    # Mock MedicationCard - simplified for assistant view (no favorite actions)
    def MedicationCard(medication_data, actions=None, key=None, show_actions=True): # show_actions default True but we will pass False
        st.markdown(f"**{medication_data.get('name', 'N/A')}**")
        st.caption(f"Generic: {medication_data.get('generic_name', 'N/A')} | Class: {medication_data.get('drug_class', 'N/A')}")
        st.caption(f"Form: {medication_data.get('form', 'N/A')} | Strength: {medication_data.get('strength', 'N/A')}")
        if show_actions and actions: # Will be False for assistant
            for action_label, action_func in actions.items(): # This loop won't run if actions is None or show_actions is False
                if st.button(action_label, key=f"{key}_{action_label.lower().replace(' ', '_')}_asst_med_card_v2"):
                    action_func()
        with st.expander("More Info (Mock)", expanded=False):
            st.write(f"**Indications:** {', '.join(medication_data.get('indications', ['N/A']))}")
            st.write(f"**Notes:** {medication_data.get('notes', 'N/A')}")


# Database Queries (with Mocks)
try:
    from database.queries import MedicationQueries
    DB_QUERIES_AVAILABLE = True
except ImportError:
    DB_QUERIES_AVAILABLE = False
    MOCK_MEDS_STORE_ASST = [ 
        {'id': 'med001', 'name': 'Amoxicillin 250mg', 'generic_name': 'Amoxicillin', 'drug_class': 'Penicillin Antibiotics', 'form': 'Capsule', 'strength': '250mg', 'indications': ['Bacterial infections'], 'notes': 'Complete full course.'},
        {'id': 'med002', 'name': 'Paracetamol 500mg', 'generic_name': 'Acetaminophen', 'drug_class': 'Analgesics', 'form': 'Tablet', 'strength': '500mg', 'indications': ['Pain relief', 'Fever reduction'], 'notes': 'Max 4g/day.'},
        {'id': 'med003', 'name': 'Lisinopril 10mg', 'generic_name': 'Lisinopril', 'drug_class': 'ACE Inhibitors', 'form': 'Tablet', 'strength': '10mg', 'indications': ['Hypertension'], 'notes': 'Monitor blood pressure.'},
        {'id': 'med004', 'name': 'Metformin 500mg', 'generic_name': 'Metformin', 'drug_class': 'Biguanides', 'form': 'Tablet', 'strength': '500mg', 'indications': ['Type 2 Diabetes'], 'notes': 'Take with meals.'},
        {'id': 'med005', 'name': 'Ibuprofen 200mg', 'generic_name': 'Ibuprofen', 'drug_class': 'NSAIDs', 'form': 'Tablet', 'strength': '200mg', 'indications': ['Pain', 'Inflammation'], 'notes': 'Take with food.'},
    ]
    class MedicationQueries:
        @staticmethod
        def search_medications(search_term=None, drug_class=None, favorites_only=None, doctor_id=None): 
            results = copy.deepcopy(MOCK_MEDS_STORE_ASST)
            if search_term:
                term = search_term.lower()
                results = [m for m in results if term in m['name'].lower() or term in m.get('generic_name','').lower()]
            if drug_class and drug_class != "All":
                results = [m for m in results if m.get('drug_class') == drug_class]
            return results

# Utils
from utils.helpers import show_error_message, show_success_message, show_warning_message

# --- UI Rendering Functions ---
def render_assistant_medication_search():
    st.subheader("🔍 Search & Filter Medications")
    
    search_form = SearchFormComponent(session_state_key="asst_med_search_term_v2", label="Search by Name or Generic Name:")
    search_form.render()

    filter_cols = st.columns([2, 1])
    with filter_cols[0]:
        available_drug_classes = DRUG_CLASSES if isinstance(DRUG_CLASSES, list) and DRUG_CLASSES else ["Analgesics", "Antibiotics", "NSAIDs", "ACE Inhibitors", "Biguanides", "Penicillin Antibiotics", "Other"]
        all_drug_classes_options = ["All"] + sorted(list(set(available_drug_classes)))
        
        current_drug_class = st.session_state.get('asst_med_drug_class_v2', "All")
        if current_drug_class not in all_drug_classes_options: current_drug_class_index = 0
        else: current_drug_class_index = all_drug_classes_options.index(current_drug_class)
        
        st.session_state.asst_med_drug_class_v2 = st.selectbox(
            "Filter by Drug Class:", 
            options=all_drug_classes_options, 
            index=current_drug_class_index,
            key="asst_med_drug_class_filter_v2"
        )
    with filter_cols[1]:
        st.markdown("<div>&nbsp;</div>", unsafe_allow_html=True) 
        if st.button("🔄 Refresh / Apply", key="asst_med_refresh_btn_v2", use_container_width=True):
            st.rerun()
    st.markdown("---")

def render_assistant_medications_list():
    st.subheader("Medication Listings")
    
    search_term_val = st.session_state.get('asst_med_search_term_v2', "")
    drug_class_filter_val = st.session_state.get('asst_med_drug_class_v2', "All")

    try:
        medications_data = MedicationQueries.search_medications(
            search_term=search_term_val, 
            drug_class=drug_class_filter_val
        )
    except AttributeError: 
        show_warning_message("Medication query service initializing. Using mock data.", icon="⚠️")
        medications_data = MedicationQueries.search_medications(search_term_val, drug_class_filter_val)
    except Exception as e:
        show_error_message(f"Error fetching medications: {e}")
        medications_data = []

    if not medications_data:
        st.info("No medications found matching your criteria.")
        return

    num_cols = 3 
    item_cols = st.columns(num_cols)
    for i, med_data_item in enumerate(medications_data):
        with item_cols[i % num_cols]:
            # For assistants, no favorite actions. Details can be a placeholder or a simple expander.
            # The MedicationCard mock handles the 'show_actions=False' implicitly by not showing fav buttons.
            # If a real MedicationCard is used, it needs to respect show_actions=False or have a mode for assistants.
            try:
                MedicationCard(medication_data=med_data_item, actions=None, key=f"asst_med_card_{med_data_item['id']}_v2", show_actions=False)
            except TypeError: 
                 MedicationCard(medication_data=med_data_item, key=f"asst_med_card_{med_data_item['id']}_alt_v2") # Try without show_actions if TypeError
            except Exception as e:
                st.error(f"Error rendering card for {med_data_item.get('name')}: {e}")
                st.json(med_data_item)

# --- Main Page Function ---
def show_assistant_medications_page():
    require_authentication()
    require_role_access([USER_ROLES['ASSISTANT']])
    inject_css()

    st.markdown("<h1>💊 Medications Database (Assistant View)</h1>", unsafe_allow_html=True)
    st.caption("This is a read-only view of the medications database. Contact a doctor or pharmacist for detailed advice.")
    
    if 'asst_med_search_term_v2' not in st.session_state: st.session_state.asst_med_search_term_v2 = ""
    if 'asst_med_drug_class_v2' not in st.session_state: st.session_state.asst_med_drug_class_v2 = "All"

    render_assistant_medication_search()
    render_assistant_medications_list()

if __name__ == "__main__":
    if 'user' not in st.session_state:
        st.session_state.user = {
            'id': 'asstMedBrowser007', 'username': 'asst_medview007', 
            'role': USER_ROLES['ASSISTANT'], 'full_name': 'Alex View (Med Asst)',
            'email': 'alex.medasst.view@example.com'
        }
        st.session_state.authenticated = True
        st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)

    if 'asst_med_search_term_v2' not in st.session_state: st.session_state.asst_med_search_term_v2 = ""
    if 'asst_med_drug_class_v2' not in st.session_state: st.session_state.asst_med_drug_class_v2 = "All"
    
    if not COMPONENTS_AVAILABLE: st.sidebar.warning("Using MOCK UI components for Asst. Medications.")
    if not DB_QUERIES_AVAILABLE: st.sidebar.warning("Using MOCK DB Queries for Asst. Medications.")

    # show_assistant_medications_page() # Called at module level now

# This call ensures Streamlit runs the page content when navigating
show_assistant_medications_page()

import streamlit as st
from datetime import datetime, timedelta
import copy

# Config and Auth
from config.settings import USER_ROLES, DRUG_CLASSES
from config.styles import inject_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access

# Components
from components.cards import MedicationCard # Assuming this component exists
from components.forms import SearchFormComponent # Assuming this component exists

# Database & Services
from database.queries import MedicationQueries # Assuming this exists

# Utils
from utils.helpers import show_error_message, show_success_message, show_warning_message

# --- Mock Data Store ---
MOCK_MEDICATIONS_DB = [
    {'id': 'med001', 'name': 'Amoxicillin 250mg', 'generic_name': 'Amoxicillin', 'drug_class': 'Penicillin Antibiotics', 'form': 'Capsule', 'strength': '250mg', 'manufacturer': 'Generic Pharma', 'indications': ['Bacterial infections'], 'contraindications': ['Penicillin allergy'], 'is_otc': False, 'storage_conditions': 'Room temperature', 'notes': 'Complete full course.', 'created_by': 'system'},
    {'id': 'med002', 'name': 'Paracetamol 500mg', 'generic_name': 'Acetaminophen', 'drug_class': 'Analgesics', 'form': 'Tablet', 'strength': '500mg', 'manufacturer': 'HealthWell', 'indications': ['Pain relief', 'Fever reduction'], 'contraindications': ['Severe liver disease'], 'is_otc': True, 'storage_conditions': 'Room temperature', 'notes': 'Max 4g/day.', 'created_by': 'system'},
    {'id': 'med003', 'name': 'Lisinopril 10mg', 'generic_name': 'Lisinopril', 'drug_class': 'ACE Inhibitors', 'form': 'Tablet', 'strength': '10mg', 'manufacturer': 'CardioCare', 'indications': ['Hypertension', 'Heart failure'], 'contraindications': ['Angioedema history'], 'is_otc': False, 'storage_conditions': 'Room temperature', 'notes': 'Monitor blood pressure.', 'created_by': 'system'},
    {'id': 'med004', 'name': 'Metformin 500mg', 'generic_name': 'Metformin', 'drug_class': 'Biguanides', 'form': 'Tablet', 'strength': '500mg', 'manufacturer': 'Generic Pharma', 'indications': ['Type 2 Diabetes'], 'contraindications': ['Renal dysfunction'], 'is_otc': False, 'storage_conditions': 'Room temperature', 'notes': 'Take with meals.', 'created_by': 'system'},
    {'id': 'med005', 'name': 'Salbutamol Inhaler 100mcg', 'generic_name': 'Albuterol', 'drug_class': 'Bronchodilators', 'form': 'Inhaler', 'strength': '100mcg/puff', 'manufacturer': 'RespiraWell', 'indications': ['Asthma', 'COPD'], 'contraindications': [], 'is_otc': False, 'storage_conditions': 'Room temperature', 'notes': 'For acute attacks.', 'created_by': 'system'},
    {'id': 'med006', 'name': 'Ibuprofen 200mg', 'generic_name': 'Ibuprofen', 'drug_class': 'NSAIDs', 'form': 'Tablet', 'strength': '200mg', 'manufacturer': 'PainFree Ltd.', 'indications': ['Pain', 'Inflammation', 'Fever'], 'contraindications': ['Active peptic ulcer'], 'is_otc': True, 'storage_conditions': 'Room temperature', 'notes': 'Take with food.', 'created_by': 'system'}
]
MOCK_FAVORITE_MEDS = {} # doctor_id: {med_id1, med_id2}

def get_mock_medications(search_term: str, drug_class: str, favorites_only: bool, doctor_id: str):
    results = copy.deepcopy(MOCK_MEDICATIONS_DB) # Start with a fresh copy
    doctor_favorites = MOCK_FAVORITE_MEDS.get(doctor_id, set())

    if search_term:
        search_term_lower = search_term.lower()
        results = [
            m for m in results if
            search_term_lower in m['name'].lower() or
            search_term_lower in m.get('generic_name','').lower()
        ]

    if drug_class != "All": # Assuming "All" means no filter by drug class
        results = [m for m in results if m.get('drug_class') == drug_class]

    # Add 'is_favorite' status before filtering by favorites_only
    for med in results:
        med['is_favorite'] = med['id'] in doctor_favorites

    if favorites_only:
        results = [m for m in results if m['is_favorite']]

    return results

def mock_toggle_favorite_medication(medication_id: str, doctor_id: str):
    if doctor_id not in MOCK_FAVORITE_MEDS:
        MOCK_FAVORITE_MEDS[doctor_id] = set()

    is_currently_favorite = medication_id in MOCK_FAVORITE_MEDS[doctor_id]

    if is_currently_favorite:
        MOCK_FAVORITE_MEDS[doctor_id].remove(medication_id)
        return False # Was favorite, now not
    else:
        MOCK_FAVORITE_MEDS[doctor_id].add(medication_id)
        return True # Was not favorite, now is

# --- Service Call Handlers ---
def handle_toggle_favorite(medication_id: str, doctor_id: str, is_currently_favorite: bool):
    try:
        # success = MedicationQueries.toggle_favorite_medication(medication_id, doctor_id, not is_currently_favorite) # Actual
        # The mock function itself toggles, so we just call it.
        new_fav_status = mock_toggle_favorite_medication(medication_id, doctor_id)
        action = "added to" if new_fav_status else "removed from"
        show_success_message(f"Medication {action} favorites.")
    except AttributeError:
        show_warning_message("Medication query service not available. Using mock toggle.")
        new_fav_status = mock_toggle_favorite_medication(medication_id, doctor_id)
        action = "added to" if new_fav_status else "removed from"
        show_success_message(f"Medication {action} favorites (mock).")
    except Exception as e:
        show_error_message(f"Error updating favorite status: {e}")

    st.rerun() # Rerun to reflect changes immediately


# --- UI Rendering Functions ---
def render_medication_search_and_filters():
    st.subheader("🔍 Search & Filter Medications")

    # For SearchFormComponent, it would typically manage its own state and return search term
    # For simplicity here, using st.text_input directly with session_state
    st.session_state.med_search_term = st.text_input(
        "Search by Name or Generic Name:",
        value=st.session_state.get('med_search_term', ""),
        key="med_search_input_main"
    )

    # Filters in columns
    filter_cols = st.columns([2, 1, 1])
    with filter_cols[0]:
        # Ensure DRUG_CLASSES is a list, provide a default if not.
        available_drug_classes = DRUG_CLASSES if isinstance(DRUG_CLASSES, list) else ["Analgesics", "Antibiotics", "NSAIDs", "ACE Inhibitors", "Bronchodilators", "Biguanides", "Penicillin Antibiotics"]
        all_drug_classes_options = ["All"] + sorted(list(set(available_drug_classes))) # Ensure unique and sorted

        current_drug_class = st.session_state.get('med_drug_class', "All")
        if current_drug_class not in all_drug_classes_options: # Handle case where saved class is no longer valid
            current_drug_class_index = 0 # Default to "All"
        else:
            current_drug_class_index = all_drug_classes_options.index(current_drug_class)

        st.session_state.med_drug_class = st.selectbox(
            "Filter by Drug Class:",
            options=all_drug_classes_options,
            index=current_drug_class_index,
            key="med_drug_class_filter_main"
        )
    with filter_cols[1]:
        st.session_state.med_show_favorites = st.checkbox(
            "Show Only My Favorites ⭐",
            value=st.session_state.get('med_show_favorites', False),
            key="med_favorites_filter_main"
        )
    with filter_cols[2]:
        # Vertical alignment for the button if possible, or just ensure it's placed neatly
        st.markdown("<div>&nbsp;</div>", unsafe_allow_html=True) # Spacer for alignment
        if st.button("🔄 Refresh / Apply", key="med_refresh_btn_main", use_container_width=True):
            st.rerun()

    st.markdown("---")


def render_medications_list():
    st.subheader("Medication Listings")
    doctor = get_current_user()
    if not doctor:
        show_error_message("Doctor information not found. Please log in again.")
        return

    search_term = st.session_state.get('med_search_term', "")
    drug_class_filter = st.session_state.get('med_drug_class', "All")
    favorites_only_filter = st.session_state.get('med_show_favorites', False)

    try:
        # medications_list = MedicationQueries.search_medications(
        #     search_term=search_term,
        #     drug_class=drug_class_filter if drug_class_filter != "All" else None,
        #     favorites_only=favorites_only_filter,
        #     doctor_id=doctor['id']
        # ) # Actual
        medications_list = get_mock_medications(search_term, drug_class_filter, favorites_only_filter, doctor['id']) # Mock
    except AttributeError:
        show_warning_message("Medication query service initializing. Using mock data.", icon="⚠️")
        medications_list = get_mock_medications(search_term, drug_class_filter, favorites_only_filter, doctor['id'])
    except Exception as e:
        show_error_message(f"Error fetching medications: {e}")
        medications_list = []

    if not medications_list:
        st.info("No medications found matching your criteria. Try adjusting your search or filters.")
        return

    num_columns = 3
    item_cols = st.columns(num_columns)
    for i, med_item_data in enumerate(medications_list):
        with item_cols[i % num_columns]:
            is_fav = med_item_data.get('is_favorite', False)
            fav_button_label = "🌟 Unfavorite" if is_fav else "⭐ Favorite"

            # Define actions for the card
            card_actions = {
                fav_button_label: lambda m_id=med_item_data['id'], d_id=doctor['id'], current_fav_status=is_fav: handle_toggle_favorite(m_id, d_id, current_fav_status),
                "View Details": lambda m_name=med_item_data['name']: st.toast(f"Details for {m_name} (placeholder).")
            }
            try:
                MedicationCard(medication_data=med_item_data, actions=card_actions, key=f"med_card_{med_item_data['id']}")
            except Exception as e:
                st.error(f"Error rendering card for {med_item_data.get('name')}: {e}")
                st.json(med_item_data)


# --- Main Page Function ---
def show_medications_page():
    require_authentication()
    require_role_access([USER_ROLES['DOCTOR']])
    inject_css()

    st.markdown("<h1>💊 Medications Database</h1>", unsafe_allow_html=True)

    if 'med_search_term' not in st.session_state: st.session_state.med_search_term = ""
    if 'med_drug_class' not in st.session_state: st.session_state.med_drug_class = "All"
    if 'med_show_favorites' not in st.session_state: st.session_state.med_show_favorites = False

    render_medication_search_and_filters()
    render_medications_list()

if __name__ == "__main__":
    if 'user' not in st.session_state:
        st.session_state.user = {
            'id': 'docMedBrowser', 'username': 'dr_medsearch',
            'role': USER_ROLES['DOCTOR'], 'full_name': 'Dr. Med Browser',
            'email': 'dr.meds@example.com'
        }
        st.session_state.authenticated = True
        st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)

    if 'med_search_term' not in st.session_state: st.session_state.med_search_term = ""
    if 'med_drug_class' not in st.session_state: st.session_state.med_drug_class = "All"
    if 'med_show_favorites' not in st.session_state: st.session_state.med_show_favorites = False

    # Initialize some mock favorites for the test user if not already set
    # This helps in testing the 'Show Only My Favorites' filter on first load in dev
    if 'docMedBrowser' not in MOCK_FAVORITE_MEDS:
        MOCK_FAVORITE_MEDS['docMedBrowser'] = set() # Ensure the set exists
        mock_toggle_favorite_medication('med001', 'docMedBrowser') # Amoxicillin
        mock_toggle_favorite_medication('med003', 'docMedBrowser') # Lisinopril

    show_medications_page()

import streamlit as st
from datetime import datetime, timedelta
import copy # For duplicating templates

# Config and Auth
from config.settings import USER_ROLES, TEMPLATE_CONFIG
from config.styles import inject_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access

# Components
from components.cards import TemplateCard # Assuming this component exists

# Database & Services
from database.queries import TemplateQueries # Assuming this exists
from services.template_service import TemplateService # Assuming this exists

# Utils
from utils.helpers import show_error_message, show_success_message, show_warning_message # Assuming these exist

# --- Mock Data (if needed) ---
MOCK_TEMPLATES_DB = [] # In-memory list to act as a simple DB for mocks

def initialize_mock_db():
    global MOCK_TEMPLATES_DB
    if not MOCK_TEMPLATES_DB: # Only add if empty, to prevent duplicates on reruns in dev
        mock_create_template({
            "name": "Standard Flu Follow-up", "category": "Follow-up",
            "description": "Template for typical flu follow-up.",
            "diagnosis": "Seasonal Influenza", "instructions": "Rest, hydrate, monitor fever.",
            "medications": [{"name": "Oseltamivir", "dosage": "75mg", "frequency": "BID", "duration": "5 days"}],
            "lab_tests": []
        }, 'docTemplateUser', is_initial_setup=True)
        mock_create_template({
            "name": "Routine Checkup", "category": "General",
            "description": "Baseline health check.",
            "diagnosis": "Routine Health Maintenance", "instructions": "Discuss lifestyle, schedule next visit.",
            "medications": [],
            "lab_tests": [{"name": "Lipid Panel", "instructions": "Fasting required"}]
        }, 'docTemplateUser', is_initial_setup=True)


def get_mock_doctor_templates(doctor_id: str):
    return [copy.deepcopy(t) for t in MOCK_TEMPLATES_DB if t['doctor_id'] == doctor_id]

def get_mock_template_by_id(template_id: str, doctor_id: str):
    for t in MOCK_TEMPLATES_DB:
        if t['id'] == template_id and t['doctor_id'] == doctor_id:
            return copy.deepcopy(t)
    return None

def mock_create_template(data, doctor_id, is_initial_setup=False):
    # is_initial_setup flag to prevent success messages during __main__ setup
    new_id = f"tmpl_{len(MOCK_TEMPLATES_DB) + 1}_{datetime.now().strftime('%S%f')}" # more unique ID
    new_template = {
        'id': new_id, 'doctor_id': doctor_id, **data,
        'created_at': datetime.now().isoformat(), 'updated_at': datetime.now().isoformat()
    }
    MOCK_TEMPLATES_DB.append(new_template)
    if not is_initial_setup: show_success_message(f"Mock Template '{new_template['name']}' created.")
    return new_template

def mock_update_template(template_id, data, doctor_id):
    for i, t in enumerate(MOCK_TEMPLATES_DB):
        if t['id'] == template_id and t['doctor_id'] == doctor_id:
            MOCK_TEMPLATES_DB[i] = {**t, **data, 'updated_at': datetime.now().isoformat()}
            show_success_message(f"Mock Template '{data['name']}' updated.")
            return MOCK_TEMPLATES_DB[i]
    show_error_message("Mock template not found for update.")
    return None

def mock_delete_template(template_id, doctor_id):
    global MOCK_TEMPLATES_DB
    original_len = len(MOCK_TEMPLATES_DB)
    MOCK_TEMPLATES_DB = [t for t in MOCK_TEMPLATES_DB if not (t['id'] == template_id and t['doctor_id'] == doctor_id)]
    if len(MOCK_TEMPLATES_DB) < original_len:
        show_success_message(f"Mock Template ID {template_id} deleted.")
        return True
    show_error_message("Mock template not found for deletion.")
    return False

# --- Helper Functions (Service Calls with Mock Fallback) ---
def handle_save_template(data, doctor_id):
    try:
        template = TemplateService.create_template(data, doctor_id) # Actual
        show_success_message(f"Template '{template['name']}' created successfully!")
    except AttributeError: # TemplateService or method not available
        show_warning_message("Template service not available. Using mock creation.")
        template = mock_create_template(data, doctor_id)
    except Exception as e:
        show_error_message(f"Error creating template: {e}")
        return # Prevent state clear on error

    st.session_state.editing_template_id = None
    st.session_state.template_form_data = {}
    st.rerun()


def handle_update_template(template_id, data, doctor_id):
    try:
        template = TemplateService.update_template(template_id, data, doctor_id) # Actual
        show_success_message(f"Template '{template['name']}' updated successfully!")
    except AttributeError:
        show_warning_message("Template service not available. Using mock update.")
        template = mock_update_template(template_id, data, doctor_id)
        if not template: return # Mock update failed
    except Exception as e:
        show_error_message(f"Error updating template: {e}")
        return

    st.session_state.editing_template_id = None
    st.session_state.template_form_data = {}
    st.rerun()

def handle_delete_template(template_id, doctor_id):
    # Simple confirmation for mock, real might use modal
    if st.session_state.get(f"confirm_delete_{template_id}"):
        try:
            # success = TemplateService.delete_template(template_id, doctor_id) # Actual
            success = mock_delete_template(template_id, doctor_id) # Mock
        except AttributeError:
            show_warning_message("Template service not available. Using mock delete.")
            success = mock_delete_template(template_id, doctor_id)
        except Exception as e:
            show_error_message(f"Error deleting template: {e}")
            success = False

        del st.session_state[f"confirm_delete_{template_id}"]
        if success: st.rerun()
    else:
        st.session_state[f"confirm_delete_{template_id}"] = True
        show_warning_message(f"Are you sure you want to delete template ID {template_id}? Click 'Delete' again to confirm.")
        st.rerun()


def handle_duplicate_template(template_id_to_duplicate, doctor_id):
    # This function would ideally use a modal for new name input for better UX
    # For now, using a session_state flag to show text_input
    st.session_state.duplicating_template_id = template_id_to_duplicate
    st.rerun()

def process_duplication(original_template_id, new_name, doctor_id):
    try:
        # original_template = TemplateQueries.get_template_details(original_template_id, doctor_id) # Actual
        original_template = get_mock_template_by_id(original_template_id, doctor_id) # Mock
        if not original_template:
            show_error_message("Original template not found.")
            return

        duplicated_data = {k: v for k, v in original_template.items() if k not in ['id', 'created_at', 'updated_at', 'doctor_id']}
        duplicated_data['name'] = new_name

        # new_template = TemplateService.create_template(duplicated_data, doctor_id) # Actual
        new_template = mock_create_template(duplicated_data, doctor_id) # Mock
        if new_template:
            show_success_message(f"Template duplicated as '{new_name}' successfully!")
    except AttributeError:
        show_warning_message("Template service/queries not available. Using mock duplication.")
        # Simplified mock duplication for Attribute Error case (already covered by mock_create_template)
    except Exception as e:
        show_error_message(f"Error duplicating template: {e}")
    finally:
        st.session_state.duplicating_template_id = None # Clear duplication mode
        st.rerun()


# --- UI Rendering Functions ---
def render_view_templates_section(doctor: dict):
    st.subheader("My Templates")

    if st.session_state.get('duplicating_template_id'):
        original_template_id = st.session_state.duplicating_template_id
        # original_template = TemplateQueries.get_template_details(original_template_id, doctor['id']) # Actual
        original_template = get_mock_template_by_id(original_template_id, doctor['id']) # Mock
        default_new_name = f"{original_template['name']} (Copy)" if original_template else "New Template Name"

        st.text_input("Enter name for duplicated template:", value=default_new_name, key="new_template_name_for_duplicate")
        col1, col2 = st.columns(2)
        if col1.button("✅ Confirm Duplicate", key="confirm_duplicate_btn"):
            process_duplication(original_template_id, st.session_state.new_template_name_for_duplicate, doctor['id'])
        if col2.button("❌ Cancel Duplicate", key="cancel_duplicate_btn"):
            st.session_state.duplicating_template_id = None
            st.rerun()
        return # Show only duplication UI

    if st.button("➕ Create New Template", key="create_new_template_btn"):
        st.session_state.editing_template_id = 'new'
        st.session_state.template_form_data = { # Initialize with defaults
            "name": "", "category": TEMPLATE_CONFIG['CATEGORIES'][0] if TEMPLATE_CONFIG['CATEGORIES'] else "General",
            "description": "", "diagnosis": "", "instructions": "",
            "medications": [], "lab_tests": []
        }
        st.rerun()
    st.markdown("---")

    try:
        templates = TemplateQueries.get_doctor_templates(doctor['id']) # Actual
    except AttributeError:
        st.warning("Template query system initializing. Using mock template data.", icon="⚠️")
        templates = get_mock_doctor_templates(doctor['id'])
    except Exception as e:
        show_error_message(f"Error fetching templates: {e}")
        templates = []

    if not templates:
        st.info("You haven't created any templates yet. Click 'Create New Template' to get started.")
        return

    for template in templates:
        actions = {
            "Edit": lambda t=template: edit_template_action(t),
            "Delete": lambda t_id=template['id']: handle_delete_template(t_id, doctor['id']),
            "Duplicate": lambda t_id=template['id']: handle_duplicate_template(t_id, doctor['id']),
        }
        confirm_delete_msg = "Confirm Delete?" if st.session_state.get(f"confirm_delete_{template['id']}") else None
        try:
            TemplateCard(template_data=template, actions=actions, key=f"template_card_{template['id']}",
                         show_confirm_delete=bool(confirm_delete_msg)) # Pass confirmation state to card if it handles it
        except TypeError: # Fallback if card doesn't support show_confirm_delete
            TemplateCard(template_data=template, actions=actions, key=f"template_card_{template['id']}")
            if confirm_delete_msg: st.caption(confirm_delete_msg) # Show message below card
        except Exception as e:
            st.error(f"Error rendering template card for {template.get('name', template.get('id'))}: {e}")
            st.json(template)
        st.markdown("---")


def edit_template_action(template_data):
    st.session_state.editing_template_id = template_data['id']
    st.session_state.template_form_data = copy.deepcopy(template_data)
    if 'medications' not in st.session_state.template_form_data or st.session_state.template_form_data['medications'] is None:
        st.session_state.template_form_data['medications'] = []
    if 'lab_tests' not in st.session_state.template_form_data or st.session_state.template_form_data['lab_tests'] is None:
        st.session_state.template_form_data['lab_tests'] = []
    st.rerun()

def render_edit_template_section(doctor: dict):
    form_data = st.session_state.template_form_data
    is_new_template = st.session_state.editing_template_id == 'new'

    header = "Create New Template" if is_new_template else f"Edit Template: {form_data.get('name', '')}"
    st.subheader(header)

    with st.form("template_form"):
        current_name = form_data.get('name', '')
        form_data['name'] = st.text_input("Template Name", value=current_name)

        # Ensure category list is not empty and selection is valid
        categories = TEMPLATE_CONFIG.get('CATEGORIES', ["General", "Follow-up"])
        current_category = form_data.get('category', categories[0])
        if current_category not in categories: current_category = categories[0]
        category_index = categories.index(current_category)
        form_data['category'] = st.selectbox("Category", options=categories, index=category_index)

        form_data['description'] = st.text_area("Description (optional)", value=form_data.get('description', ''))

        st.markdown("##### Content")
        form_data['diagnosis'] = st.text_area("Diagnosis / Clinical Impression", value=form_data.get('diagnosis', ''))
        form_data['instructions'] = st.text_area("General Instructions / Advice", value=form_data.get('instructions', ''))

        st.markdown("##### Medications")
        if 'medications' not in form_data or not isinstance(form_data['medications'], list): form_data['medications'] = []
        form_data['medications'] = st.data_editor(
            form_data['medications'], num_rows="dynamic", key="med_editor",
            column_config={ "name": st.column_config.TextColumn("Medication Name", required=True), "dosage": "Dosage", "frequency": "Frequency", "duration": "Duration"}
        )

        st.markdown("##### Lab Tests")
        if 'lab_tests' not in form_data or not isinstance(form_data['lab_tests'], list): form_data['lab_tests'] = []
        form_data['lab_tests'] = st.data_editor(
            form_data['lab_tests'], num_rows="dynamic", key="lab_editor",
            column_config={ "name": st.column_config.TextColumn("Test Name", required=True), "instructions": "Instructions"}
        )

        col1, col2 = st.columns(2)
        with col1:
            action_label = "💾 Save Template" if is_new_template else "🔄 Update Template"
            if st.form_submit_button(action_label, use_container_width=True):
                if not form_data['name']:
                    show_error_message("Template Name is required.")
                else:
                    if is_new_template:
                        handle_save_template(form_data, doctor['id'])
                    else:
                        handle_update_template(st.session_state.editing_template_id, form_data, doctor['id'])
        with col2:
            if st.form_submit_button("❌ Cancel", type="secondary", use_container_width=True):
                st.session_state.editing_template_id = None
                st.session_state.template_form_data = {}
                st.rerun()

    # This direct update to session state outside form submission might be problematic if st.rerun is called elsewhere
    # st.session_state.template_form_data = form_data


# --- Main Page Function ---
def show_templates_page():
    require_authentication()
    require_role_access([USER_ROLES['DOCTOR']])
    inject_css()

    st.markdown("<h1>📋 Prescription Templates</h1>", unsafe_allow_html=True)

    current_user = get_current_user()
    if not current_user:
        show_error_message("Unable to retrieve user information. Please log in again.")
        return

    if 'editing_template_id' not in st.session_state: st.session_state.editing_template_id = None
    if 'template_form_data' not in st.session_state: st.session_state.template_form_data = {}
    if 'duplicating_template_id' not in st.session_state: st.session_state.duplicating_template_id = None


    if st.session_state.editing_template_id is not None:
        render_edit_template_section(current_user)
    else: # Handles both normal view and duplication prompt
        render_view_templates_section(current_user)

if __name__ == "__main__":
    if 'user' not in st.session_state:
        st.session_state.user = {
            'id': 'docTemplateUser', 'username': 'dr_templater',
            'role': USER_ROLES['DOCTOR'], 'full_name': 'Dr. Templater',
            'email': 'dr.templater@example.com'
        }
        st.session_state.authenticated = True
        st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)

    if 'editing_template_id' not in st.session_state: st.session_state.editing_template_id = None
    if 'template_form_data' not in st.session_state: st.session_state.template_form_data = {}
    if 'duplicating_template_id' not in st.session_state: st.session_state.duplicating_template_id = None

    initialize_mock_db() # Populate mock DB for testing
    # show_templates_page() # Called at module level now

# This call ensures Streamlit runs the page content when navigating
show_templates_page()

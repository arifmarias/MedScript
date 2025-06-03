import streamlit as st
from datetime import datetime, timedelta # Added for show_login_page (used by its expander/demo section if any part uses it)
from database.init_db import check_and_initialize_database
from auth.permissions import get_allowed_navigation_items
from config.styles import inject_css, inject_component_css # Added for show_login_page
# Ensure all necessary auth functions are imported, show_login_page is removed, login_user is added
from auth.authentication import (
    initialize_session,
    is_authenticated,
    # show_login_page, # Will be defined locally
    logout_user,
    get_current_user,
    check_session_validity,
    login_user # Ensured login_user is imported
)
from config.settings import USER_ROLES

# Page Imports (will be dynamic based on actual files in pages/)
from pages.c1_doctor_dashboard import show_doctor_dashboard # Placeholder, replace c1_ with actual prefix
from pages.c2_doctor_todays_patients import show_todays_patients_page # Placeholder
from pages.c8_assistant_dashboard import show_assistant_dashboard # Placeholder
from pages.c14_super_admin_dashboard import show_super_admin_dashboard # Placeholder
# Actual imports based on ls output:
# from pages.d1_doctor_dashboard import show_doctor_dashboard # MOVED LOCALLY
# from pages.d2_doctor_todays_patients import show_todays_patients_page # MOVED LOCALLY
# from pages.d3_doctor_prescriptions import show_prescriptions_page # MOVED LOCALLY
# from pages.d4_doctor_templates import show_templates_page # MOVED LOCALLY
# from pages.d5_doctor_medications import show_medications_page # Will be MOVED LOCALLY
# from pages.d8_assistant_dashboard import show_assistant_dashboard # MOVED LOCALLY
# from pages.d14_super_admin_dashboard import show_super_admin_dashboard # MOVED LOCALLY

# Imports for various dashboards and components
from datetime import date # Already have datetime, timedelta. Ensure date is directly available.
import pandas as pd # Already available via mock AnalyticsService if that's defined above. Ensure it's here.
from typing import Dict, List, Any # Standard typing
from auth.permissions import require_role_access
from services.analytics_service import AnalyticsService # get_user_dashboard_metrics is not a separate import from the provided file
# Assuming MetricCard is generic enough. For others, add mocks if not available.
try:
    from components.cards import MetricCard, AnalyticsCard, ActivityCard, render_card_grid
    CARDS_SA_AVAILABLE = True
except ImportError:
    CARDS_SA_AVAILABLE = False
    if "MetricCard" not in globals(): # If MetricCard itself wasn't found earlier
        def MetricCard(label, value, key=None, help_text=None, icon=None): st.metric(label=label, value=value, help=help_text) # Mock
    def AnalyticsCard(title, data, key=None): st.info(f"AnalyticsCard: {title} (mock)")
    def ActivityCard(activities, max_items=5, key=None): st.info(f"ActivityCard: {len(activities)} items (mock)")
    def render_card_grid(cards_data, card_type_map, columns=3): st.info("render_card_grid (mock)")

try:
    from components.charts import TimeSeriesChart, PieChart, BarChart, AnalyticsDashboard, create_medical_kpi_dashboard
    CHARTS_SA_AVAILABLE = True
except ImportError:
    CHARTS_SA_AVAILABLE = False
    # Mocks for these charts are already defined if CHARTS_AVAILABLE was False earlier.
    # If AnalyticsDashboard or create_medical_kpi_dashboard are distinct, they need mocks here.
    if "AnalyticsDashboard" not in globals():
        class AnalyticsDashboard:
            def __init__(self, data, title=None): self.data = data; self.title = title
            def render_prescription_analytics(self): st.info(f"AnalyticsDashboard - Prescription (mock): {self.title}")
            # Add other render methods if used by SA dashboard
    if "create_medical_kpi_dashboard" not in globals():
        def create_medical_kpi_dashboard(data, title=None): st.info(f"Medical KPI Dashboard (mock): {title}")

# Imports for Doctor's Prescription Page
try:
    from components.cards import PrescriptionCard
except ImportError:
    if "PrescriptionCard" not in globals(): # Check if already mocked by another page
        def PrescriptionCard(prescription_data, actions, key): st.info(f"PrescriptionCard (mock) for {prescription_data.get('prescription_id')}")
try:
    from components.forms import PrescriptionMedicationComponent, PrescriptionLabTestComponent
    # SearchFormComponent already imported/mocked
except ImportError:
    if "PrescriptionMedicationComponent" not in globals():
        def PrescriptionMedicationComponent(current_medications, available_medications, key_prefix):
            st.info("PrescriptionMedicationComponent (mock)")
            return current_medications # Pass through for now
    if "PrescriptionLabTestComponent" not in globals():
        def PrescriptionLabTestComponent(current_lab_tests, available_lab_tests, key_prefix):
            st.info("PrescriptionLabTestComponent (mock)")
            return current_lab_tests # Pass through

try:
    from services.ai_service import AIAnalysisService, is_ai_available
except ImportError:
    if "AIAnalysisService" not in globals():
        class AIAnalysisService: pass # Simple mock
    if "is_ai_available" not in globals():
        def is_ai_available(): return False # Default to false if service not there

try:
    from services.pdf_service import generate_prescription_pdf, get_pdf_filename, create_download_link
except ImportError:
    def generate_prescription_pdf(rx_data): st.info("generate_prescription_pdf (mock)"); return b"PDF_CONTENT_MOCK"
    def get_pdf_filename(rx_data): return "mock_prescription.pdf"
    def create_download_link(content, filename, label): st.info(f"Download link for {filename} (mock)")


# Updated database queries import to include all necessary for SA Dashboard
from database.queries import (
    DashboardQueries, TemplateQueries, VisitQueries, PatientQueries,
    AnalyticsQueries, UserQueries, PrescriptionQueries, get_entity_counts,
    MedicationQueries, LabTestQueries # Added for prescription page
)
# Updated formatters import
from utils.formatters import format_date_display, format_time_display, format_percentage, format_currency, format_patient_name
# from utils.helpers import show_error_message, show_success_message, show_warning_message # Assumed globally available
from datetime import time # Added for _dtp_get_mock_patient_visits
import copy # Added for _drtmpl_ functions

# Imports for Doctor's Templates Page
from config.settings import TEMPLATE_CONFIG # Added
try:
    from components.cards import TemplateCard
except ImportError:
    if "TemplateCard" not in globals(): # Check if already mocked
        def TemplateCard(template_data, actions, key, show_confirm_delete=False): st.info(f"TemplateCard (mock) for {template_data.get('name')}")
try:
    from services.template_service import TemplateService
except ImportError:
    if "TemplateService" not in globals():
        class TemplateService: # Basic mock
            @staticmethod
            def create_template(data, dr_id): return {"id": "mock_tmpl_new", **data}
            @staticmethod
            def update_template(t_id, data, dr_id): return {"id": t_id, **data}
            @staticmethod
            def delete_template(t_id, dr_id): return True
# TemplateQueries already imported via Doctor Dashboard

# Imports for Doctor's Medications Page
from config.settings import DRUG_CLASSES # Added (ensure it's not duplicated if already there for other roles)
# MedicationCard, SearchFormComponent, MedicationQueries are likely already handled or mocked.

# Full-featured Doctor Dashboard (moved from pages/1_doctor_dashboard.py original spec)
def render_doctor_dashboard_content_internal(current_user):
    st.subheader("Activity Overview")

    col1_time_filter, col2_refresh_btn = st.columns([3,1])
    with col1_time_filter:
        days_back_selection = st.selectbox(
            "Select Time Range for Analytics:",
            options=[7, 14, 30, 90],
            format_func=lambda x: f"Last {x} days",
            index=2,  # Default to 30 days
            key="doctor_dash_days_back_v1" # Unique key
        )
    with col2_refresh_btn:
        st.markdown("<div>&nbsp;</div>", unsafe_allow_html=True) # Vertical alignment
        if st.button("Refresh Data", key="doctor_dash_refresh_v1"): # Unique key
            st.rerun()

    metrics_data = {}
    my_prescriptions_val = "N/A"
    today_patients_val = "N/A"
    completed_consultations_val = "N/A"
    pending_consultations_val = "N/A"
    active_templates_val = "N/A"

    try:
        analytics_service_instance = AnalyticsService() # Needs to be defined or imported
        metrics_data = analytics_service_instance.get_dashboard_metrics(
            USER_ROLES['DOCTOR'],
            current_user['id'],
            days_back=days_back_selection
        )
        my_prescriptions_val = metrics_data.get('my_prescriptions', metrics_data.get('my_prescriptions_count',0)) # Check for common key variations

    except Exception as e:
        st.error(f"Error fetching doctor analytics metrics: {e}")
        # metrics_data remains {}

    try:
        today_summary_data = DashboardQueries.get_today_summary(doctor_id=current_user['id'])
        if today_summary_data is None: today_summary_data = {}
        today_patients_val = today_summary_data.get('todays_visits_doctor', today_summary_data.get('total_patients', 0))
        completed_consultations_val = today_summary_data.get('completed_consultations_doctor', today_summary_data.get('completed_consultations', 0))
        if isinstance(today_patients_val, int) and isinstance(completed_consultations_val, int):
            pending_consultations_val = today_patients_val - completed_consultations_val
        else:
            pending_consultations_val = "N/A"
    except Exception as e:
        st.error(f"Error fetching today's summary: {e}")

    try:
        active_templates_list = TemplateQueries.get_doctor_templates(current_user['id']) # Assuming this returns a list
        active_templates_val = len(active_templates_list) if active_templates_list is not None else 0
    except AttributeError: # If TemplateQueries or method doesn't exist
        st.warning("TemplateQueries not available for active templates count.")
        active_templates_val = "N/A"
    except Exception as e:
        st.error(f"Error fetching template count: {e}")
        active_templates_val = "N/A"


    st.markdown("<h4>Key Metrics</h4>", unsafe_allow_html=True)
    m_cols = st.columns(5)
    # Using st.metric directly as MetricCard might not be available or might have different signature
    m_cols[0].metric("Today's Patients", today_patients_val)
    m_cols[1].metric("Completed Today", completed_consultations_val)
    m_cols[2].metric("Pending Today", pending_consultations_val)
    m_cols[3].metric(f"My Prescriptions (Last {days_back_selection}d)", my_prescriptions_val)
    m_cols[4].metric("Active Templates", active_templates_val)

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.subheader("Today's Appointments")
    try:
        today_visits_list = VisitQueries.get_doctor_today_visits(current_user['id'])
        if not today_visits_list:
            st.info("No appointments scheduled for today.")
        else:
            for visit in today_visits_list:
                patient_name = visit.get('patient_full_name', visit.get('patient_name', 'N/A'))
                visit_time = visit.get('visit_time')
                # format_time_display needs to be robust for various time formats (datetime.time, str)
                visit_time_str = format_time_display(visit_time) if visit_time else 'N/A'
                visit_type = visit.get('visit_type', 'Consultation')
                visit_status = visit.get('status', visit.get('consultation_completed_status', 'Scheduled'))

                cols_appt = st.columns([3,1,2,1])
                cols_appt[0].markdown(f"**{patient_name}**")
                cols_appt[1].markdown(f"🕒 {visit_time_str}")
                cols_appt[2].markdown(f"📋 {visit_type}")
                if str(visit_status).lower() == 'completed':
                    cols_appt[3].success(f"✅ Completed")
                elif str(visit_status).lower() in ['pending', 'scheduled']:
                    cols_appt[3].warning(f"⏳ {str(visit_status).title()}")
                else:
                    cols_appt[3].info(f"{str(visit_status).title()}")
    except AttributeError:
        st.warning("VisitQueries or get_doctor_today_visits method not found. Appointments cannot be displayed.")
    except Exception as e:
        st.error(f"Error fetching today's appointments: {e}")
        st.info("Today's appointments list will be shown here.")

# Main function for Doctor Dashboard page content
def render_doctor_dashboard(user: dict):
    # require_authentication() # Handled by run_app calling this
    require_role_access([USER_ROLES['DOCTOR']]) # Still good for direct calls or future refactoring

    # inject_css() # Global CSS is in show_login_page and potentially main app if needed
    inject_component_css('DASHBOARD_CARDS') # Specific to this dashboard

    st.markdown("<h1>👨‍⚕️ Doctor Dashboard</h1>", unsafe_allow_html=True)

    if user:
        render_doctor_dashboard_content_internal(user)
    else:
        st.error("Could not retrieve user information for dashboard.")

# --- Assistant Dashboard Start ---
# Copied from pages/8_assistant_dashboard.py and adapted
# Helper function for Assistant Dashboard content
def render_assistant_dashboard_content_internal(current_user: dict): # Renamed for consistency
    st.subheader("🗓️ Daily Overview & Quick Actions")

    col1_time, col2_refresh, col3_spacer = st.columns([2,1,2])
    with col1_time:
        days_back_filter = st.selectbox(
            "Select Period for My Activity:",
            options=[7, 14, 30, 90],
            format_func=lambda x: f"Last {x} days",
            index=1, # Default to 14 days
            key="asst_dash_days_back_v1"
        )
    with col2_refresh:
        st.markdown("<div>&nbsp;</div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh Data", key="asst_dash_refresh_v1", use_container_width=True):
            st.rerun()

    st.markdown("---")

    st.markdown("<h4>Key Metrics</h4>", unsafe_allow_html=True)

    patients_registered_by_me = "N/A"
    visits_recorded_by_me = "N/A"
    total_patients_managed = "N/A"
    upcoming_appointments_today = "N/A"

    try:
        analytics_service = AnalyticsService() # Assumes AnalyticsService is imported and robust
        assistant_metrics = analytics_service.get_dashboard_metrics(
            USER_ROLES['ASSISTANT'], current_user['id'], days_back=days_back_filter
        )
        patients_registered_by_me = assistant_metrics.get('patients_registered_by_user', 0)
        visits_recorded_by_me = assistant_metrics.get('visits_recorded_by_user', 0)
    except Exception as e:
        st.warning(f"Could not load some analytics: {e}")
        # Fallback to direct queries if AnalyticsService fails or specific metrics are not there
        try:
            patients_registered_by_me = PatientQueries.count_patients_created_by(current_user['id'], days_back=days_back_filter)
            visits_recorded_by_me = VisitQueries.count_visits_recorded_by(current_user['id'], days_back=days_back_filter)
        except Exception as qe:
            st.error(f"Error fetching activity data: {qe}")


    try:
        total_patients_managed = PatientQueries.get_total_patients_managed_by(current_user['id'])
        upcoming_appointments_today = VisitQueries.get_all_today_visits()
    except AttributeError as ae: # Handles if a query class or method is missing
        st.error(f"A required database query function is missing: {ae}. Some metrics cannot be displayed.")
    except Exception as e:
        st.error(f"Error fetching summary metrics: {e}")

    m_cols = st.columns(4)
    # Using st.metric as MetricCard might not be available or might have different signature
    m_cols[0].metric(label=f"Patients Registered (Last {days_back_filter}d)", value=patients_registered_by_me)
    m_cols[1].metric(label=f"Visits Recorded (Last {days_back_filter}d)", value=visits_recorded_by_me)
    m_cols[2].metric(label="Total Patients You Manage", value=total_patients_managed)
    m_cols[3].metric(label="Upcoming Appointments Today (All)", value=upcoming_appointments_today)

    st.markdown("---")

    st.subheader("🚀 Quick Actions")
    qa_cols = st.columns(2)
    if qa_cols[0].button("➕ Register New Patient", use_container_width=True, type="primary", key="asst_reg_patient_btn"):
        st.toast("Action: Navigate to Patient Registration (Simulated).")
        # This would ideally set st.session_state.current_page = 'pages/9_assistant_patient_management.py' and st.rerun()
        # For now, direct navigation is not implemented here, only via sidebar.
    if qa_cols[1].button("➕ Record New Visit", use_container_width=True, type="primary", key="asst_rec_visit_btn"):
        st.toast("Action: Navigate to Record Visit (Simulated).")
        # This would ideally set st.session_state.current_page = 'pages/10_assistant_visit_management.py' and st.rerun()

    st.markdown("---")
    st.info("Recent activity and task list sections will be available soon.")

# Main function for Assistant Dashboard page content
def render_assistant_dashboard(user: dict):
    require_role_access([USER_ROLES['ASSISTANT']])
    inject_component_css('DASHBOARD_CARDS')
    st.markdown("<h1>💁‍♀️ Assistant Dashboard</h1>", unsafe_allow_html=True)

    if user:
        # The welcome message `st.sidebar.success(...)` is now handled by the main show_sidebar function.
        render_assistant_dashboard_content_internal(user)
    else:
        st.error("Could not retrieve user information for assistant dashboard.")
# --- Assistant Dashboard End ---

# Definition of show_login_page() MOVED HERE
def show_login_page():
    st.markdown("<style>div[data-testid='stSidebarNav'] {display: none;}</style>", unsafe_allow_html=True)
    # from config.styles import inject_css, inject_component_css # Already imported at top level

    # Inject CSS
    inject_css()
    inject_component_css('LOGIN_FORM')

    # initialize_session() # Removed as it's called at the start of run_app()

    st.markdown("""
        <div class="main-header">
            <h1>🏥 MedScript Pro</h1>
            <p>Comprehensive Medical Prescription Management System</p>
        </div>
    """, unsafe_allow_html=True)

    # Login container
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)

            st.markdown("""
                <div class="login-header">
                    <h2>🔐 Login</h2>
                    <p>Please enter your credentials to access the system</p>
                </div>
            """, unsafe_allow_html=True)

            # Login form
            with st.form("login_form"):
                username = st.text_input(
                    "Username",
                    placeholder="Enter your username",
                    help="Use demo credentials: superadmin, doctor1, or assistant1"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    help="Demo passwords: admin123, doctor123, assistant123"
                )

                col_login, col_clear = st.columns(2)

                with col_login:
                    login_submitted = st.form_submit_button(
                        "🔓 Login",
                        use_container_width=True,
                        type="primary"
                    )

                with col_clear:
                    if st.form_submit_button("🔄 Clear", use_container_width=True):
                        st.rerun()

            # Handle login
            if login_submitted:
                if username and password:
                    if login_user(username, password): # Calls imported login_user
                        st.rerun()
                else:
                    st.error("Please enter both username and password") # Direct error, no ERROR_MESSAGES needed here

            st.markdown('</div>', unsafe_allow_html=True)

    # Demo credentials info
    with st.expander("🔍 Demo Credentials", expanded=False):
        col1_exp, col2_exp, col3_exp = st.columns(3) # Renamed to avoid conflict with outer scope if any

        with col1_exp:
            st.markdown("""
                **Super Admin**
                - Username: `superadmin`
                - Password: `admin123`
                - Full system access
            """)

        with col2_exp:
            st.markdown("""
                **Doctor**
                - Username: `doctor1`
                - Password: `doctor123`
                - Clinical workflow access
            """)

        with col3_exp:
            st.markdown("""
                **Assistant**
                - Username: `assistant1`
                - Password: `assistant123`
                - Patient support functions
            """)

    # System info
    st.markdown("---")
    col1_info, col2_info, col3_info = st.columns(3) # Renamed to avoid conflict

    with col1_info:
        st.info("""
            **🏥 Features**
            - Role-based access control
            - AI-powered drug interactions
            - Professional PDF prescriptions
        """)

    with col2_info:
        st.info("""
            **🔒 Security**
            - Encrypted password storage
            - Session management
            - Activity logging
        """)

    with col3_info:
        st.info("""
            **📊 Analytics**
            - Prescription tracking
            - Patient management
            - Usage statistics
        """)

st.set_page_config(
    page_title="MedScript Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

def show_sidebar(user: dict):
    with st.sidebar:
        st.markdown(f"### Welcome, {user.get('full_name', 'User')}")

        user_type_display = user.get('user_type', 'Unknown').replace('_', ' ').title()
        st.markdown(f"**Role:** {user_type_display}")
        st.markdown("---")

        allowed_pages_list = get_allowed_navigation_items() # This function already filters by role

        page_labels_with_icons = []
        page_key_to_path_map = {}

        for page_item in allowed_pages_list:
            label_with_icon = f"{page_item.get('icon', '')} {page_item['label']}"
            page_labels_with_icons.append(label_with_icon)
            page_key_to_path_map[label_with_icon] = page_item['path']

        if not page_labels_with_icons:
            st.write("No pages available for your role.")
        else:
            current_page_path = st.session_state.get('current_page')
            current_selection_label = None
            if current_page_path:
                for label, path_val in page_key_to_path_map.items():
                    if path_val == current_page_path:
                        current_selection_label = label
                        break

            if not current_selection_label and page_labels_with_icons:
                current_selection_label = page_labels_with_icons[0]
                st.session_state.current_page = page_key_to_path_map[current_selection_label]

            selected_page_label = st.radio(
                "Navigation",
                options=page_labels_with_icons,
                index=page_labels_with_icons.index(current_selection_label) if current_selection_label in page_labels_with_icons else 0,
                key="sidebar_navigation_radio"
            )

            if selected_page_label and page_key_to_path_map.get(selected_page_label) != st.session_state.get('current_page'):
                st.session_state.current_page = page_key_to_path_map[selected_page_label]
                st.rerun()

        st.markdown("---")
        if st.button("Log Out", key="sidebar_logout_button", use_container_width=True):
            logout_user()
            st.rerun()

def run_app(): # Renamed main to run_app
    check_and_initialize_database()
    initialize_session()
    check_session_validity()  # Handle session expiry

    if is_authenticated():
        current_user = get_current_user()
        show_sidebar(current_user)

        active_page_path = st.session_state.get('current_page')

        if not active_page_path:
            user_role = current_user.get('user_type')
            if user_role == USER_ROLES['DOCTOR']:
                active_page_path = 'pages/1_doctor_dashboard.py'
            elif user_role == USER_ROLES['ASSISTANT']:
                active_page_path = 'pages/8_assistant_dashboard.py'
            elif user_role == USER_ROLES['SUPER_ADMIN']:
                active_page_path = 'pages/14_super_admin_dashboard.py'
            else:
                st.markdown("# Welcome to MedScript Pro!")
                st.write("Please select a page from the navigation.")
                return

        # Call the appropriate page rendering function based on the path
        if active_page_path == 'pages/1_doctor_dashboard.py':
            render_doctor_dashboard(current_user) # Call the new local function
        elif active_page_path == 'pages/2_doctor_todays_patients.py':
            render_doctor_todays_patients(current_user) # Call the new local function
        elif active_page_path == 'pages/8_assistant_dashboard.py':
            render_assistant_dashboard(current_user) # Call the new local function
        elif active_page_path == 'pages/14_super_admin_dashboard.py':
            render_super_admin_dashboard(current_user)
        elif active_page_path == 'pages/3_doctor_prescriptions.py':
            render_doctor_prescriptions(current_user)
        elif active_page_path == 'pages/4_doctor_templates.py':
            render_doctor_templates(current_user)
        elif active_page_path == 'pages/5_doctor_medications.py':
            render_doctor_medications(current_user)
        # Add more elif conditions here as more pages are integrated
        else:
            st.error(f"Page not found: {active_page_path}")
            st.markdown("# Welcome to MedScript Pro!")
            st.write("Please select a valid page from the navigation.")
    else:
        show_login_page() # Calls the local version

if __name__ == "__main__":
    run_app() # Or main()

# --- Super Admin Dashboard Start ---
# Copied from pages/14_super_admin_dashboard.py and adapted

def _sa_render_overview_tab(days_filter): # Renamed with _sa_ prefix
    st.subheader("📊 System Overview")
    col_filter, col_refresh = st.columns([3, 1])
    with col_filter:
        time_range = st.selectbox(
            "Time Range", options=[7, 14, 30, 60, 90], index=2,
            format_func=lambda x: f"Last {x} days", key="sa_overview_time_range_v1"
        )
    with col_refresh:
        st.markdown("<div>&nbsp;</div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", use_container_width=True, key="sa_overview_refresh_v1"):
            st.rerun()

    analytics_service = AnalyticsService() # Assumes this is available
    # The SA dashboard used a specific get_dashboard_metrics, if that's different from doctor/assistant,
    # AnalyticsService needs to handle it or we use more specific queries.
    # For now, assuming get_dashboard_metrics can take SUPER_ADMIN role.
    metrics = analytics_service.get_dashboard_metrics(USER_ROLES['SUPER_ADMIN'], days_back=time_range)

    if not metrics: st.warning("Unable to load SA dashboard metrics"); return

    st.markdown("### 📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Total Users", metrics.get('total_users', 0))
    col2.metric("🏥 Total Patients", metrics.get('total_patients', 0))
    total_prescriptions = metrics.get('total_prescriptions', 0)
    recent_prescriptions = metrics.get('recent_prescriptions', 0)
    delta_rx = f"+{recent_prescriptions}" if recent_prescriptions > 0 else None
    col3.metric("📝 Total Prescriptions", total_prescriptions, delta=delta_rx)
    col4.metric("💊 Medications in DB", metrics.get('total_medications', 0))

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("🆕 New Patients", metrics.get('recent_patients', 0), help=f"Last {time_range} days")
    user_activity_list = metrics.get('user_activity', []) # Expects list of dicts like [{'user_type': 'doctor', 'count': 10}]
    total_activity_count = sum(item.get('count', 0) for item in user_activity_list)
    col6.metric("📊 User Activity Actions", total_activity_count, help=f"Last {time_range} days")

    try:
        today_summary = DashboardQueries.get_today_summary() # General summary
        col7.metric("📅 Today's Visits (All)", today_summary.get('todays_visits', 0))
        col8.metric("📋 Today's Prescriptions (All)", today_summary.get('todays_prescriptions', 0))
    except Exception as e:
        st.error(f"Failed to load today's summary: {e}")
        col7.metric("📅 Today's Visits (All)", "Error")
        col8.metric("📋 Today's Prescriptions (All)", "Error")

    st.markdown("### 📊 Analytics Charts")
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        if user_activity_list: # This is the data for role activity from metrics
            PieChart(data=pd.DataFrame(user_activity_list), title="User Activity by Role", labels_field='user_type', values_field='count') # Assuming PieChart takes DataFrame
        else: st.info("No user activity data for chart.")
    with col_chart2:
        top_doctors_data = metrics.get('top_doctors', []) # Expects list of dicts like [{'full_name': 'Dr. X', 'prescription_count': 5}]
        if top_doctors_data:
            BarChart(data=pd.DataFrame(top_doctors_data), title="Top Doctors by Prescriptions", x_field='full_name', y_field='prescription_count')
        else: st.info("No top doctors data.")

    st.markdown("### 🕐 Recent System Activity")
    try:
        recent_activity_logs = DashboardQueries.get_recent_activity(limit=10) # General system activity
        if recent_activity_logs: ActivityCard(recent_activity_logs, max_items=8).render() # Assumes ActivityCard and its render method
        else: st.info("No recent system activity found.")
    except Exception as e:
        st.error(f"Failed to load recent activity: {e}")

def _sa_render_users_tab(): # Renamed
    st.subheader("👥 User Management Overview")
    try:
        all_users = UserQueries.get_all_users() # Assumes this exists
        if not all_users: st.warning("No users found."); return

        active_users = len([u for u in all_users if u.get('is_active', True)])
        doctors = len([u for u in all_users if u.get('user_type') == USER_ROLES['DOCTOR']])
        assistants = len([u for u in all_users if u.get('user_type') == USER_ROLES['ASSISTANT']])

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Users", len(all_users)); col2.metric("Active Users", active_users)
        col3.metric("Doctors", doctors); # Add more metrics if space allows or rearrange
        # st.metric("Assistants", assistants)

        user_types_counts = {}
        for user in all_users: user_types_counts[user.get('user_type', 'unknown').title()] = user_types_counts.get(user.get('user_type', 'unknown').title(), 0) + 1
        if user_types_counts: PieChart(data=pd.DataFrame([{'user_type': k, 'count': v} for k,v in user_types_counts.items()]), title="User Distribution by Role", labels_field='user_type', values_field='count')

        st.markdown("### 🆕 Recently Registered Users (Top 5)")
        sorted_users = sorted(all_users, key=lambda x: x.get('created_at', str(datetime.min)), reverse=True)
        for user in sorted_users[:5]:
            st.write(f"**{user.get('full_name', 'N/A')}** ({user.get('user_type','N/A').title()}) - Joined: {format_date_display(user.get('created_at')) if user.get('created_at') else 'N/A'}")
    except Exception as e: st.error(f"Error rendering users tab: {e}")

def _sa_render_patients_tab(): # Renamed
    st.subheader("🏥 Patient Overview")
    try:
        # Using get_entity_counts for total, and search_patients for sample/demographics
        counts = AnalyticsQueries.get_entity_counts()
        total_patients = counts.get('total_patients',0)
        st.metric("Total Registered Patients", total_patients)

        # For demographics, we might need a sample or a dedicated query if 'all_patients' is too large
        # For mock, let's assume we can get some patient data for charts
        sample_patients_for_charts = PatientQueries.search_patients(limit=200) # Mock function might need limit param
        if not sample_patients_for_charts: st.info("Not enough patient data for demographic charts."); return

        ages = []
        gender_counts = {}
        for p in sample_patients_for_charts:
            gender_counts[p.get('gender', 'Unknown')] = gender_counts.get(p.get('gender', 'Unknown'), 0) + 1
            dob = p.get('date_of_birth')
            if dob:
                try:
                    birth_date = datetime.strptime(dob, '%Y-%m-%d').date() if isinstance(dob, str) else dob
                    ages.append((date.today() - birth_date).days // 365)
                except: pass

        col_chart_p1, col_chart_p2 = st.columns(2)
        if gender_counts: PieChart(data=pd.DataFrame([{'gender':k, 'count':v} for k,v in gender_counts.items()]), title="Patient Gender Distribution", labels_field='gender', values_field='count', parent_container=col_chart_p1)

        if ages:
            age_groups = {'0-18':0, '19-35':0, '36-50':0, '51-65':0, '65+':0}
            for age in ages:
                if age <= 18: age_groups['0-18']+=1
                elif age <=35: age_groups['19-35']+=1
                elif age <=50: age_groups['36-50']+=1
                elif age <=65: age_groups['51-65']+=1
                else: age_groups['65+']+=1
            if any(age_groups.values()): BarChart(data=pd.DataFrame([{'age_group':k, 'count':v} for k,v in age_groups.items()]), title="Patient Age Distribution", x_field='age_group', y_field='count', parent_container=col_chart_p2)

    except Exception as e: st.error(f"Error rendering patients tab: {e}")

def _sa_render_prescriptions_tab(): # Renamed
    st.subheader("📝 Prescription Overview")
    try:
        analytics_service = AnalyticsService()
        # Assuming this method is adapted or exists in the actual/mock service for SA role
        prescription_analytics = analytics_service.get_prescription_analytics(USER_ROLES['SUPER_ADMIN'], days_back=30)
        if not prescription_analytics: st.warning("No prescription analytics data."); return

        # This assumes AnalyticsDashboard is a component that can take this data
        # If not, use individual charts like PrescriptionTrendChart, MedicationUsageChart
        # For now, using the mock AnalyticsDashboard structure from prompt
        dashboard_component = AnalyticsDashboard(prescription_analytics, title="Prescription Activity (Last 30 Days)")
        dashboard_component.render_prescription_analytics() # This method needs to exist on the component

        # Additional insights if not covered by dashboard component
        top_dx = prescription_analytics.get('top_diagnoses', [])
        if top_dx: st.write("**Top Diagnoses (Overall):**", pd.DataFrame(top_dx).head())
        top_rx_meds = prescription_analytics.get('most_prescribed_medications', []) # Assuming this is part of rx_analytics for SA
        if top_rx_meds: st.write("**Top Prescribed Medications (Overall):**", pd.DataFrame(top_rx_meds).head())

    except Exception as e: st.error(f"Error rendering prescriptions tab: {e}")

def _sa_render_system_tab(): # Renamed
    st.subheader("⚙️ System Monitoring")
    try:
        analytics_service = AnalyticsService()
        system_metrics = analytics_service.get_system_performance_metrics()
        if not system_metrics: st.warning("Unable to load system metrics."); return

        st.markdown("### 🏥 System Health")
        col1, col2, col3 = st.columns(3)
        db_size_val = system_metrics.get('database', {}).get('file_size_mb', system_metrics.get('db_size_mb',0))
        col1.metric("Database Size", f"{db_size_val:.1f} MB")
        error_rate_val = system_metrics.get('error_rate', {}).get('error_rate', system_metrics.get('error_rate_last_24h',0))
        col2.metric("Error Rate (24h)", f"{error_rate_val:.1f}%", delta_color="inverse")
        col3.metric("Active Users (24h)", system_metrics.get('active_users_last_24h', 0))

        st.markdown("### 💾 Database Statistics")
        db_stats = system_metrics.get('database', {})
        if db_stats :
            st.write(f"Total Tables: {db_stats.get('table_count', db_metrics.get('db_table_count', 'N/A'))}") # Using db_metrics from original prompt
            st.write(f"Total Records (Est.): {db_stats.get('total_records', db_metrics.get('db_total_records', 'N/A')):,}")
        else: # Fallback to direct entity counts if db_stats is minimal
            counts = AnalyticsQueries.get_entity_counts()
            st.write("Record Counts (from AnalyticsQueries):")
            for entity, count in counts.items(): st.write(f"- {entity.replace('_',' ').title()}: {count:,}")
    except Exception as e: st.error(f"Error rendering system tab: {e}")

def _sa_render_dashboard_content(user: dict): # Renamed and accepts user
    """Render the main SA dashboard content with tabs"""
    try:
        tab_titles = ["📊 Overview", "👥 Users", "🏥 Patients", "📝 Prescriptions", "⚙️ System"]
        tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_titles)

        # For overview tab, pass a default time range or make it configurable within the tab
        # For now, hardcoding to 30 days for simplicity of this function call
        with tab1: _sa_render_overview_tab(days_filter=30)
        with tab2: _sa_render_users_tab()
        with tab3: _sa_render_patients_tab()
        with tab4: _sa_render_prescriptions_tab()
        with tab5: _sa_render_system_tab()

    except Exception as e:
        st.error(f"Error loading SA dashboard content: {str(e)}")

# Main function for Super Admin Dashboard page content
def render_super_admin_dashboard(user: dict):
    require_role_access([USER_ROLES['SUPER_ADMIN']])
    inject_component_css('DASHBOARD_CARDS')
    st.markdown("""
        <div class="main-header">
            <h1>🏥 Super Admin Dashboard</h1>
            <p>System Overview and Analytics</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="welcome-message">
            Welcome back, <strong>{user.get('full_name', 'Admin')}</strong>!
            Here's your system overview for {format_date_display(date.today())}.
        </div>
    """, unsafe_allow_html=True)

    _sa_render_dashboard_content(user)
# --- Super Admin Dashboard End ---

# --- Doctor's Prescriptions Page Start ---
# Copied from pages/3_doctor_prescriptions.py and adapted

def _drpres_get_mock_patients(query: str): # Prefixed
    if not query: return []
    return [
        {'id': 'p001', 'first_name': 'John', 'last_name': 'Doe', 'dob': '1985-01-15', 'gender': 'Male', 'allergies': ['Peanuts'], 'conditions': ['Hypertension']},
        {'id': 'p002', 'first_name': 'Jane', 'last_name': 'Smith', 'dob': '1992-07-22', 'gender': 'Female', 'allergies': [], 'conditions': ['Asthma', 'Migraine']},
    ]

def _drpres_get_mock_medications(query: str = ""): # Prefixed
    meds = [
        {'id': 'med001', 'name': 'Amoxicillin 250mg', 'category': 'Antibiotic'},
        {'id': 'med002', 'name': 'Paracetamol 500mg', 'category': 'Analgesic'},
        {'id': 'med003', 'name': 'Lisinopril 10mg', 'category': 'Antihypertensive'},
    ]
    if query:
        return [m for m in meds if query.lower() in m['name'].lower()]
    return meds

def _drpres_get_mock_lab_tests(query: str = ""): # Prefixed
    tests = [
        {'id': 'lab001', 'name': 'Complete Blood Count (CBC)', 'category': 'Hematology'},
        {'id': 'lab002', 'name': 'Lipid Panel', 'category': 'Chemistry'},
        {'id': 'lab003', 'name': 'Urinalysis', 'category': 'Microbiology'},
    ]
    if query:
        return [t for t in tests if query.lower() in t['name'].lower()]
    return tests

def _drpres_get_mock_prescriptions(query: str, doctor_id: str): # Prefixed
    all_prescriptions = [
        {'prescription_id': 'rx001', 'patient_name': 'John Doe', 'patient_id': 'p001', 'date_issued': '2023-10-01', 'status': 'Active', 'doctor_id': 'docRxMaster', 'medications': [{'name': 'Amoxicillin 250mg'}], 'lab_tests': []},
        {'prescription_id': 'rx002', 'patient_name': 'Jane Smith', 'patient_id': 'p002', 'date_issued': '2023-09-15', 'status': 'Expired', 'doctor_id': 'docRxMaster', 'medications': [], 'lab_tests': [{'name': 'Lipid Panel'}]},
    ]
    doctor_prescriptions = [rx for rx in all_prescriptions if rx['doctor_id'] == doctor_id]
    if not query: return doctor_prescriptions
    query_lower = query.lower()
    return [rx for rx in doctor_prescriptions if query_lower in rx['patient_name'].lower() or query_lower in rx['prescription_id'].lower()]

def _drpres_handle_ai_analysis(medications, patient_context): # Prefixed
    st.toast("🔬 AI Analysis triggered (placeholder). This may take a moment.")
    st.info("AI Analysis Complete: No critical interactions found (mock response).")

def _drpres_handle_save_prescription(prescription_data, medications, lab_tests, doctor): # Prefixed
    # format_patient_name is globally available
    patient_name = format_patient_name(st.session_state.selected_patient_for_rx.get('first_name','N/A'), st.session_state.selected_patient_for_rx.get('last_name',''))
    try:
        PrescriptionQueries.create_prescription(
            patient_id=st.session_state.selected_patient_for_rx['id'], doctor_id=doctor['id'],
            diagnosis=prescription_data['diagnosis'], chief_complaint=prescription_data['chief_complaint'],
            notes=prescription_data['general_notes'], medications=medications, lab_tests=lab_tests
        )
        show_success_message(f"Prescription for {patient_name} saved successfully!")
        st.session_state.rx_medications = []; st.session_state.rx_lab_tests = []
        return True
    except AttributeError:
        st.warning(f"Prescription for {patient_name} submitted (mock save). DB integration pending.")
        st.session_state.rx_medications = []; st.session_state.rx_lab_tests = []
        return True
    except Exception as e:
        show_error_message(f"Failed to save prescription for {patient_name}: {e}")
        return False

def _drpres_handle_prescription_action(action: str, rx_data: dict): # Prefixed
    st.toast(f"{action} for Prescription ID: {rx_data.get('prescription_id', 'N/A')} (placeholder).")
    if action == "View PDF": st.info("PDF generation placeholder.")

def _drpres_render_create_prescription_tab(doctor: dict): # Prefixed
    st.subheader("⚕️ Create New Prescription")
    st.markdown("#### 1. Select Patient")

    try: patient_search_fn = PatientQueries.search_patients
    except AttributeError: patient_search_fn = _drpres_get_mock_patients; st.warning("Patient search mock active.")

    # SearchFormComponent is globally available or mocked
    patient_search_form = SearchFormComponent(search_function=patient_search_fn, result_key_prefix="drpres_patient_search_", form_key="drpres_patient_search_form", placeholder="Search patient...", label="Find Patient")
    selected_patient_id = patient_search_form.render()

    if selected_patient_id and (not st.session_state.get('selected_patient_for_rx') or st.session_state.selected_patient_for_rx['id'] != selected_patient_id) :
        try:
            patient_data = PatientQueries.get_patient_details(selected_patient_id) if patient_search_fn != _drpres_get_mock_patients else next((p for p in _drpres_get_mock_patients("any") if p['id'] == selected_patient_id), None)
            if patient_data: st.session_state.selected_patient_for_rx = patient_data; st.session_state.rx_medications = []; st.session_state.rx_lab_tests = []
            else: show_error_message("Patient not found."); st.session_state.selected_patient_for_rx = None
        except Exception as e: show_error_message(f"Error fetching patient: {e}"); st.session_state.selected_patient_for_rx = None

    if st.session_state.get('selected_patient_for_rx'):
        patient = st.session_state.selected_patient_for_rx
        patient_name = format_patient_name(patient['first_name'], patient['last_name'])
        st.success(f"Selected Patient: **{patient_name}** (ID: {patient['id']})")
        if st.button("Clear Selected Patient", key="drpres_clear_patient_btn"):
            st.session_state.selected_patient_for_rx = None; st.session_state.rx_medications = []; st.session_state.rx_lab_tests = []; st.rerun()

        st.markdown("#### 2. Prescription Details")
        with st.form("drpres_create_rx_form"):
            chief_complaint = st.text_input("Chief Complaint", key="drpres_rx_chief")
            diagnosis = st.text_area("Diagnosis", key="drpres_rx_diag")

            try: available_meds = MedicationQueries.search_medications("")
            except AttributeError: available_meds = _drpres_get_mock_medications(); st.warning("Medication search mock active.")
            # PrescriptionMedicationComponent is globally available or mocked
            med_component = PrescriptionMedicationComponent(st.session_state.get('rx_medications', []), available_meds, "drpres_rx_med")
            st.session_state.rx_medications = med_component.render()

            try: available_tests = LabTestQueries.search_lab_tests("")
            except AttributeError: available_tests = _drpres_get_mock_lab_tests(); st.warning("Lab test search mock active.")
            # PrescriptionLabTestComponent is globally available or mocked
            test_component = PrescriptionLabTestComponent(st.session_state.get('rx_lab_tests', []), available_tests, "drpres_rx_lab")
            st.session_state.rx_lab_tests = test_component.render()

            general_notes = st.text_area("General Notes", key="drpres_rx_notes")

            if is_ai_available() and st.form_submit_button("🔬 Analyze with AI (Beta)", use_container_width=False):
                 _drpres_handle_ai_analysis(st.session_state.rx_medications, patient)

            if st.form_submit_button("💾 Save Prescription", use_container_width=True):
                if not chief_complaint or not diagnosis: show_error_message("Chief Complaint and Diagnosis are required.")
                elif not st.session_state.rx_medications and not st.session_state.rx_lab_tests: show_error_message("Add medication or lab test.")
                else:
                    rx_data = {"chief_complaint": chief_complaint, "diagnosis": diagnosis, "general_notes": general_notes}
                    if _drpres_handle_save_prescription(rx_data, st.session_state.rx_medications, st.session_state.rx_lab_tests, doctor): st.rerun()
    else: st.info("Select a patient to create a prescription.")

def _drpres_render_view_prescriptions_tab(doctor: dict): # Prefixed
    st.subheader("📋 View Existing Prescriptions")
    try: prescription_search_fn = lambda query: PrescriptionQueries.search_prescriptions(query, doctor_id=doctor['id'])
    except AttributeError: prescription_search_fn = lambda query: _drpres_get_mock_prescriptions(query, doctor['id']); st.warning("Prescription search mock active.")

    search_query_rx = st.text_input("Search by Patient Name, Rx ID...", key="drpres_rx_search_input")
    if st.button("Search Prescriptions", key="drpres_rx_search_btn") or search_query_rx:
        try: prescriptions = prescription_search_fn(search_query_rx)
        except Exception as e: show_error_message(f"Error searching: {e}"); prescriptions = []
        if not prescriptions: st.info(f"No prescriptions found for '{search_query_rx}'.")
        else:
            st.write(f"Found {len(prescriptions)} prescription(s):")
            for idx, rx in enumerate(prescriptions):
                actions = {"View PDF": lambda r=rx: _drpres_handle_prescription_action("View PDF", r), "Edit": lambda r=rx: _drpres_handle_prescription_action("Edit", r)}
                # PrescriptionCard is globally available or mocked
                try: PrescriptionCard(prescription_data=rx, actions=actions, key=f"drpres_rx_card_{rx.get('prescription_id', idx)}")
                except Exception as e: st.error(f"Error rendering card: {e}")
    else: st.info("Enter search terms to find prescriptions.")

def render_doctor_prescriptions(user: dict): # Renamed from show_prescriptions_page
    require_role_access([USER_ROLES['DOCTOR']])
    # inject_css() # Global
    st.markdown("<h1>📝 Prescription Management</h1>", unsafe_allow_html=True)
    if not user: show_error_message("User info not found."); return

    if 'selected_patient_for_rx' not in st.session_state: st.session_state.selected_patient_for_rx = None
    if 'rx_medications' not in st.session_state: st.session_state.rx_medications = []
    if 'rx_lab_tests' not in st.session_state: st.session_state.rx_lab_tests = []

    tab_titles = ["➕ Create New Prescription", "📄 View Prescriptions"]
    tab1, tab2 = st.tabs(tab_titles)
    with tab1: _drpres_render_create_prescription_tab(user)
    with tab2: _drpres_render_view_prescriptions_tab(user)
# --- Doctor's Prescriptions Page End ---

# --- Doctor's Today's Patients Page Start ---
# Copied from pages/2_doctor_todays_patients.py and adapted

# Mock data if queries or components are not ready (specific to this page's needs)
def _dtp_get_mock_patient_visits(doctor_id: str):
    """Returns a list of mock patient visit data for the given doctor ID."""
    current_date = datetime.now().date()
    return [
        {
            'visit_id': 'v001', 'patient_id': 'p001', 'doctor_id': doctor_id,
            'patient_first_name': 'John', 'patient_last_name': 'Doe', 'patient_dob': '1985-01-15', 'patient_gender': 'Male',
            'visit_time': time(9, 0), 'visit_date': current_date, 'visit_type': 'Follow-up', 'status': 'Scheduled',
            'notes': 'Routine check-up.'
        },
        {
            'visit_id': 'v002', 'patient_id': 'p002', 'doctor_id': doctor_id,
            'patient_first_name': 'Jane', 'patient_last_name': 'Smith', 'patient_dob': '1992-07-22', 'patient_gender': 'Female',
            'visit_time': time(10, 30), 'visit_date': current_date, 'visit_type': 'New Consultation', 'status': 'Scheduled',
            'notes': 'Initial consultation for ongoing symptoms.'
        },
        {
            'visit_id': 'v003', 'patient_id': 'p003', 'doctor_id': doctor_id,
            'patient_first_name': 'Alice', 'patient_last_name': 'Wonder', 'patient_dob': '1978-11-05', 'patient_gender': 'Female',
            'visit_time': time(11, 15), 'visit_date': current_date, 'visit_type': 'Check-up', 'status': 'Completed',
            'notes': 'Post-op check.'
        },
    ]

def _dtp_handle_patient_action(action_type: str, patient_visit_data: dict):
    """Placeholder function to handle actions from PatientCard."""
    # format_patient_name is assumed to be imported globally in app.py
    patient_name = format_patient_name(patient_visit_data.get('patient_first_name','N/A'), patient_visit_data.get('patient_last_name',''))
    st.toast(f"{action_type} for {patient_name} (Visit ID: {patient_visit_data.get('visit_id', 'N/A')})")
    if action_type == "View Details":
        st.session_state.selected_patient_visit = patient_visit_data
    elif action_type == "Start Consultation":
        st.session_state.active_consultation = patient_visit_data

def _dtp_render_todays_patients_list(doctor: dict): # Renamed from render_todays_patients_list
    """Renders the list of today's patients for the given doctor."""
    st.markdown("---")
    if st.button("🔄 Refresh List", key="dtp_refresh_button"): # Added key
        st.rerun()

    patient_visits = []
    try:
        patient_visits = VisitQueries.get_doctor_today_visits(doctor['id'])
        if patient_visits is None: patient_visits = []
    except AttributeError:
        st.warning("Patient data system (VisitQueries.get_doctor_today_visits) is initializing. Using mock data.")
        patient_visits = _dtp_get_mock_patient_visits(doctor['id'])
    except Exception as e:
        st.error(f"An error occurred while fetching patient data: {e}")
        patient_visits = []

    if not patient_visits:
        st.info("No patients scheduled for today.")
        return

    upcoming_visits = [v for v in patient_visits if v.get('status', 'Scheduled').lower() == 'scheduled']
    completed_visits = [v for v in patient_visits if v.get('status', 'Scheduled').lower() == 'completed']
    other_visits = [v for v in patient_visits if v.get('status', 'Scheduled').lower() not in ['scheduled', 'completed']]

    if upcoming_visits:
        st.subheader("Upcoming Appointments")
        for visit_data in upcoming_visits:
            patient_name = format_patient_name(visit_data.get('patient_first_name'), visit_data.get('patient_last_name'))
            # format_time_display is assumed to be imported globally
            visit_time_formatted = format_time_display(visit_data.get('visit_time')) if visit_data.get('visit_time') else "N/A"

            actions = {
                "View Details": lambda v=visit_data: _dtp_handle_patient_action("View Details", v),
                "Start Consultation": lambda v=visit_data: _dtp_handle_patient_action("Start Consultation", v)
            }
            card_data = {
                'name': patient_name, 'id': visit_data.get('patient_id'), 'dob': visit_data.get('patient_dob'),
                'gender': visit_data.get('patient_gender'), 'next_appointment_time': visit_time_formatted,
                'next_appointment_type': visit_data.get('visit_type'), 'status': visit_data.get('status', 'Scheduled'),
            }
            try:
                # PatientCard is assumed to be imported globally or mocked
                PatientCard(patient_data=card_data, actions=actions, key=f"dtp_patient_card_{visit_data.get('visit_id')}")
            except Exception as e: st.error(f"Could not display patient card for {patient_name}: {e}")
        st.markdown("---")

    if completed_visits:
        st.subheader("Completed Consultations Today")
        for visit_data in completed_visits:
            patient_name = format_patient_name(visit_data.get('patient_first_name'), visit_data.get('patient_last_name'))
            visit_time_formatted = format_time_display(visit_data.get('visit_time')) if visit_data.get('visit_time') else "N/A"
            actions = {"View Summary": lambda v=visit_data: _dtp_handle_patient_action("View Summary", v)}
            card_data = {
                'name': patient_name, 'id': visit_data.get('patient_id'), 'dob': visit_data.get('patient_dob'),
                'gender': visit_data.get('patient_gender'), 'last_appointment_time': visit_time_formatted,
                'last_appointment_type': visit_data.get('visit_type'), 'status': visit_data.get('status', 'Completed'),
            }
            try:
                PatientCard(patient_data=card_data, actions=actions, key=f"dtp_completed_card_{visit_data.get('visit_id')}")
            except Exception as e: st.error(f"Could not display patient card for {patient_name}: {e}")
        st.markdown("---")

    if other_visits:
        st.subheader("Other Status")
        for visit_data in other_visits: st.write(visit_data)


def render_doctor_todays_patients(user: dict): # Renamed from show_todays_patients_page
    """Main function to display the Today's Patients page."""
    require_role_access([USER_ROLES['DOCTOR']])
    # inject_css() # Global CSS usually handled once or by show_login_page if needed there
    st.markdown("<h1>📅 Today's Patients</h1>", unsafe_allow_html=True)

    # user object is passed, no need to call get_current_user() again
    if user:
        st.info(f"Displaying today's patient list for Dr. {user.get('full_name', 'N/A')}.")
        _dtp_render_todays_patients_list(user) # Call prefixed helper
    else:
        st.error("Could not retrieve doctor information. Please log in again.")
# --- Doctor's Today's Patients Page End ---

# --- Doctor's Templates Page Start ---
# Copied from pages/4_doctor_templates.py and adapted

_DRTMPL_MOCK_TEMPLATES_DB = []

def _drtmpl_initialize_mock_db(): # Prefixed
    global _DRTMPL_MOCK_TEMPLATES_DB # Use prefixed global
    if not _DRTMPL_MOCK_TEMPLATES_DB:
        _drtmpl_mock_create_template({"name": "Flu Follow-up", "category": "Follow-up", "diagnosis": "Influenza", "instructions": "Rest.", "medications": [], "lab_tests": []}, 'docTemplateUser', is_initial_setup=True)
        _drtmpl_mock_create_template({"name": "Routine Physical", "category": "General", "diagnosis": "Health Maintenance", "instructions": "Yearly check.", "medications": [], "lab_tests": []}, 'docTemplateUser', is_initial_setup=True)

def _drtmpl_get_mock_doctor_templates(doctor_id: str): # Prefixed
    return [copy.deepcopy(t) for t in _DRTMPL_MOCK_TEMPLATES_DB if t['doctor_id'] == doctor_id]

def _drtmpl_get_mock_template_by_id(template_id: str, doctor_id: str): # Prefixed
    for t in _DRTMPL_MOCK_TEMPLATES_DB:
        if t['id'] == template_id and t['doctor_id'] == doctor_id: return copy.deepcopy(t)
    return None

def _drtmpl_mock_create_template(data, doctor_id, is_initial_setup=False): # Prefixed
    global _DRTMPL_MOCK_TEMPLATES_DB
    new_id = f"tmpl_app_{len(_DRTMPL_MOCK_TEMPLATES_DB) + 1}"
    new_template = {'id': new_id, 'doctor_id': doctor_id, **data, 'created_at': datetime.now().isoformat(), 'updated_at': datetime.now().isoformat()}
    _DRTMPL_MOCK_TEMPLATES_DB.append(new_template)
    if not is_initial_setup: show_success_message(f"Mock Template '{new_template['name']}' created.")
    return new_template

def _drtmpl_mock_update_template(template_id, data, doctor_id): # Prefixed
    global _DRTMPL_MOCK_TEMPLATES_DB
    for i, t in enumerate(_DRTMPL_MOCK_TEMPLATES_DB):
        if t['id'] == template_id and t['doctor_id'] == doctor_id:
            _DRTMPL_MOCK_TEMPLATES_DB[i] = {**t, **data, 'updated_at': datetime.now().isoformat()}; return _DRTMPL_MOCK_TEMPLATES_DB[i]
    return None

def _drtmpl_mock_delete_template(template_id, doctor_id): # Prefixed
    global _DRTMPL_MOCK_TEMPLATES_DB
    original_len = len(_DRTMPL_MOCK_TEMPLATES_DB)
    _DRTMPL_MOCK_TEMPLATES_DB = [t for t in _DRTMPL_MOCK_TEMPLATES_DB if not (t['id'] == template_id and t['doctor_id'] == doctor_id)]
    return len(_DRTMPL_MOCK_TEMPLATES_DB) < original_len

def _drtmpl_handle_save_template(data, doctor_id): # Prefixed
    try: template = TemplateService.create_template(data, doctor_id)
    except AttributeError: template = _drtmpl_mock_create_template(data, doctor_id); show_warning_message("Template service mock active.")
    except Exception as e: show_error_message(f"Error: {e}"); return
    if template: show_success_message(f"Template '{template['name']}' created."); st.session_state.drtmpl_editing_template_id = None; st.session_state.drtmpl_template_form_data = {}; st.rerun()
    else: show_error_message("Failed to create template.")

def _drtmpl_handle_update_template(template_id, data, doctor_id): # Prefixed
    try: template = TemplateService.update_template(template_id, data, doctor_id)
    except AttributeError: template = _drtmpl_mock_update_template(template_id, data, doctor_id); show_warning_message("Template service mock active.")
    except Exception as e: show_error_message(f"Error: {e}"); return
    if template: show_success_message(f"Template '{template['name']}' updated."); st.session_state.drtmpl_editing_template_id = None; st.session_state.drtmpl_template_form_data = {}; st.rerun()
    else: show_error_message("Failed to update template.")

def _drtmpl_handle_delete_template(template_id, doctor_id): # Prefixed
    confirm_key = f"drtmpl_confirm_delete_{template_id}"
    if st.session_state.get(confirm_key):
        try: success = TemplateService.delete_template(template_id, doctor_id)
        except AttributeError: success = _drtmpl_mock_delete_template(template_id, doctor_id); show_warning_message("Template service mock active.")
        except Exception as e: show_error_message(f"Error: {e}"); success = False
        del st.session_state[confirm_key]
        if success: show_success_message(f"Template ID {template_id} deleted."); st.rerun()
        else: show_error_message("Failed to delete template.")
    else: st.session_state[confirm_key] = True; show_warning_message(f"Confirm delete template ID {template_id}?"); st.rerun()

def _drtmpl_handle_duplicate_template(template_id, doctor_id): # Prefixed
    st.session_state.drtmpl_duplicating_template_id = template_id; st.rerun()

def _drtmpl_process_duplication(original_template_id, new_name, doctor_id): # Prefixed
    try:
        original_template = TemplateQueries.get_template_details(original_template_id, doctor_id) if DB_QUERIES_AVAILABLE else _drtmpl_get_mock_template_by_id(original_template_id, doctor_id)
        if not original_template: show_error_message("Original template not found."); return
        duplicated_data = {k: v for k, v in original_template.items() if k not in ['id', 'created_at', 'updated_at', 'doctor_id']}
        duplicated_data['name'] = new_name
        try: new_template = TemplateService.create_template(duplicated_data, doctor_id)
        except AttributeError: new_template = _drtmpl_mock_create_template(duplicated_data, doctor_id); show_warning_message("Template service mock active.")
        if new_template: show_success_message(f"Template duplicated as '{new_name}'.")
    except Exception as e: show_error_message(f"Error duplicating: {e}")
    finally: st.session_state.drtmpl_duplicating_template_id = None; st.rerun()

def _drtmpl_render_view_templates_section(doctor: dict): # Prefixed
    st.subheader("My Templates")
    if st.session_state.get('drtmpl_duplicating_template_id'):
        orig_id = st.session_state.drtmpl_duplicating_template_id
        orig_tmpl = TemplateQueries.get_template_details(orig_id, doctor['id']) if DB_QUERIES_AVAILABLE else _drtmpl_get_mock_template_by_id(orig_id, doctor['id'])
        new_name_val = f"{orig_tmpl['name']} (Copy)" if orig_tmpl else "New Template Name"
        st.text_input("Name for duplicated template:", value=new_name_val, key="drtmpl_new_template_name")
        c1,c2 = st.columns(2)
        if c1.button("✅ Confirm Duplicate", key="drtmpl_confirm_dup_btn"): _drtmpl_process_duplication(orig_id, st.session_state.drtmpl_new_template_name, doctor['id'])
        if c2.button("❌ Cancel Duplicate", key="drtmpl_cancel_dup_btn"): st.session_state.drtmpl_duplicating_template_id = None; st.rerun()
        return

    if st.button("➕ Create New Template", key="drtmpl_create_new_btn"):
        st.session_state.drtmpl_editing_template_id = 'new'
        st.session_state.drtmpl_template_form_data = {"name": "", "category": TEMPLATE_CONFIG.get('CATEGORIES', ["General"])[0], "description": "", "diagnosis": "", "instructions": "", "medications": [], "lab_tests": []}
        st.rerun()
    st.markdown("---")

    try: templates = TemplateQueries.get_doctor_templates(doctor['id'])
    except AttributeError: templates = _drtmpl_get_mock_doctor_templates(doctor['id']); st.warning("Template query mock active.")
    except Exception as e: show_error_message(f"Error fetching templates: {e}"); templates = []

    if not templates: st.info("No templates created yet."); return
    for tmpl in templates:
        actions = {"Edit": lambda t=tmpl: _drtmpl_edit_template_action(t), "Delete": lambda t_id=tmpl['id']: _drtmpl_handle_delete_template(t_id, doctor['id']), "Duplicate": lambda t_id=tmpl['id']: _drtmpl_handle_duplicate_template(t_id, doctor['id'])}
        confirm_del = bool(st.session_state.get(f"drtmpl_confirm_delete_{tmpl['id']}"))
        try: TemplateCard(template_data=tmpl, actions=actions, key=f"drtmpl_card_{tmpl['id']}", show_confirm_delete=confirm_del)
        except TypeError: TemplateCard(template_data=tmpl, actions=actions, key=f"drtmpl_card_{tmpl['id']}"); \
                          if confirm_del: st.caption("Confirm Delete?")
        except Exception as e: st.error(f"Error rendering card {tmpl.get('name')}: {e}")
        st.markdown("---")

def _drtmpl_edit_template_action(template_data): # Prefixed
    st.session_state.drtmpl_editing_template_id = template_data['id']
    st.session_state.drtmpl_template_form_data = copy.deepcopy(template_data)
    if 'medications' not in st.session_state.drtmpl_template_form_data or st.session_state.drtmpl_template_form_data['medications'] is None: st.session_state.drtmpl_template_form_data['medications'] = []
    if 'lab_tests' not in st.session_state.drtmpl_template_form_data or st.session_state.drtmpl_template_form_data['lab_tests'] is None: st.session_state.drtmpl_template_form_data['lab_tests'] = []
    st.rerun()

def _drtmpl_render_edit_template_section(doctor: dict): # Prefixed
    form_data = st.session_state.drtmpl_template_form_data
    is_new = st.session_state.drtmpl_editing_template_id == 'new'
    st.subheader("Create New Template" if is_new else f"Edit Template: {form_data.get('name', '')}")

    with st.form("drtmpl_template_form"):
        form_data['name'] = st.text_input("Template Name", value=form_data.get('name', ''))
        cats = TEMPLATE_CONFIG.get('CATEGORIES', ["General", "Follow-up"])
        curr_cat = form_data.get('category', cats[0]); cat_idx = cats.index(curr_cat) if curr_cat in cats else 0
        form_data['category'] = st.selectbox("Category", options=cats, index=cat_idx)
        form_data['description'] = st.text_area("Description", value=form_data.get('description', ''))
        form_data['diagnosis'] = st.text_area("Diagnosis", value=form_data.get('diagnosis', ''))
        form_data['instructions'] = st.text_area("Instructions", value=form_data.get('instructions', ''))
        if 'medications' not in form_data or not isinstance(form_data['medications'], list): form_data['medications'] = []
        form_data['medications'] = st.data_editor(form_data['medications'], num_rows="dynamic", key="drtmpl_med_editor", column_config={"name":"Medication", "dosage":"Dosage", "frequency":"Frequency", "duration":"Duration"})
        if 'lab_tests' not in form_data or not isinstance(form_data['lab_tests'], list): form_data['lab_tests'] = []
        form_data['lab_tests'] = st.data_editor(form_data['lab_tests'], num_rows="dynamic", key="drtmpl_lab_editor", column_config={"name":"Test Name", "instructions":"Instructions"})

        c1,c2=st.columns(2)
        if c1.form_submit_button("Save Template" if is_new else "Update Template", use_container_width=True):
            if not form_data['name']: show_error_message("Name is required.")
            else:
                if is_new: _drtmpl_handle_save_template(form_data, doctor['id'])
                else: _drtmpl_handle_update_template(st.session_state.drtmpl_editing_template_id, form_data, doctor['id'])
        if c2.form_submit_button("Cancel", type="secondary", use_container_width=True):
            st.session_state.drtmpl_editing_template_id = None; st.session_state.drtmpl_template_form_data = {}; st.rerun()

def render_doctor_templates(user: dict): # Renamed from show_templates_page
    require_role_access([USER_ROLES['DOCTOR']])
    # inject_css() # Global
    st.markdown("<h1>📋 Prescription Templates</h1>", unsafe_allow_html=True)
    if not user: show_error_message("User info not found."); return

    # Initialize session state keys specific to this page, prefixed
    for key, default_val in [('drtmpl_editing_template_id', None), ('drtmpl_template_form_data', {}), ('drtmpl_duplicating_template_id', None)]:
        if key not in st.session_state: st.session_state[key] = default_val

    # Initialize mock DB for templates if not using real queries
    if not DB_QUERIES_AVAILABLE or not hasattr(TemplateQueries, 'get_doctor_templates'): _drtmpl_initialize_mock_db()


    if st.session_state.drtmpl_editing_template_id is not None: _drtmpl_render_edit_template_section(user)
    else: _drtmpl_render_view_templates_section(user)
# --- Doctor's Templates Page End ---

# --- Doctor's Medications Page Start ---
# Copied from pages/5_doctor_medications.py and adapted

_DRMED_MOCK_MEDICATIONS_DB = [ # Prefixed global mock DB
    {'id': 'med001', 'name': 'Amoxicillin 250mg', 'generic_name': 'Amoxicillin', 'drug_class': 'Penicillin Antibiotics', 'form': 'Capsule', 'strength': '250mg', 'manufacturer': 'Generic Pharma', 'indications': ['Bacterial infections'], 'contraindications': ['Penicillin allergy'], 'is_otc': False, 'storage_conditions': 'Room temperature', 'notes': 'Complete full course.', 'created_by': 'system'},
    {'id': 'med002', 'name': 'Paracetamol 500mg', 'generic_name': 'Acetaminophen', 'drug_class': 'Analgesics', 'form': 'Tablet', 'strength': '500mg', 'manufacturer': 'HealthWell', 'indications': ['Pain relief', 'Fever reduction'], 'contraindications': ['Severe liver disease'], 'is_otc': True, 'storage_conditions': 'Room temperature', 'notes': 'Max 4g/day.', 'created_by': 'system'},
    # Add more from original file if needed, this is just a sample
]
_DRMED_MOCK_FAVORITE_MEDS = {} # doctor_id: {med_id1, med_id2}

def _drmed_get_mock_medications(search_term: str, drug_class: str, favorites_only: bool, doctor_id: str): # Prefixed
    results = copy.deepcopy(_DRMED_MOCK_MEDICATIONS_DB)
    doctor_favorites = _DRMED_MOCK_FAVORITE_MEDS.get(doctor_id, set())
    if search_term:
        search_term_lower = search_term.lower()
        results = [m for m in results if search_term_lower in m['name'].lower() or search_term_lower in m.get('generic_name','').lower()]
    if drug_class != "All": results = [m for m in results if m.get('drug_class') == drug_class]
    for med in results: med['is_favorite'] = med['id'] in doctor_favorites
    if favorites_only: results = [m for m in results if m['is_favorite']]
    return results

def _drmed_mock_toggle_favorite_medication(medication_id: str, doctor_id: str): # Prefixed
    if doctor_id not in _DRMED_MOCK_FAVORITE_MEDS: _DRMED_MOCK_FAVORITE_MEDS[doctor_id] = set()
    is_currently_favorite = medication_id in _DRMED_MOCK_FAVORITE_MEDS[doctor_id]
    if is_currently_favorite: _DRMED_MOCK_FAVORITE_MEDS[doctor_id].remove(medication_id); return False
    else: _DRMED_MOCK_FAVORITE_MEDS[doctor_id].add(medication_id); return True

def _drmed_handle_toggle_favorite(medication_id: str, doctor_id: str, is_currently_favorite: bool): # Prefixed
    try:
        new_fav_status = MedicationQueries.toggle_favorite_medication(medication_id, doctor_id, not is_currently_favorite) if DB_QUERIES_AVAILABLE else _drmed_mock_toggle_favorite_medication(medication_id, doctor_id)
        action = "added to" if new_fav_status else "removed from"
        show_success_message(f"Medication {action} favorites.")
    except AttributeError: # Fallback for mock if toggle_favorite_medication doesn't take 3 args
        new_fav_status = _drmed_mock_toggle_favorite_medication(medication_id, doctor_id)
        action = "added to" if new_fav_status else "removed from"
        show_warning_message(f"Medication {action} favorites (mock toggle).")
    except Exception as e: show_error_message(f"Error updating favorite status: {e}")
    st.rerun()

def _drmed_render_medication_search_and_filters(): # Prefixed
    st.subheader("🔍 Search & Filter Medications")
    # Use a unique key for session state to avoid conflicts if other pages use similar names
    st.session_state.drmed_search_term = st.text_input("Search by Name or Generic Name:", value=st.session_state.get('drmed_search_term', ""), key="drmed_search_input")

    filter_cols = st.columns([2, 1, 1])
    with filter_cols[0]:
        available_drug_classes = DRUG_CLASSES if isinstance(DRUG_CLASSES, list) and DRUG_CLASSES else ["Analgesics", "Other"]
        all_drug_classes_options = ["All"] + sorted(list(set(available_drug_classes)))
        current_drug_class = st.session_state.get('drmed_drug_class', "All")
        idx = all_drug_classes_options.index(current_drug_class) if current_drug_class in all_drug_classes_options else 0
        st.session_state.drmed_drug_class = st.selectbox("Filter by Drug Class:", options=all_drug_classes_options, index=idx, key="drmed_drug_class_filter")
    with filter_cols[1]:
        st.session_state.drmed_show_favorites = st.checkbox("Show Only My Favorites ⭐", value=st.session_state.get('drmed_show_favorites', False), key="drmed_favorites_filter")
    with filter_cols[2]:
        st.markdown("<div>&nbsp;</div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh / Apply", key="drmed_refresh_btn", use_container_width=True): st.rerun()
    st.markdown("---")

def _drmed_render_medications_list(doctor: dict): # Prefixed
    st.subheader("Medication Listings")
    search_term = st.session_state.get('drmed_search_term', "")
    drug_class_filter = st.session_state.get('drmed_drug_class', "All")
    favorites_only_filter = st.session_state.get('drmed_show_favorites', False)

    try:
        medications_list = MedicationQueries.search_medications(search_term=search_term, drug_class=drug_class_filter if drug_class_filter != "All" else None, favorites_only=favorites_only_filter, doctor_id=doctor['id'])
    except AttributeError:
        st.warning("Medication query service mock active.")
        medications_list = _drmed_get_mock_medications(search_term, drug_class_filter, favorites_only_filter, doctor['id'])
    except Exception as e: show_error_message(f"Error fetching medications: {e}"); medications_list = []

    if not medications_list: st.info("No medications found matching your criteria."); return
    num_columns = 3; item_cols = st.columns(num_columns)
    for i, med_item_data in enumerate(medications_list):
        with item_cols[i % num_columns]:
            is_fav = med_item_data.get('is_favorite', False)
            fav_label = "🌟 Unfavorite" if is_fav else "⭐ Favorite"
            card_actions = {fav_label: lambda m_id=med_item_data['id'], d_id=doctor['id'], current_fav=is_fav: _drmed_handle_toggle_favorite(m_id, d_id, current_fav),
                            "View Details": lambda m_name=med_item_data['name']: st.toast(f"Details for {m_name} (placeholder).")}
            try: MedicationCard(medication_data=med_item_data, actions=card_actions, key=f"drmed_card_{med_item_data['id']}")
            except Exception as e: st.error(f"Error rendering card for {med_item_data.get('name')}: {e}")

def render_doctor_medications(user: dict): # Renamed from show_medications_page
    require_role_access([USER_ROLES['DOCTOR']])
    # inject_css() # Global
    st.markdown("<h1>💊 Medications Database</h1>", unsafe_allow_html=True)

    # Initialize session state keys specific to this page
    for key, default_val in [('drmed_search_term', ""), ('drmed_drug_class', "All"), ('drmed_show_favorites', False)]:
        if key not in st.session_state: st.session_state[key] = default_val

    # Initialize mock favorites if needed
    if not DB_QUERIES_AVAILABLE or not hasattr(MedicationQueries, 'toggle_favorite_medication'):
        global _DRMED_MOCK_FAVORITE_MEDS # Ensure it's accessible for the init
        if user['id'] not in _DRMED_MOCK_FAVORITE_MEDS: _DRMED_MOCK_FAVORITE_MEDS[user['id']] = set()
        # Example: _drmed_mock_toggle_favorite_medication('med001', user['id']) # Add a default favorite for testing

    _drmed_render_medication_search_and_filters()
    _drmed_render_medications_list(user)
# --- Doctor's Medications Page End ---

# --- Doctor's Today's Patients Page Start ---

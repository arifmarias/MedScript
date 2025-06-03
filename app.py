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
# from pages.d2_doctor_todays_patients import show_todays_patients_page # Will be MOVED LOCALLY
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


# Updated database queries import to include all necessary for SA Dashboard
from database.queries import (
    DashboardQueries, TemplateQueries, VisitQueries, PatientQueries,
    AnalyticsQueries, UserQueries, PrescriptionQueries, get_entity_counts
)
# Updated formatters import
from utils.formatters import format_date_display, format_time_display, format_percentage, format_currency, format_patient_name
# from utils.helpers import show_error_message, show_success_message, show_warning_message # Assumed globally available
from datetime import time # Added for _dtp_get_mock_patient_visits

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
            render_super_admin_dashboard(current_user) # Call the new local function
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

# Definition of show_login_page() MOVED HERE

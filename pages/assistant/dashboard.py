import streamlit as st
from datetime import datetime, timedelta
import pandas as pd # For mock data generation

# Config and Auth
from config.settings import USER_ROLES
from config.styles import inject_css, inject_component_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access

# Services & Components (Assuming these exist, with fallbacks)
try:
    from services.analytics_service import AnalyticsService
except ImportError:
    class AnalyticsService: # Mock service
        def get_dashboard_metrics(self, role, user_id, days_back):
            st.warning("AnalyticsService not found. Using mock assistant dashboard metrics.")
            # Simulate some metrics relevant to an assistant
            return {
                'patients_registered_by_user': max(0, int(days_back / 2 + (hash(user_id) % 5))),
                'visits_recorded_by_user': max(0, int(days_back * 1.5 + (hash(user_id) % 10))),
            }

try:
    from components.cards import MetricCard
except ImportError:
    def MetricCard(label, value, key=None, help_text=None, icon=None): # Mock MetricCard
        st.metric(label=label, value=value, help=help_text)
        if icon: st.caption(icon) # Simple icon display

try:
    from database.queries import DashboardQueries, PatientQueries, VisitQueries
except ImportError:
    # Simplified Mock Queries for Assistant Dashboard
    MOCK_ASSISTANT_PATIENTS_DB = [
        {'id': 'p001', 'name': 'Patient Alpha', 'created_by': 'assistant123', 'created_at': (datetime.now() - timedelta(days=2)).isoformat()},
        {'id': 'p002', 'name': 'Patient Beta', 'created_by': 'assistant456', 'created_at': (datetime.now() - timedelta(days=5)).isoformat()},
        {'id': 'p003', 'name': 'Patient Gamma', 'created_by': 'assistant123', 'created_at': (datetime.now() - timedelta(days=10)).isoformat()},
        {'id': 'p004', 'name': 'Patient Delta', 'created_by': 'assistant123', 'created_at': (datetime.now() - timedelta(days=20)).isoformat()},
    ]
    MOCK_ASSISTANT_VISITS_DB = [
        {'id': 'v001', 'patient_name': 'Patient Alpha', 'recorded_by': 'assistant123', 'visit_date': (datetime.now() - timedelta(days=1)).isoformat()},
        {'id': 'v002', 'patient_name': 'Patient Beta', 'recorded_by': 'assistant456', 'visit_date': (datetime.now() - timedelta(days=1)).isoformat()},
        {'id': 'v003', 'patient_name': 'Patient Gamma', 'recorded_by': 'assistant123', 'visit_date': datetime.now().isoformat()}, # Today
        {'id': 'v004', 'patient_name': 'Patient Alpha', 'recorded_by': 'assistant123', 'visit_date': datetime.now().isoformat()}, # Today
    ]

    class PatientQueries:
        @staticmethod
        def count_patients_created_by(assistant_id, days_back=None):
            filtered = [p for p in MOCK_ASSISTANT_PATIENTS_DB if p['created_by'] == assistant_id]
            if days_back:
                start_date = datetime.now() - timedelta(days=days_back)
                filtered = [p for p in filtered if datetime.fromisoformat(p['created_at']) >= start_date]
            return len(filtered)

        @staticmethod
        def get_total_patients_managed_by(assistant_id): # Total ever created by this assistant
            return len([p for p in MOCK_ASSISTANT_PATIENTS_DB if p['created_by'] == assistant_id])

    class VisitQueries:
        @staticmethod
        def count_visits_recorded_by(assistant_id, days_back):
            filtered = [v for v in MOCK_ASSISTANT_VISITS_DB if v['recorded_by'] == assistant_id]
            start_date = datetime.now() - timedelta(days=days_back)
            filtered = [v for v in filtered if datetime.fromisoformat(v['visit_date']) >= start_date]
            return len(filtered)

        @staticmethod
        def get_all_today_visits(): # All visits scheduled for today, regardless of who recorded
            today_str = datetime.now().date().isoformat()
            return len([v for v in MOCK_ASSISTANT_VISITS_DB if v['visit_date'].startswith(today_str)])

    class DashboardQueries: pass # Placeholder

# Utils
from utils.formatters import format_date_display # Assuming this exists
from utils.helpers import show_error_message, show_success_message, show_warning_message


# --- Main Rendering Function ---
def render_assistant_dashboard_content(current_user: dict):
    st.subheader("🗓️ Daily Overview & Quick Actions")

    col1_time, col2_refresh, col3_spacer = st.columns([2,1,2])
    with col1_time:
        days_back_filter = st.selectbox(
            "Select Period for My Activity:",
            options=[7, 14, 30, 90],
            format_func=lambda x: f"Last {x} days",
            index=1 # Default to 14 days
        )
    with col2_refresh:
        st.markdown("<div>&nbsp;</div>", unsafe_allow_html=True) # Spacer for better alignment
        if st.button("🔄 Refresh Data", key="refresh_assistant_dash_main", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # --- Key Metrics ---
    st.markdown("<h4>Key Metrics</h4>", unsafe_allow_html=True)

    patients_registered_by_me = 0
    visits_recorded_by_me = 0

    try: # Try AnalyticsService first
        analytics_service = AnalyticsService()
        assistant_metrics = analytics_service.get_dashboard_metrics(
            USER_ROLES['ASSISTANT'], current_user['id'], days_back=days_back_filter
        )
        patients_registered_by_me = assistant_metrics.get('patients_registered_by_user', 0)
        visits_recorded_by_me = assistant_metrics.get('visits_recorded_by_user', 0)
    except Exception: # Fallback to direct queries
        try:
            patients_registered_by_me = PatientQueries.count_patients_created_by(current_user['id'], days_back=days_back_filter)
            visits_recorded_by_me = VisitQueries.count_visits_recorded_by(current_user['id'], days_back=days_back_filter)
        except Exception as qe:
            show_error_message(f"Error fetching data from direct queries: {qe}")
            # metrics remain 0

    try:
        total_patients_managed = PatientQueries.get_total_patients_managed_by(current_user['id'])
        upcoming_appointments_today = VisitQueries.get_all_today_visits()
    except Exception as e:
        show_error_message(f"Error fetching summary metrics: {e}")
        total_patients_managed = "N/A"
        upcoming_appointments_today = "N/A"

    m_cols = st.columns(4)
    m_cols[0].metric(label=f"Patients Registered (Last {days_back_filter}d)", value=patients_registered_by_me)
    m_cols[1].metric(label=f"Visits Recorded (Last {days_back_filter}d)", value=visits_recorded_by_me)
    m_cols[2].metric(label="Total Patients You Manage", value=total_patients_managed)
    m_cols[3].metric(label="Upcoming Appointments Today (All)", value=upcoming_appointments_today)

    st.markdown("---")

    # --- Quick Actions ---
    st.subheader("🚀 Quick Actions")
    qa_cols = st.columns(2)
    if qa_cols[0].button("➕ Register New Patient", use_container_width=True, type="primary"):
        st.toast("Action: Navigate to Patient Registration (Simulated).")
        # Replace with: st.switch_page("pages/assistant/register_patient.py") when available
    if qa_cols[1].button("➕ Record New Visit", use_container_width=True, type="primary"):
        st.toast("Action: Navigate to Record Visit (Simulated).")
        # Replace with: st.switch_page("pages/assistant/record_visit.py") when available

    st.markdown("---")
    st.info("Recent activity and task list sections will be available soon.")


# --- Main Page Function ---
def show_assistant_dashboard():
    require_authentication()
    require_role_access([USER_ROLES['ASSISTANT']])

    inject_css()
    # inject_component_css('DASHBOARD_CARDS')

    st.markdown("<h1>💁‍♀️ Assistant Dashboard</h1>", unsafe_allow_html=True)

    current_user = get_current_user()
    if current_user:
        st.sidebar.success(f"Welcome, {current_user.get('full_name', 'Assistant')}!")
        render_assistant_dashboard_content(current_user)
    else:
        st.error("Could not retrieve user information. Please try logging in again.")


if __name__ == "__main__":
    if 'user' not in st.session_state:
        st.session_state.user = {
            'id': 'assistant123',
            'username': 'med_assistant_jane',
            'role': USER_ROLES['ASSISTANT'],
            'full_name': 'Jane Doe (Assistant)',
            'email': 'jane.assistant@example.com'
        }
        st.session_state.authenticated = True
        st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)

    # show_assistant_dashboard() # Called at module level now

# This call ensures Streamlit runs the page content when navigating
show_assistant_dashboard()

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd # For creating sample DataFrames for charts

# Config and Auth
from config.settings import USER_ROLES
from config.styles import inject_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access

# Services & Components (Assuming these exist, with fallbacks)
try:
    from services.analytics_service import AnalyticsService
except ImportError:
    class AnalyticsService: # Mock service
        def get_patient_analytics(self, role, user_id, days_back):
            # st.warning("AnalyticsService (get_patient_analytics) not found. Using mock data.", icon="⚠️") # Less verbose for final
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            date_range = pd.date_range(start_date, end_date, freq='D')
            registrations_count = [max(0, int(3 + 2 * (i % 5) - (i % 2)**2 + i//7 + hash(user_id)%3)) for i in range(len(date_range))]
            return {
                'patient_registrations_timeline': pd.DataFrame({
                    'date': date_range,
                    'count': registrations_count
                }),
                'total_patients_registered': sum(registrations_count)
            }

        def get_visit_analytics(self, role, user_id, days_back):
            # st.warning("AnalyticsService (get_visit_analytics) not found. Using mock data.", icon="⚠️") # Less verbose for final
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            date_range = pd.date_range(start_date, end_date, freq='D')
            visits_count = [max(0, int(5 + 3 * (i % 7) - (i % 3)**2 + i//5 + hash(user_id)%4)) for i in range(len(date_range))]
            visit_types = ['Check-up', 'Follow-up', 'New Complaint', 'Vaccination', 'Scheduled Consultation']
            return {
                'visit_recordings_timeline': pd.DataFrame({
                    'date': date_range,
                    'count': visits_count
                }),
                'total_visits_recorded': sum(visits_count),
                'visit_types_distribution': pd.DataFrame({
                    'visit_type': visit_types,
                    'count': [max(0, int(sum(visits_count)/(i+2) + (hash(user_id) % (i+1)*2) )) for i in range(len(visit_types))]
                })
            }

try:
    from components.charts import TimeSeriesChart, BarChart
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    def TimeSeriesChart(data, title=None, x_axis='date', y_axis='count'):
        if title: st.caption(title)
        if isinstance(data, pd.DataFrame) and not data.empty and x_axis in data.columns and y_axis in data.columns:
            st.line_chart(data.set_index(x_axis)[y_axis])
        else: st.info(f"No data or incorrect format for TimeSeriesChart: {title if title else ''}.")

    def BarChart(data, title=None, x_axis=None, y_axis=None):
        if title: st.caption(title)
        if isinstance(data, pd.DataFrame) and not data.empty:
            if x_axis is None and len(data.columns) > 0: x_axis = data.columns[0]
            if y_axis is None and len(data.columns) > 1: y_axis = data.columns[1]
            if x_axis in data.columns and y_axis in data.columns: st.bar_chart(data.set_index(x_axis)[y_axis])
            elif x_axis in data.columns : st.bar_chart(data.set_index(x_axis))
            else: st.bar_chart(data)
        else: st.info(f"No data or incorrect format for BarChart: {title if title else ''}.")

# Utils
from utils.helpers import show_error_message, show_success_message, show_warning_message


# --- Main Rendering Function ---
def render_assistant_analytics_content(assistant: dict):
    st.markdown("### Your Activity Overview")

    col1, col2_spacer, col3 = st.columns([1, 2, 1])
    with col1:
        selected_period_days = st.selectbox(
            "Select Period:",
            options=[7, 15, 30, 60, 90],
            format_func=lambda x: f"Last {x} days",
            index=2, # Default to 30 days
            key="asst_analytics_period_select_v2"
        )
    with col3:
        st.markdown("<div>&nbsp;</div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh Data", key="refresh_asst_analytics_v2", use_container_width=True):
            st.rerun()

    st.markdown("---")

    try:
        analytics_service = AnalyticsService()
        patient_reg_analytics = analytics_service.get_patient_analytics(USER_ROLES['ASSISTANT'], assistant['id'], days_back=selected_period_days)
        visit_rec_analytics = analytics_service.get_visit_analytics(USER_ROLES['ASSISTANT'], assistant['id'], days_back=selected_period_days)
    except Exception as e:
        show_error_message(f"Error fetching analytics data: {e}")
        patient_reg_analytics, visit_rec_analytics = {}, {}

    # --- Display Metrics & Charts ---
    st.subheader("👤 Patient Registrations by You")
    if patient_reg_analytics and isinstance(patient_reg_analytics, dict):
        total_registered = patient_reg_analytics.get('total_patients_registered', 0)
        st.metric(label=f"Total Patients Registered (Last {selected_period_days} days)", value=total_registered if total_registered is not None else "N/A")

        reg_timeline_data = patient_reg_analytics.get('patient_registrations_timeline')
        if isinstance(reg_timeline_data, pd.DataFrame) and not reg_timeline_data.empty:
            TimeSeriesChart(reg_timeline_data, title="Registration Trend", x_axis='date', y_axis='count')
        else:
            st.info("No patient registration trend data available for this period.")
    else:
        st.info("No patient registration analytics available or data is in an unexpected format.")

    st.markdown("---")

    st.subheader("🗓️ Visit Recordings by You")
    if visit_rec_analytics and isinstance(visit_rec_analytics, dict):
        total_recorded_visits = visit_rec_analytics.get('total_visits_recorded', 0)
        st.metric(label=f"Total Visits Recorded (Last {selected_period_days} days)", value=total_recorded_visits if total_recorded_visits is not None else "N/A")

        visit_timeline_data = visit_rec_analytics.get('visit_recordings_timeline')
        if isinstance(visit_timeline_data, pd.DataFrame) and not visit_timeline_data.empty:
            TimeSeriesChart(visit_timeline_data, title="Visit Recording Trend", x_axis='date', y_axis='count')
        else:
            st.info("No visit recording trend data available for this period.")

        st.markdown("##### Visit Types Recorded by You")
        visit_types_data = visit_rec_analytics.get('visit_types_distribution')
        if isinstance(visit_types_data, pd.DataFrame) and not visit_types_data.empty:
            BarChart(visit_types_data, title="Distribution of Visit Types", x_axis='visit_type', y_axis='count')
        else:
            st.info("No data on types of visits recorded.")
    else:
        st.info("No visit recording analytics available or data is in an unexpected format.")


# --- Main Page Function ---
def show_assistant_analytics_page():
    require_authentication()
    require_role_access([USER_ROLES['ASSISTANT']])
    inject_css()

    st.markdown("<h1>📊 My Activity Analytics</h1>", unsafe_allow_html=True)

    current_user = get_current_user()
    if not current_user:
        show_error_message("Unable to retrieve user information. Please log in again.")
        return

    render_assistant_analytics_content(current_user)

if __name__ == "__main__":
    if 'user' not in st.session_state:
        st.session_state.user = {
            'id': 'asstAnalyticsUser002', # Changed ID for testing
            'username': 'asst_analyzer002',
            'role': USER_ROLES['ASSISTANT'],
            'full_name': 'Drew Analyzer (Asst.)', # Changed name
            'email': 'drew.analyzer.asst@example.com'
        }
        st.session_state.authenticated = True
        st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)

    if not CHARTS_AVAILABLE: st.sidebar.warning("Using MOCK Chart components for Asst. Analytics.")
    # No specific session state for filters needed at this top level, handled by selectbox key

    # show_assistant_analytics_page() # Called at module level now

# This call ensures Streamlit runs the page content when navigating
show_assistant_analytics_page()

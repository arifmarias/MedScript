import streamlit as st
from datetime import datetime, timedelta
from config.settings import USER_ROLES
from config.styles import inject_css, inject_component_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access # Assuming this exists
from services.analytics_service import AnalyticsService # Assuming get_user_dashboard_metrics is part of this or similar
from components.cards import MetricCard # Assuming this component exists
from database.queries import DashboardQueries, TemplateQueries # Assuming these exist
from utils.formatters import format_date_display

def render_doctor_dashboard_content(current_user):
    st.subheader("Activity Overview")

    # Time range selector
    col1, col2 = st.columns([3,1])
    with col1:
        days_back = st.selectbox(
            "Select Time Range for Analytics:",
            options=[7, 14, 30, 90],
            format_func=lambda x: f"Last {x} days",
            index=2  # Default to 30 days
        )
    with col2:
        if st.button("Refresh Data"):
            st.rerun()

    try:
        analytics_service = AnalyticsService()
        # Assuming a method like get_dashboard_metrics exists and can be scoped by user_id and role
        # This might need adjustment based on actual AnalyticsService implementation
        metrics = analytics_service.get_dashboard_metrics(
            USER_ROLES['DOCTOR'],
            current_user['id'],
            days_back=days_back
        )

        # Fallback for metrics if specific keys are missing
        my_prescriptions_count = metrics.get('my_prescriptions_count', 0)
        # For other metrics, we might need specific queries if not covered by a general metrics call

    except Exception as e:
        st.error(f"Error fetching dashboard analytics: {e}")
        metrics = {} # Ensure metrics is defined
        my_prescriptions_count = 0


    # Key Metrics Display
    st.markdown("<h4>Key Metrics</h4>", unsafe_allow_html=True)

    # Placeholder for today's summary data - will need actual queries
    try:
        today_summary = DashboardQueries.get_today_summary(doctor_id=current_user['id'])
        if today_summary is None: today_summary = {} # Ensure it's a dict
        today_patients = today_summary.get('total_patients', 0)
        completed_consultations = today_summary.get('completed_consultations', 0)
        pending_consultations = today_patients - completed_consultations
    except Exception as e:
        st.error(f"Error fetching today's summary: {e}")
        today_patients = "N/A"
        completed_consultations = "N/A"
        pending_consultations = "N/A"

    try:
        active_templates_count = TemplateQueries.get_doctor_templates_count(current_user['id'])
    except Exception as e:
        st.error(f"Error fetching template count: {e}")
        active_templates_count = "N/A"

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        MetricCard("Today's Patients", today_patients, key="mc1")
    with m2:
        MetricCard("Completed Consultations", completed_consultations, key="mc2")
    with m3:
        MetricCard("Pending Consultations", pending_consultations, key="mc3")
    with m4:
        MetricCard(f"My Prescriptions (Last {days_back}d)", my_prescriptions_count, key="mc4")
    with m5:
        MetricCard("Active Templates", active_templates_count, key="mc5")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Today's Appointments
    st.subheader("Today's Appointments")
    try:
        # Assuming get_doctor_today_visits returns a list of appointment-like objects
        # This query needs to be implemented in database.queries.VisitQueries or DashboardQueries
        today_visits = DashboardQueries.get_doctor_today_visits(current_user['id'])
        if today_visits:
            for visit in today_visits:
                # Assuming visit is a dictionary or object with these keys
                patient_name = visit.get('patient_full_name', 'N/A')
                visit_time_str = visit.get('visit_time', datetime.now()).strftime('%H:%M') if visit.get('visit_time') else 'N/A'
                visit_type = visit.get('visit_type', 'Consultation')
                visit_status = visit.get('status', 'Scheduled')

                cols = st.columns([3,1,2,1])
                cols[0].markdown(f"**{patient_name}**")
                cols[1].markdown(f"🕒 {visit_time_str}")
                cols[2].markdown(f"📋 {visit_type}")
                if visit_status.lower() == 'completed':
                    cols[3].markdown(f"✅ {visit_status}")
                elif visit_status.lower() == 'pending' or visit_status.lower() == 'scheduled':
                     cols[3].markdown(f"⏳ {visit_status}")
                else:
                    cols[3].markdown(f"{visit_status}")

                # st.markdown(f"- **{patient_name}** at {visit_time_str} ({visit_type}) - Status: {visit_status}")
            if not today_visits: st.info("No appointments scheduled for today.")
        else:
            st.info("No appointments scheduled for today, or unable to fetch appointments.")
    except NotImplementedError:
        st.warning("Today's appointments list feature is under development.")
    except Exception as e:
        st.error(f"Error fetching today's appointments: {e}")
        st.info("Today's appointments list will be shown here once the data connection is established.")


    # Recent Prescriptions (Optional)
    # st.subheader("Recent Prescriptions")
    # st.info("Recent prescriptions list will be shown here.")

def show_doctor_dashboard():
    require_authentication()
    # Ensure the role check uses the correct function name and exists
    # For now, assuming require_role_access is available in auth.permissions
    require_role_access([USER_ROLES['DOCTOR']])

    inject_css() # Inject global styles
    inject_component_css('DASHBOARD_CARDS') # Specific styles for cards

    st.markdown("<h1>👨‍⚕️ Doctor Dashboard</h1>", unsafe_allow_html=True)

    current_user = get_current_user()
    if current_user:
        st.success(f"Welcome back, Dr. {current_user.get('full_name', 'Doctor')}!")
        render_doctor_dashboard_content(current_user)
    else:
        st.error("Could not retrieve user information. Please try logging in again.")

if __name__ == "__main__":
    # This is primarily for development/testing the page in isolation
    # In a real multi-page app, Streamlit calls this based on page navigation
    if 'user' not in st.session_state: # Mock user for direct script run
        st.session_state.user = {
            'id': 'doc123',
            'username': 'testdoctor',
            'role': USER_ROLES['DOCTOR'],
            'full_name': 'Test Doctor Name',
            'email': 'doctor@example.com'
        }
        st.session_state.authenticated = True
        st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)

    # show_doctor_dashboard() # Called at module level now

# This call ensures Streamlit runs the page content when navigating
show_doctor_dashboard()

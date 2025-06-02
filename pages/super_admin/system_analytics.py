import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

# Config and Auth
from config.settings import USER_ROLES
from config.styles import inject_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access

# Mock Services, Queries, and Components if not available
try:
    from services.analytics_service import AnalyticsService
except ImportError:
    class AnalyticsService: # Mock service
        def get_system_performance_metrics(self, days_back=7):
            # st.warning("AnalyticsService (get_system_performance_metrics) not found. Using mock data.", icon="⚠️") # Less verbose
            error_rate_data = pd.DataFrame({
                'date': pd.date_range(end=datetime.now(), periods=days_back, freq='D'),
                'error_rate_percent': [random.uniform(0.1, 2.5) for _ in range(days_back)]
            })
            return {
                'error_rate_last_24h': random.uniform(0.1, 1.5),
                'active_users_last_24h': random.randint(5, 50),
                'avg_response_time_ms': random.randint(150, 600),
                'error_rate_timeline': error_rate_data,
                'db_size_mb': random.uniform(100, 1000),
                'db_table_count': random.randint(10,30),
                'db_total_records': random.randint(10000, 1000000)
            }
        # Add other necessary methods if AnalyticsService is supposed to provide more direct data
        # For example, get_user_registration_summary, get_prescription_creation_summary etc.

try:
    from database.queries import AnalyticsQueries, DashboardQueries, UserQueries
    if not hasattr(UserQueries, 'get_all_users'):
        class MockUserQueriesForSA:
            @staticmethod
            def get_all_users():
                return [
                    {'id': 'user001', 'username': 'doc_john', 'full_name': 'Dr. John Doe', 'role': USER_ROLES['DOCTOR']},
                    {'id': 'user002', 'username': 'asst_jane', 'full_name': 'Jane Assist', 'role': USER_ROLES['ASSISTANT']},
                    {'id': 'user003', 'username': 'sa_prime', 'full_name': 'Super Admin Prime', 'role': USER_ROLES['SUPER_ADMIN']},
                ]
        UserQueries.get_all_users = MockUserQueriesForSA.get_all_users # Patch it if missing
except ImportError:
    class UserQueries:
            @staticmethod
            def get_all_users():
                return [
                    {'id': 'user001', 'username': 'doc_john', 'full_name': 'Dr. John Doe', 'role': USER_ROLES['DOCTOR']},
                    {'id': 'user002', 'username': 'asst_jane', 'full_name': 'Jane Assist', 'role': USER_ROLES['ASSISTANT']},
                    {'id': 'user003', 'username': 'sa_prime', 'full_name': 'Super Admin Prime', 'role': USER_ROLES['SUPER_ADMIN']},
                ]

    class AnalyticsQueries:
        @staticmethod
        def get_entity_counts():
            # st.warning("AnalyticsQueries (get_entity_counts) not found. Using mock counts.", icon="⚠️")
            return {
                'total_users': random.randint(50, 200), 'total_patients': random.randint(1000, 5000),
                'total_prescriptions': random.randint(2000, 10000), 'total_medications': random.randint(100, 500),
                'total_lab_tests': random.randint(50, 300),  'total_visits': random.randint(5000, 20000)
            }
        @staticmethod
        def get_user_registration_timeline(days_back=30):
            dates = pd.date_range(end=datetime.now(), periods=days_back, freq='D')
            return pd.DataFrame({'date': dates, 'count': [random.randint(0,5) for _ in range(days_back)]})
        @staticmethod
        def get_prescription_creation_timeline(days_back=30):
            dates = pd.date_range(end=datetime.now(), periods=days_back, freq='D')
            return pd.DataFrame({'date': dates, 'count': [random.randint(5,25) for _ in range(days_back)]})
        @staticmethod
        def get_user_activity(days_back=7, user_id=None, action_type=None, limit=50):
            base_time = datetime.now(); activities = []
            users = UserQueries.get_all_users() # Use the (potentially patched) UserQueries
            actions = ['login', 'create_patient', 'update_patient', 'create_prescription', 'view_analytics', 'error_occurred']
            entities = ['patient_XYZ', 'prescription_ABC', 'analytics_dash', 'system_log', None]
            for _ in range(limit * 2):
                user = random.choice(users)
                act = random.choice(actions)
                activities.append({'timestamp': base_time - timedelta(minutes=random.randint(0, days_back * 1440)),
                                   'user_id': user['id'], 'username': user['username'], 'user_role': user['role'],
                                   'action_type': act, 'entity_affected': random.choice(entities),
                                   'success': random.choice([True,True,False]) if act != 'error_occurred' else False,
                                   'details': 'Mock action details.' if act != 'error_occurred' else 'Simulated error.'})
            if user_id and user_id != "All": activities = [a for a in activities if a['user_id'] == user_id]
            if action_type and action_type != "All": activities = [a for a in activities if a['action_type'] == action_type]
            activities.sort(key=lambda x: x['timestamp'], reverse=True)
            return pd.DataFrame(activities[:limit])
        @staticmethod
        def get_table_row_counts():
            return {'patients': 1234, 'visits': 6789, 'prescriptions': 3456, 'users': 167, 'medications': 289, 'lab_tests': 123}
    class DashboardQueries: pass

try:
    from components.charts import TimeSeriesChart, BarChart, PieChart
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    def create_mock_chart(name): # Simplified mock chart creator
        def MockChart(data, title="", x_axis=None, y_axis=None, x=None, y=None, use_container_width=True):
            st.caption(title or f"Mock {name}")
            if isinstance(data, pd.DataFrame) and not data.empty:
                x_col = x_axis or x or data.columns[0]
                y_col = y_axis or y or data.columns[1] if len(data.columns) > 1 else None
                if x_col in data.columns and (y_col is None or y_col in data.columns):
                    chart_data = data.set_index(x_col)
                    if y_col: chart_data = chart_data[y_col]
                    if name == "TimeSeriesChart": st.line_chart(chart_data, use_container_width=use_container_width)
                    elif name == "BarChart": st.bar_chart(chart_data, use_container_width=use_container_width)
                    elif name == "PieChart": st.bar_chart(chart_data, use_container_width=use_container_width) # No direct pie, use bar
                    else: st.dataframe(data.head(3), use_container_width=use_container_width)
                else: st.dataframe(data.head(3), use_container_width=use_container_width)
            else: st.info(f"No data for {name}.")
        return MockChart
    TimeSeriesChart = create_mock_chart("TimeSeriesChart"); BarChart = create_mock_chart("BarChart"); PieChart = create_mock_chart("PieChart")

try:
    from utils.formatters import format_date_display, get_time_ago
except ImportError:
    def format_date_display(dt_obj): return dt_obj.strftime('%Y-%m-%d %H:%M') if isinstance(dt_obj, datetime) else str(dt_obj)
    def get_time_ago(dt_obj):
        if not isinstance(dt_obj, datetime): return str(dt_obj)
        delta = datetime.now() - dt_obj
        if delta.days > 0: return f"{delta.days}d ago"
        if delta.seconds // 3600 > 0 : return f"{delta.seconds // 3600}h ago"
        return f"{delta.seconds // 60}m ago"


# --- Tab Rendering Functions ---
def render_overview_tab(days_filter):
    st.subheader("System Wide Counts")
    try:
        counts = AnalyticsQueries.get_entity_counts()
        cols = st.columns(4)
        cols[0].metric("Total Users", counts.get('total_users', 'N/A')); cols[1].metric("Total Patients", counts.get('total_patients', 'N/A'))
        cols[2].metric("Total Prescriptions", counts.get('total_prescriptions', 'N/A')); cols[3].metric("Total Visits", counts.get('total_visits', 'N/A'))
        cols2 = st.columns(2); cols2[0].metric("Medications in DB", counts.get('total_medications', 'N/A')); cols2[1].metric("Lab Tests in DB", counts.get('total_lab_tests', 'N/A'))
    except Exception as e: show_error_message(f"Error fetching counts: {e}")

    st.markdown("---"); st.subheader(f"Activity Trends (Last {days_filter} Days)")
    try:
        user_reg = AnalyticsQueries.get_user_registration_timeline(days_back=days_filter)
        TimeSeriesChart(user_reg, title="New User Registrations", x='date', y='count')
    except Exception as e: show_error_message(f"Error user reg data: {e}")
    try:
        rx_create = AnalyticsQueries.get_prescription_creation_timeline(days_back=days_filter)
        TimeSeriesChart(rx_create, title="Prescriptions Created", x='date', y='count')
    except Exception as e: show_error_message(f"Error prescription data: {e}")

def render_user_activity_tab(days_filter):
    st.subheader("Recent User Actions")
    users = [{'id': 'All', 'username': 'All', 'full_name': 'All Users'}] + UserQueries.get_all_users()
    user_map = {u['id']: f"{u['full_name']} ({u['username']})" for u in users}
    actions = ["All", "login", "create_patient", "update_patient", "create_prescription", "view_analytics", "error_occurred"]

    f_cols = st.columns(2)
    sel_user = f_cols[0].selectbox("Filter by User:", options=list(user_map.keys()), format_func=lambda x: user_map[x], key="sa_activity_user_filter_v2")
    sel_action = f_cols[1].selectbox("Filter by Action Type:", options=actions, key="sa_activity_action_filter_v2")

    try:
        activity = AnalyticsQueries.get_user_activity(days_back=days_filter, user_id=sel_user if sel_user != "All" else None, action_type=sel_action if sel_action != "All" else None, limit=100)
        if not activity.empty:
            activity_disp = activity.copy(); activity_disp['timestamp'] = activity_disp['timestamp'].apply(lambda x: f"{format_date_display(x)} ({get_time_ago(x)})")
            st.dataframe(activity_disp[['timestamp', 'username', 'user_role', 'action_type', 'success', 'entity_affected', 'details']].head(50), height=300, use_container_width=True) # Show top 50 of filtered
        else: st.info("No user activity for selected filters.")
    except Exception as e: show_error_message(f"Error fetching activity: {e}")

    st.markdown("---"); st.subheader("Activity Aggregates")
    if 'activity' in locals() and not activity.empty:
        try:
            role_act = activity.groupby('user_role')['action_type'].count().reset_index(name='count')
            PieChart(role_act, title="Activity by Role", x_axis='user_role', y_axis='count')
            active_usr = activity.groupby('username')['action_type'].count().nlargest(10).reset_index(name='action_count')
            BarChart(active_usr, title="Most Active Users (Top 10)", x_axis='username', y_axis='action_count')
        except Exception as e: show_error_message(f"Error generating aggregates: {e}")
    else: st.info("Not enough data for aggregates.")

def render_system_health_tab(days_filter):
    st.subheader("System Performance & Error Monitoring")
    try:
        health = AnalyticsService().get_system_performance_metrics(days_back=days_filter)
        h_cols = st.columns(3)
        h_cols[0].metric("Error Rate (24h)", f"{health.get('error_rate_last_24h', 0):.2f}%")
        h_cols[1].metric("Active Users (24h)", health.get('active_users_last_24h', 'N/A'))
        h_cols[2].metric("Avg. Response (ms)", f"{health.get('avg_response_time_ms', 0)}")

        err_timeline = health.get('error_rate_timeline')
        if isinstance(err_timeline, pd.DataFrame) and not err_timeline.empty: TimeSeriesChart(err_timeline, title=f"Error Rate Over Last {days_filter} Days", x='date', y='error_rate_percent')

        st.markdown("##### Recent Error Logs (Simulated)"); errors = AnalyticsQueries.get_user_activity(days_back=days_filter, action_type='error_occurred', limit=10)
        if not errors.empty:
            errors_disp = errors.copy(); errors_disp['timestamp'] = errors_disp['timestamp'].apply(lambda x: f"{format_date_display(x)} ({get_time_ago(x)})")
            st.dataframe(errors_disp[['timestamp', 'username', 'details']], height=200, use_container_width=True)
        else: st.info("No critical error logs recently.")
    except Exception as e: show_error_message(f"Error fetching health metrics: {e}")

def render_database_stats_tab():
    st.subheader("Database Information")
    try:
        db_m = AnalyticsService().get_system_performance_metrics() # Mock includes DB stats
        db_cols = st.columns(3)
        db_cols[0].metric("DB Size", f"{db_m.get('db_size_mb', 0):.2f} MB"); db_cols[1].metric("Total Tables", db_m.get('db_table_count', 'N/A')); db_cols[2].metric("Total Records (Est.)", f"{db_m.get('db_total_records', 0):,}")

        st.markdown("##### Table Row Counts (Simulated)"); tbl_counts = AnalyticsQueries.get_table_row_counts()
        if tbl_counts: df_tbls = pd.DataFrame(list(tbl_counts.items()), columns=['Table', 'Rows']); BarChart(df_tbls, title="Rows per Table", x_axis='Table', y_axis='Rows')
        else: st.info("Could not get table counts.")
    except Exception as e: show_error_message(f"Error fetching DB stats: {e}")

def show_system_analytics_page():
    require_authentication(); require_role_access([USER_ROLES['SUPER_ADMIN']]); inject_css()
    st.markdown("<h1>⚙️ System Analytics & Monitoring</h1>", unsafe_allow_html=True)
    if not get_current_user(): show_error_message("Admin data not found."); return

    top_cols = st.columns([3,1])
    days_filter = top_cols[0].selectbox("Global Time Period:", options=[7,15,30,60,90], format_func=lambda x:f"Last {x}d", index=1, key="sa_analytics_global_days_v2")
    top_cols[1].markdown("<div>&nbsp;</div>", unsafe_allow_html=True);
    if top_cols[1].button("🔄 Refresh", key="sa_refresh_all_v2", use_container_width=True): st.rerun()
    st.markdown("---")

    tabs = ["📊 Overview", "👥 User Activity", "❤️ System Health", "🗄️ Database Stats"]
    tab_overview, tab_user_act, tab_sys_health, tab_db = st.tabs(tabs)
    with tab_overview: render_overview_tab(days_filter)
    with tab_user_act: render_user_activity_tab(days_filter)
    with tab_sys_health: render_system_health_tab(days_filter)
    with tab_db: render_database_stats_tab()

if __name__ == "__main__":
    if 'user' not in st.session_state:
        st.session_state.user = {'id': 'superadmin008', 'username': 'sa_sysview_v2', 'role': USER_ROLES['SUPER_ADMIN'], 'full_name': 'Sys Admin Viewer V2'}
        st.session_state.authenticated = True; st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)
    if not CHARTS_AVAILABLE: st.sidebar.warning("Using MOCK Chart components for SA System Analytics.")
    # Mock queries show own warnings if AnalyticsQueries/DashboardQueries are not found.
    if 'UserQueries' not in globals() or not hasattr(UserQueries, 'get_all_users'):
        class UserQueries: @staticmethod
        def get_all_users(): return [{'id': 'u1', 'username': 'mock_u', 'full_name': 'Mock User', 'role': 'mock_role'}]
    show_system_analytics_page()

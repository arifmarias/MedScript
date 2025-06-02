"""
MedScript Pro - Super Admin Dashboard
This page displays the main dashboard for super administrators with system-wide metrics and analytics.
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Any
import streamlit as st
import pandas as pd
from config.settings import USER_ROLES
from config.styles import inject_css, inject_component_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access
from services.analytics_service import AnalyticsService, get_user_dashboard_metrics
from components.cards import MetricCard, AnalyticsCard, ActivityCard, render_card_grid
from components.charts import (
    TimeSeriesChart, PieChart, BarChart, AnalyticsDashboard,
    create_medical_kpi_dashboard
)
from database.queries import (
    DashboardQueries, get_entity_counts, AnalyticsQueries,
    UserQueries, PatientQueries, PrescriptionQueries
)
from utils.formatters import format_date_display, format_percentage, format_currency

def show_super_admin_dashboard():
    """Display the super admin dashboard"""
    # Authentication and permission checks
    require_authentication()
    require_role_access([USER_ROLES['SUPER_ADMIN']])
    
    # Inject CSS
    inject_css()
    inject_component_css('DASHBOARD_CARDS')
    
    # Page header
    st.markdown("""
        <div class="main-header">
            <h1>🏥 Super Admin Dashboard</h1>
            <p>System Overview and Analytics</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Get current user
    current_user = get_current_user()
    
    # Welcome message
    st.markdown(f"""
        <div class="welcome-message">
            Welcome back, <strong>{current_user['full_name']}</strong>! 
            Here's your system overview for {format_date_display(date.today())}.
        </div>
    """, unsafe_allow_html=True)
    
    # Main dashboard content
    render_dashboard_content()

def render_dashboard_content():
    """Render the main dashboard content"""
    try:
        # Create tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", "👥 Users", "🏥 Patients", "📝 Prescriptions", "⚙️ System"
        ])
        
        with tab1:
            render_overview_tab()
        
        with tab2:
            render_users_tab()
        
        with tab3:
            render_patients_tab()
        
        with tab4:
            render_prescriptions_tab()
        
        with tab5:
            render_system_tab()
    
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
        st.info("Please refresh the page or contact support if the problem persists.")

def render_overview_tab():
    """Render the overview tab with key metrics"""
    st.subheader("📊 System Overview")
    
    # Time range selector
    col_filter, col_refresh = st.columns([3, 1])
    
    with col_filter:
        time_range = st.selectbox(
            "Time Range",
            options=[7, 14, 30, 60, 90],
            index=2,  # Default to 30 days
            format_func=lambda x: f"Last {x} days"
        )
    
    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Get dashboard metrics
    analytics_service = AnalyticsService()
    metrics = analytics_service.get_dashboard_metrics(
        USER_ROLES['SUPER_ADMIN'], 
        days_back=time_range
    )
    
    if not metrics:
        st.warning("Unable to load dashboard metrics")
        return
    
    # Key Metrics Cards
    st.markdown("### 📈 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = metrics.get('total_users', 0)
        st.metric(
            label="👥 Total Users",
            value=total_users,
            help="Active users in the system"
        )
    
    with col2:
        total_patients = metrics.get('total_patients', 0)
        st.metric(
            label="🏥 Total Patients",
            value=total_patients,
            help="Registered patients in the system"
        )
    
    with col3:
        total_prescriptions = metrics.get('total_prescriptions', 0)
        recent_prescriptions = metrics.get('recent_prescriptions', 0)
        delta = f"+{recent_prescriptions}" if recent_prescriptions > 0 else None
        st.metric(
            label="📝 Total Prescriptions",
            value=total_prescriptions,
            delta=delta,
            help=f"Total prescriptions ({recent_prescriptions} in last {time_range} days)"
        )
    
    with col4:
        total_medications = metrics.get('total_medications', 0)
        st.metric(
            label="💊 Medications",
            value=total_medications,
            help="Active medications in database"
        )
    
    # Recent Activity Metrics
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        recent_patients = metrics.get('recent_patients', 0)
        st.metric(
            label="🆕 New Patients",
            value=recent_patients,
            help=f"New patients in last {time_range} days"
        )
    
    with col6:
        # Calculate active users percentage
        user_activity = metrics.get('user_activity', [])
        total_activity = sum(item.get('count', 0) for item in user_activity)
        st.metric(
            label="📊 User Activity",
            value=total_activity,
            help=f"Total user actions in last {time_range} days"
        )
    
    with col7:
        # Today's summary
        today_summary = DashboardQueries.get_today_summary()
        todays_visits = today_summary.get('todays_visits', 0)
        st.metric(
            label="📅 Today's Visits",
            value=todays_visits,
            help="Patient visits scheduled for today"
        )
    
    with col8:
        todays_prescriptions = today_summary.get('todays_prescriptions', 0)
        st.metric(
            label="📋 Today's Prescriptions",
            value=todays_prescriptions,
            help="Prescriptions created today"
        )
    
    # Charts Section
    st.markdown("### 📊 Analytics Charts")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # User Activity by Role
        user_activity_data = metrics.get('user_activity', [])
        if user_activity_data:
            chart = PieChart(
                data=user_activity_data,
                labels_field='user_type',
                values_field='count',
                title="User Activity by Role",
                height=300
            )
            chart.render()
        else:
            st.info("No user activity data available")
    
    with col_chart2:
        # Top Doctors by Prescriptions
        top_doctors = metrics.get('top_doctors', [])
        if top_doctors:
            chart = BarChart(
                data=top_doctors,
                x_field='full_name',
                y_field='prescription_count',
                title="Top Doctors by Prescriptions",
                height=300
            )
            chart.render()
        else:
            st.info("No prescription data available")
    
    # Recent Activity
    st.markdown("### 🕐 Recent System Activity")
    
    recent_activity = DashboardQueries.get_recent_activity(limit=10)
    if recent_activity:
        activity_card = ActivityCard(recent_activity, max_items=8)
        activity_card.render()
    else:
        st.info("No recent activity found")

def render_users_tab():
    """Render the users management tab"""
    st.subheader("👥 User Management Overview")
    
    # User statistics
    all_users = UserQueries.get_all_users()
    
    if not all_users:
        st.warning("No users found in the system")
        return
    
    # User metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        active_users = len([u for u in all_users if u.get('is_active', True)])
        st.metric("Active Users", active_users)
    
    with col2:
        doctors = len([u for u in all_users if u.get('user_type') == 'doctor'])
        st.metric("Doctors", doctors)
    
    with col3:
        assistants = len([u for u in all_users if u.get('user_type') == 'assistant'])
        st.metric("Assistants", assistants)
    
    # User distribution chart
    user_types = {}
    for user in all_users:
        user_type = user.get('user_type', 'unknown').replace('_', ' ').title()
        user_types[user_type] = user_types.get(user_type, 0) + 1
    
    if user_types:
        chart_data = [{'user_type': k, 'count': v} for k, v in user_types.items()]
        chart = PieChart(
            data=chart_data,
            labels_field='user_type',
            values_field='count',
            title="User Distribution by Role"
        )
        chart.render()
    
    # Recent user registrations
    st.markdown("### 🆕 Recently Registered Users")
    
    # Sort users by creation date
    sorted_users = sorted(all_users, key=lambda x: x.get('created_at', ''), reverse=True)
    recent_users = sorted_users[:5]
    
    if recent_users:
        for user in recent_users:
            col_name, col_type, col_date = st.columns([2, 1, 1])
            
            with col_name:
                st.write(f"**{user.get('full_name', 'Unknown')}**")
                st.caption(f"@{user.get('username', 'unknown')}")
            
            with col_type:
                user_type = user.get('user_type', '').replace('_', ' ').title()
                st.write(user_type)
            
            with col_date:
                created_date = user.get('created_at', '')
                if created_date:
                    try:
                        date_obj = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                        st.write(format_date_display(date_obj.date()))
                    except:
                        st.write(created_date[:10])
    else:
        st.info("No recent user registrations")

def render_patients_tab():
    """Render the patients overview tab"""
    st.subheader("🏥 Patient Management Overview")
    
    # Get patient statistics
    all_patients = PatientQueries.search_patients(limit=1000)  # Get more for stats
    
    if not all_patients:
        st.warning("No patients found in the system")
        return
    
    # Patient metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_patients = len(all_patients)
        st.metric("Total Patients", total_patients)
    
    with col2:
        male_patients = len([p for p in all_patients if p.get('gender') == 'Male'])
        st.metric("Male Patients", male_patients)
    
    with col3:
        female_patients = len([p for p in all_patients if p.get('gender') == 'Female'])
        st.metric("Female Patients", female_patients)
    
    with col4:
        # Calculate average age
        ages = []
        for patient in all_patients:
            dob = patient.get('date_of_birth')
            if dob:
                try:
                    if isinstance(dob, str):
                        birth_date = datetime.strptime(dob, '%Y-%m-%d').date()
                    else:
                        birth_date = dob
                    
                    age = (date.today() - birth_date).days // 365
                    ages.append(age)
                except:
                    continue
        
        avg_age = sum(ages) // len(ages) if ages else 0
        st.metric("Average Age", f"{avg_age} years")
    
    # Patient charts
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Gender distribution
        gender_counts = {}
        for patient in all_patients:
            gender = patient.get('gender', 'Unknown')
            gender_counts[gender] = gender_counts.get(gender, 0) + 1
        
        if gender_counts:
            chart_data = [{'gender': k, 'count': v} for k, v in gender_counts.items()]
            chart = PieChart(
                data=chart_data,
                labels_field='gender',
                values_field='count',
                title="Patient Gender Distribution"
            )
            chart.render()
    
    with col_chart2:
        # Age distribution
        age_groups = {'0-18': 0, '19-35': 0, '36-50': 0, '51-65': 0, '65+': 0}
        
        for age in ages:
            if age <= 18:
                age_groups['0-18'] += 1
            elif age <= 35:
                age_groups['19-35'] += 1
            elif age <= 50:
                age_groups['36-50'] += 1
            elif age <= 65:
                age_groups['51-65'] += 1
            else:
                age_groups['65+'] += 1
        
        if any(age_groups.values()):
            chart_data = [{'age_group': k, 'count': v} for k, v in age_groups.items()]
            chart = BarChart(
                data=chart_data,
                x_field='age_group',
                y_field='count',
                title="Patient Age Distribution"
            )
            chart.render()
    
    # Recent patient registrations
    st.markdown("### 🆕 Recently Registered Patients")
    
    # Get recent patients (last 10)
    sorted_patients = sorted(all_patients, key=lambda x: x.get('created_at', ''), reverse=True)
    recent_patients = sorted_patients[:8]
    
    if recent_patients:
        for patient in recent_patients:
            col_name, col_age, col_contact, col_date = st.columns([2, 1, 1, 1])
            
            with col_name:
                name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
                st.write(f"**{name}**")
                st.caption(f"ID: {patient.get('patient_id', 'Unknown')}")
            
            with col_age:
                dob = patient.get('date_of_birth')
                if dob:
                    try:
                        if isinstance(dob, str):
                            birth_date = datetime.strptime(dob, '%Y-%m-%d').date()
                        else:
                            birth_date = dob
                        age = (date.today() - birth_date).days // 365
                        st.write(f"{age} years")
                    except:
                        st.write("Unknown")
                else:
                    st.write("Unknown")
            
            with col_contact:
                phone = patient.get('phone', 'N/A')
                st.write(phone[:12] + "..." if len(phone) > 12 else phone)
            
            with col_date:
                created_date = patient.get('created_at', '')
                if created_date:
                    try:
                        date_obj = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                        st.write(format_date_display(date_obj.date()))
                    except:
                        st.write(created_date[:10])

def render_prescriptions_tab():
    """Render the prescriptions overview tab"""
    st.subheader("📝 Prescription Management Overview")
    
    # Get prescription analytics
    analytics_service = AnalyticsService()
    prescription_analytics = analytics_service.get_prescription_analytics(
        USER_ROLES['SUPER_ADMIN'],
        days_back=30
    )
    
    if not prescription_analytics:
        st.warning("No prescription data available")
        return
    
    # Create analytics dashboard
    dashboard = AnalyticsDashboard(prescription_analytics)
    dashboard.render_prescription_analytics()
    
    # Additional prescription insights
    st.markdown("### 💡 Prescription Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top diagnoses
        top_diagnoses = prescription_analytics.get('top_diagnoses', [])
        if top_diagnoses:
            st.markdown("**Most Common Diagnoses:**")
            for i, diagnosis in enumerate(top_diagnoses[:5], 1):
                st.write(f"{i}. {diagnosis.get('diagnosis', 'Unknown')} ({diagnosis.get('count', 0)} cases)")
        else:
            st.info("No diagnosis data available")
    
    with col2:
        # Top lab tests
        top_lab_tests = prescription_analytics.get('top_lab_tests', [])
        if top_lab_tests:
            st.markdown("**Most Ordered Lab Tests:**")
            for i, test in enumerate(top_lab_tests[:5], 1):
                st.write(f"{i}. {test.get('test_name', 'Unknown')} ({test.get('count', 0)} orders)")
        else:
            st.info("No lab test data available")

def render_system_tab():
    """Render the system monitoring tab"""
    st.subheader("⚙️ System Monitoring")
    
    # Get system health metrics
    analytics_service = AnalyticsService()
    system_metrics = analytics_service.get_system_performance_metrics()
    
    if not system_metrics:
        st.warning("Unable to load system metrics")
        return
    
    # System health overview
    st.markdown("### 🏥 System Health")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        db_size = system_metrics.get('database', {}).get('file_size_mb', 0)
        st.metric(
            label="Database Size",
            value=f"{db_size:.1f} MB",
            help="Current database file size"
        )
    
    with col2:
        error_rate = system_metrics.get('error_rate', {}).get('error_rate', 0)
        st.metric(
            label="Error Rate",
            value=f"{error_rate:.1f}%",
            delta_color="inverse",
            help="Error rate in last 24 hours"
        )
    
    with col3:
        active_users_24h = system_metrics.get('active_users_24h', 0)
        st.metric(
            label="Active Users (24h)",
            value=active_users_24h,
            help="Unique users active in last 24 hours"
        )
    
    with col4:
        total_records = system_metrics.get('database', {}).get('total_records', 0)
        st.metric(
            label="Total Records",
            value=total_records,
            help="Total records in database"
        )
    
    # Database statistics
    st.markdown("### 💾 Database Statistics")
    
    db_stats = system_metrics.get('database', {})
    if db_stats:
        col_db1, col_db2 = st.columns(2)
        
        with col_db1:
            st.markdown("**Database Information:**")
            st.write(f"• File Size: {db_stats.get('file_size_mb', 0):.2f} MB")
            st.write(f"• Table Count: {db_stats.get('table_count', 0)}")
            st.write(f"• Page Count: {db_stats.get('page_count', 0):,}")
            st.write(f"• Page Size: {db_stats.get('page_size', 0):,} bytes")
        
        with col_db2:
            # Entity counts
            entity_counts = get_entity_counts()
            st.markdown("**Record Counts:**")
            for entity, count in entity_counts.items():
                entity_name = entity.replace('_', ' ').title()
                st.write(f"• {entity_name}: {count:,}")
    
    # System activity
    st.markdown("### 📊 System Activity")
    
    # Hourly usage
    hourly_usage = system_metrics.get('hourly_usage', [])
    if hourly_usage:
        # Convert to chart format
        chart_data = []
        for item in hourly_usage:
            hour = int(item.get('hour', 0))
            hour_str = f"{hour:02d}:00"
            chart_data.append({
                'hour': hour_str,
                'activity_count': item.get('activity_count', 0)
            })
        
        chart = BarChart(
            data=chart_data,
            x_field='hour',
            y_field='activity_count',
            title="System Activity by Hour (Last 7 Days)"
        )
        chart.render()
    
    # Recent errors (if any)
    error_stats = system_metrics.get('error_rate', {})
    if error_stats.get('errors', 0) > 0:
        st.markdown("### ⚠️ Error Summary")
        
        col_err1, col_err2 = st.columns(2)
        
        with col_err1:
            st.metric(
                label="Total Errors (24h)",
                value=error_stats.get('errors', 0),
                delta_color="inverse"
            )
        
        with col_err2:
            st.metric(
                label="Total Requests (24h)",
                value=error_stats.get('total', 0)
            )
        
        if error_stats.get('errors', 0) > 10:
            st.warning("⚠️ Higher than normal error rate detected. Please review system logs.")
    
    # System recommendations
    st.markdown("### 💡 System Recommendations")
    
    recommendations = []
    
    # Database size check
    if db_stats.get('file_size_mb', 0) > 100:
        recommendations.append("🗄️ Consider database maintenance - size exceeds 100MB")
    
    # Error rate check
    if error_rate > 5:
        recommendations.append("⚠️ Error rate is elevated - review system logs")
    
    # Activity check
    if active_users_24h < 1:
        recommendations.append("📊 Low user activity detected in last 24 hours")
    
    if recommendations:
        for rec in recommendations:
            st.info(rec)
    else:
        st.success("✅ System is running optimally")

# This call ensures Streamlit runs the page content when navigating
show_super_admin_dashboard()

if __name__ == "__main__":
    # Mock setup or specific direct run logic can go here
    # For example, ensuring a mock user is set if not already by main app flow
    if 'user' not in st.session_state:
        st.session_state.user = {
            'id': 'sa_dashboard_direct',
            'username': 'sa_dash_direct',
            'role': USER_ROLES['SUPER_ADMIN'],
            'full_name': 'SA Dashboard Direct Runner'
        }
        st.session_state.authenticated = True
        st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)
    # show_super_admin_dashboard() # Already called at module level
    pass
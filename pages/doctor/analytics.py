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
        def get_prescription_analytics(self, role, user_id, days_back):
            st.warning("AnalyticsService not found. Using mock prescription analytics.")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            date_range = pd.date_range(start_date, end_date, freq='D')
            count_data = [max(0, int(5 + 3 * (i % 7) - (i % 3)**2 + i//5)) for i in range(len(date_range))] # More varied data
            return {
                'prescriptions_timeline': pd.DataFrame({
                    'date': date_range,
                    'count': count_data
                }),
                'total_prescriptions': sum(count_data),
                'average_meds_per_prescription': 2.5 if sum(count_data) > 0 else 0
            }
        def get_patient_analytics(self, role, user_id, days_back): # For patients this doctor interacted with
            st.warning("AnalyticsService not found. Using mock patient analytics.")
            return {
                'patient_demographics': pd.DataFrame({
                    'age_group': ['0-18', '19-35', '36-50', '51-65', '65+'],
                    'count': [max(0, int(days_back/10 + i*2 - (i%2)*5)) for i in range(5)] # Data varies with days_back
                }),
                'gender_distribution': pd.DataFrame({
                    'gender': ['Male', 'Female', 'Other', 'Prefer not to say'],
                    'count': [max(0,int(days_back/5 + i*3)) for i in range(4)]
                }),
                'new_vs_returning_patients': {'new': max(0,int(days_back/3)), 'returning': max(0,int(days_back*2/3))}
            }
        def get_medication_analytics(self, role, user_id, days_back):
            st.warning("AnalyticsService not found. Using mock medication analytics.")
            med_names = ['Amoxicillin', 'Lisinopril', 'Metformin', 'Paracetamol', 'Salbutamol', 'Aspirin', 'Omeprazole']
            return {
                'most_prescribed_medications': pd.DataFrame({
                    'medication_name': med_names[:5],
                    'prescription_count': [max(0,int(days_back/6 + i*2)) for i in range(5)]
                }),
                'prescription_by_drug_class': pd.DataFrame({
                    'drug_class': ['Antibiotics', 'ACE Inhibitors', 'Biguanides', 'Analgesics', 'Bronchodilators'],
                    'count': [max(0,int(days_back/5 + i)) for i in range(5)]
                })
            }

try:
    from components.charts import (
        PrescriptionTrendChart,
        PatientDemographicsChart,
        MedicationUsageChart,
        AnalyticsDashboard
    )
    # If AnalyticsDashboard exists, we might prefer it.
    # For this example, we'll assume individual charts are primary.
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    def create_mock_chart_component(name):
        def MockChartComponent(data, title=None):
            if title: st.caption(title)
            if isinstance(data, pd.DataFrame) and not data.empty:
                try:
                    st.bar_chart(data.set_index(data.columns[0]))
                except Exception as e:
                    st.error(f"Failed to render mock chart for {name} with given data: {e}")
                    st.dataframe(data)
            elif isinstance(data, dict) and data:
                 st.json(data) # Simple display for dict data
            else:
                st.info(f"No data or unsupported data format for mock chart: {name}.")
        return MockChartComponent

    PrescriptionTrendChart = create_mock_chart_component("Prescription Trend Chart")
    PatientDemographicsChart = create_mock_chart_component("Patient Demographics Chart")
    MedicationUsageChart = create_mock_chart_component("Medication Usage Chart")

    class AnalyticsDashboard:
        def __init__(self, data=None, title=None):
            self.data = data
            self.title = title
            st.warning("AnalyticsDashboard component not found. Using mock rendering.")
        # Add mock render methods if you intend to test the dashboard flow
        def render(self): # Generic render
            st.subheader(self.title or "Mock Dashboard Section")
            if self.data: st.json(self.data)
            else: st.info("No data for this dashboard section.")


# Utils
from utils.helpers import show_error_message, show_success_message, show_warning_message


# --- Main Rendering Function ---
def render_analytics_content(doctor: dict):
    st.markdown("### Analytics Overview")

    col1, col2 = st.columns([1,3])
    with col1:
        selected_period_days = st.selectbox(
            "Select Period:",
            options=[7, 30, 60, 90, 180, 365],
            format_func=lambda x: f"Last {x} days" if x != 365 else "Last Year",
            index=1 # Default to 30 days
        )
    with col2:
        st.markdown("<div>&nbsp;</div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh Data", key="refresh_analytics_main", use_container_width=True):
            st.rerun()

    st.markdown("---")

    try:
        analytics_service = AnalyticsService()
        prescription_analytics = analytics_service.get_prescription_analytics(USER_ROLES['DOCTOR'], doctor['id'], days_back=selected_period_days)
        patient_analytics = analytics_service.get_patient_analytics(USER_ROLES['DOCTOR'], doctor['id'], days_back=selected_period_days)
        medication_analytics = analytics_service.get_medication_analytics(USER_ROLES['DOCTOR'], doctor['id'], days_back=selected_period_days)
    except Exception as e:
        show_error_message(f"Error fetching analytics data: {e}")
        prescription_analytics, patient_analytics, medication_analytics = {}, {}, {}

    # --- Display Charts ---
    # Using individual charts for now.

    st.header("Prescription Analytics")
    if prescription_analytics:
        total_rx = prescription_analytics.get('total_prescriptions', 0)
        avg_meds = prescription_analytics.get('average_meds_per_prescription', 0.0)

        kpi_cols_rx = st.columns(2)
        kpi_cols_rx[0].metric(label="Total Prescriptions Issued", value=total_rx if total_rx is not None else "N/A")
        kpi_cols_rx[1].metric(label="Avg. Meds per Prescription", value=f"{avg_meds:.1f}" if isinstance(avg_meds, (int,float)) else "N/A")

        timeline_data = prescription_analytics.get('prescriptions_timeline')
        if timeline_data is not None and not timeline_data.empty:
            PrescriptionTrendChart(timeline_data, title=f"Prescription Volume (Last {selected_period_days} Days)")
        else:
            st.info("No prescription timeline data available.")
    else:
        st.info("No prescription analytics data available for the selected period.")

    st.markdown("---")
    st.header("Medication Analytics")
    if medication_analytics:
        med_usage_data = medication_analytics.get('most_prescribed_medications')
        if med_usage_data is not None and not med_usage_data.empty:
            MedicationUsageChart(med_usage_data, title=f"Most Prescribed Medications (Last {selected_period_days} Days)")
        else:
            st.info("No data on most prescribed medications.")

        drug_class_data = medication_analytics.get('prescription_by_drug_class')
        if drug_class_data is not None and not drug_class_data.empty:
            # Assuming MedicationUsageChart can also display this or a similar component exists
            MedicationUsageChart(drug_class_data, title=f"Prescriptions by Drug Class (Last {selected_period_days} Days)")
        else:
            st.info("No data on prescriptions by drug class.")
    else:
        st.info("No medication analytics data available.")

    st.markdown("---")
    st.header("Patient Analytics")
    if patient_analytics:
        new_patients = patient_analytics.get('new_vs_returning_patients', {}).get('new', 0)
        returning_patients = patient_analytics.get('new_vs_returning_patients', {}).get('returning', 0)

        kpi_cols_pt = st.columns(2)
        kpi_cols_pt[0].metric(label=f"New Patients (Last {selected_period_days} Days)", value=new_patients if new_patients is not None else "N/A")
        kpi_cols_pt[1].metric(label=f"Returning Patients (Last {selected_period_days} Days)", value=returning_patients if returning_patients is not None else "N/A")

        demographics_data = patient_analytics.get('patient_demographics')
        if demographics_data is not None and not demographics_data.empty:
            PatientDemographicsChart(demographics_data, title="Patient Age Groups")
        else:
            st.info("No patient age demographics data.")

        gender_data = patient_analytics.get('gender_distribution')
        if gender_data is not None and not gender_data.empty:
            # Using mock chart directly for this if PatientDemographicsChart is specific
            st.caption("Patient Gender Distribution")
            st.bar_chart(gender_data.set_index(gender_data.columns[0]))
        else:
            st.info("No patient gender distribution data.")
    else:
        st.info("No patient analytics data available for your activity in the selected period.")


# --- Main Page Function ---
def show_doctor_analytics_page():
    require_authentication()
    require_role_access([USER_ROLES['DOCTOR']])
    inject_css()

    st.markdown("<h1>📊 My Analytics Dashboard</h1>", unsafe_allow_html=True)

    current_user = get_current_user()
    if not current_user:
        show_error_message("Unable to retrieve user information. Please log in again.")
        return

    render_analytics_content(current_user)

if __name__ == "__main__":
    if 'user' not in st.session_state:
        st.session_state.user = {
            'id': 'docAnalyticsUser',
            'username': 'dr_stats',
            'role': USER_ROLES['DOCTOR'],
            'full_name': 'Dr. Stats',
            'email': 'dr.stats@example.com'
        }
        st.session_state.authenticated = True
        st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)

    show_doctor_analytics_page()

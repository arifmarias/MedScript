import streamlit as st
from datetime import datetime, time, timedelta

# Configuration and Authentication
from config.settings import USER_ROLES
from config.styles import inject_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access

# Components and Database
from components.cards import PatientCard # Assuming this component exists
from database.queries import VisitQueries # Assuming VisitQueries and get_doctor_today_visits exist
from utils.formatters import format_patient_name, format_time_display

# Mock data if queries or components are not ready
def get_mock_patient_visits(doctor_id: str):
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

def handle_patient_action(action_type: str, patient_visit_data: dict):
    """Placeholder function to handle actions from PatientCard."""
    patient_name = format_patient_name(patient_visit_data.get('patient_first_name','N/A'), patient_visit_data.get('patient_last_name',''))
    st.toast(f"{action_type} for {patient_name} (Visit ID: {patient_visit_data.get('visit_id', 'N/A')})")
    # In a real app, this would navigate, open a modal, or trigger a backend process.
    if action_type == "View Details":
        st.session_state.selected_patient_visit = patient_visit_data
        # Potentially navigate to a patient detail page or show a modal
        # st.switch_page("pages/doctor/patient_details.py") # Example if using st.switch_page
    elif action_type == "Start Consultation":
        # Navigate to consultation page or start process
        st.session_state.active_consultation = patient_visit_data
        # st.switch_page("pages/doctor/consultation.py") # Example

def render_todays_patients_list(doctor: dict):
    """Renders the list of today's patients for the given doctor."""
    st.markdown("---")
    if st.button("🔄 Refresh List"):
        st.rerun()

    try:
        # Attempt to fetch real data
        # This query needs to be implemented in database/queries/VisitQueries.py
        # It should return a list of dictionaries, each representing a visit with patient details.
        patient_visits = VisitQueries.get_doctor_today_visits(doctor['id'])
        if patient_visits is None: # Query might return None if no visits or error
            patient_visits = []
            # st.info("No patients scheduled for today or data is currently unavailable.") # Covered below
    except AttributeError: # If VisitQueries or the method doesn't exist
        st.warning("Patient data system is currently initializing. Using mock data for demonstration.")
        patient_visits = get_mock_patient_visits(doctor['id'])
    except Exception as e:
        st.error(f"An error occurred while fetching patient data: {e}")
        patient_visits = [] # Fallback to empty list on other errors

    if not patient_visits:
        st.info("No patients scheduled for today.")
        return

    # Display patients in sections: Upcoming, Completed
    upcoming_visits = [v for v in patient_visits if v.get('status', 'Scheduled').lower() == 'scheduled']
    completed_visits = [v for v in patient_visits if v.get('status', 'Scheduled').lower() == 'completed']
    other_visits = [v for v in patient_visits if v.get('status', 'Scheduled').lower() not in ['scheduled', 'completed']]


    if upcoming_visits:
        st.subheader("Upcoming Appointments")
        for visit_data in upcoming_visits:
            patient_name = format_patient_name(visit_data.get('patient_first_name'), visit_data.get('patient_last_name'))
            visit_time_formatted = format_time_display(visit_data.get('visit_time')) if visit_data.get('visit_time') else "N/A"
            
            # Prepare actions for the PatientCard
            actions = {
                "View Details": lambda v=visit_data: handle_patient_action("View Details", v),
                "Start Consultation": lambda v=visit_data: handle_patient_action("Start Consultation", v)
            }

            # Data to pass to PatientCard
            card_data = {
                'name': patient_name,
                'id': visit_data.get('patient_id'),
                'dob': visit_data.get('patient_dob'),
                'gender': visit_data.get('patient_gender'),
                'next_appointment_time': visit_time_formatted,
                'next_appointment_type': visit_data.get('visit_type'),
                'status': visit_data.get('status', 'Scheduled'),
                # Any other relevant details for the card
            }
            
            try:
                # Assuming PatientCard is a component that takes this data
                PatientCard(
                    patient_data=card_data, 
                    actions=actions,
                    key=f"patient_card_{visit_data.get('visit_id')}"
                )
            except TypeError as te: # Catch if PatientCard has unexpected arguments
                 st.error(f"Error rendering PatientCard for {patient_name}: {te}. Check PatientCard component definition.")
                 st.json(card_data) # Display raw data for debugging
            except Exception as e:
                st.error(f"Could not display patient card for {patient_name}: {e}")
                st.write(f"Raw data: {visit_data}")
        st.markdown("---")

    if completed_visits:
        st.subheader("Completed Consultations Today")
        for visit_data in completed_visits:
            patient_name = format_patient_name(visit_data.get('patient_first_name'), visit_data.get('patient_last_name'))
            visit_time_formatted = format_time_display(visit_data.get('visit_time')) if visit_data.get('visit_time') else "N/A"
            actions = {
                "View Summary": lambda v=visit_data: handle_patient_action("View Summary", v),
            }
            card_data = {
                'name': patient_name,
                'id': visit_data.get('patient_id'),
                'dob': visit_data.get('patient_dob'),
                'gender': visit_data.get('patient_gender'),
                'last_appointment_time': visit_time_formatted,
                'last_appointment_type': visit_data.get('visit_type'),
                'status': visit_data.get('status', 'Completed'),
            }
            try:
                PatientCard(patient_data=card_data, actions=actions, key=f"completed_card_{visit_data.get('visit_id')}")
            except Exception as e:
                st.error(f"Could not display patient card for {patient_name}: {e}")
        st.markdown("---")
    
    if other_visits:
        st.subheader("Other Status")
        for visit_data in other_visits:
             st.write(visit_data) # Basic display for now


def show_todays_patients_page():
    """Main function to display the Today's Patients page."""
    require_authentication()
    require_role_access([USER_ROLES['DOCTOR']]) # Ensure role access
    
    inject_css() # Inject global styles if any specific to this page are added

    st.markdown("<h1>📅 Today's Patients</h1>", unsafe_allow_html=True)
    
    doctor = get_current_user()
    if doctor:
        st.info(f"Displaying today's patient list for Dr. {doctor.get('full_name', 'N/A')}.")
        render_todays_patients_list(doctor)
    else:
        st.error("Could not retrieve doctor information. Please log in again.")

if __name__ == "__main__":
    # Mock session state for isolated testing
    if 'user' not in st.session_state:
        st.session_state.user = {
            'id': 'doc789', 
            'username': 'dr_today', 
            'role': USER_ROLES['DOCTOR'], 
            'full_name': 'Dr. Every Day',
            'email': 'dr.every@example.com'
        }
        st.session_state.authenticated = True
        st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)
    
    # show_todays_patients_page() # Called at module level now

# This call ensures Streamlit runs the page content when navigating
show_todays_patients_page()

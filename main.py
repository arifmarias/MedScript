import streamlit as st
from database.init_db import check_and_initialize_database
from auth.permissions import get_allowed_navigation_items # Added import
from auth.authentication import (
    initialize_session,
    is_authenticated,
    show_login_page,
    logout_user,
    get_current_user,
    check_session_validity,
)

st.set_page_config(
    page_title="MedScript Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    check_and_initialize_database() # <<< ADD THIS LINE
    initialize_session()
    check_session_validity()  # Handle session expiry

    if is_authenticated():
        user = get_current_user()
        st.sidebar.success(f"Welcome, {user['full_name']}!")
        if st.sidebar.button("Log Out"):
            logout_user()
            st.rerun()

        # Add custom navigation links
        st.sidebar.markdown("---") # Optional separator
        st.sidebar.header("Navigation")
        allowed_pages = get_allowed_navigation_items() # This line should already be there or be similar

        for page_info in allowed_pages:
            # Assuming page_info['path'] is like 'pages/1_doctor_dashboard.py'
            # We need to extract '1_doctor_dashboard' for the URL
            try:
                path_parts = page_info['path'].split('/')
                filename_with_ext = path_parts[-1] # Should be '1_doctor_dashboard.py'
                url_component = filename_with_ext.replace('.py', '')

                link_markdown = f"- [{page_info.get('icon', '')} {page_info['label']}]({url_component})"
                st.sidebar.markdown(link_markdown, unsafe_allow_html=True)
            except Exception as e:
                # Log or handle potential errors if path format is unexpected
                st.sidebar.error(f"Could not create link for {page_info.get('label', 'Unknown page')}")

        st.sidebar.markdown("---") # Optional separator

        # The main area welcome message can remain
        st.markdown("""
            # Welcome to MedScript Pro!

            Please use the navigation panel on the left to access different sections of the application based on your role.
            If you don't see the navigation panel, click the `>` arrow in the top-left corner.
        """, unsafe_allow_html=True)
    else:
        show_login_page()

if __name__ == "__main__":
    main()

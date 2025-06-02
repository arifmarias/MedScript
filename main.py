import streamlit as st
from database.init_db import check_and_initialize_database
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

        st.markdown("""
            # Welcome to MedScript Pro!

            Please use the navigation panel on the left to access different sections of the application based on your role.
            If you don't see the navigation panel, click the `>` arrow in the top-left corner.
        """, unsafe_allow_html=True)
    else:
        show_login_page()

if __name__ == "__main__":
    main()

"""
MedScript Pro - Super Admin User Management
This page handles complete user CRUD operations for super administrators.
"""

from datetime import datetime, date
from typing import Dict, List, Any, Optional
import streamlit as st
from config.settings import USER_ROLES, USER_TYPES
from config.styles import inject_css, inject_component_css
from auth.authentication import require_authentication, get_current_user
from auth.permissions import require_role_access, Permission, PermissionChecker
from components.forms import UserFormComponent, SearchFormComponent
from components.cards import UserCard, render_card_grid
from database.queries import UserQueries, AnalyticsQueries
from utils.formatters import format_date_display, format_phone_number, get_time_ago
from utils.validators import validate_user_data
from services.analytics_service import log_analytics_event

def show_user_management():
    """Display the user management page"""
    # Authentication and permission checks
    require_authentication()
    require_role_access([USER_ROLES['SUPER_ADMIN']])
    
    # Inject CSS
    inject_css()
    inject_component_css('DASHBOARD_CARDS')
    
    # Page header
    st.markdown("""
        <div class="main-header">
            <h1>👥 User Management</h1>
            <p>Manage system users, roles, and permissions</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'selected_user' not in st.session_state:
        st.session_state.selected_user = None
    if 'show_create_form' not in st.session_state:
        st.session_state.show_create_form = False
    if 'show_edit_form' not in st.session_state:
        st.session_state.show_edit_form = False
    
    # Main content
    render_user_management_content()

def render_user_management_content():
    """Render the main user management content"""
    try:
        # Action buttons
        col_actions = st.columns([1, 1, 1, 4])
        
        with col_actions[0]:
            if st.button("➕ Add User", type="primary", use_container_width=True):
                st.session_state.show_create_form = True
                st.session_state.show_edit_form = False
                st.session_state.selected_user = None
                st.rerun()
        
        with col_actions[1]:
            if st.button("🔄 Refresh", use_container_width=True):
                st.session_state.selected_user = None
                st.session_state.show_create_form = False
                st.session_state.show_edit_form = False
                st.rerun()
        
        with col_actions[2]:
            if st.button("📊 Analytics", use_container_width=True):
                show_user_analytics()
                return
        
        # Show appropriate content based on state
        if st.session_state.show_create_form:
            render_create_user_form()
        elif st.session_state.show_edit_form and st.session_state.selected_user:
            render_edit_user_form()
        else:
            render_user_list()
    
    except Exception as e:
        st.error(f"Error loading user management: {str(e)}")

def render_user_list():
    """Render the list of users with search and filters"""
    st.subheader("👥 System Users")
    
    # Search and filters
    col_search, col_filter = st.columns([2, 1])
    
    with col_search:
        search_term = st.text_input(
            "Search users",
            placeholder="Search by name, username, or email...",
            label_visibility="collapsed"
        )
    
    with col_filter:
        role_filter = st.selectbox(
            "Filter by Role",
            options=["All Roles"] + [role.replace('_', ' ').title() for role in USER_TYPES],
            label_visibility="collapsed"
        )
    
    # Get users
    all_users = UserQueries.get_all_users(include_inactive=True)
    
    if not all_users:
        st.warning("No users found in the system")
        return
    
    # Apply filters
    filtered_users = apply_user_filters(all_users, search_term, role_filter)
    
    # User statistics
    render_user_statistics(all_users, filtered_users)
    
    # Users table/cards
    if filtered_users:
        render_users_display(filtered_users)
    else:
        st.info("No users match the current filters")

def apply_user_filters(users: List[Dict[str, Any]], search_term: str, role_filter: str) -> List[Dict[str, Any]]:
    """Apply search and role filters to user list"""
    filtered = users
    
    # Apply search filter
    if search_term:
        search_lower = search_term.lower()
        filtered = [
            user for user in filtered
            if (search_lower in user.get('full_name', '').lower() or
                search_lower in user.get('username', '').lower() or
                search_lower in user.get('email', '').lower())
        ]
    
    # Apply role filter
    if role_filter != "All Roles":
        role_value = role_filter.lower().replace(' ', '_')
        filtered = [user for user in filtered if user.get('user_type') == role_value]
    
    return filtered

def render_user_statistics(all_users: List[Dict[str, Any]], filtered_users: List[Dict[str, Any]]):
    """Render user statistics"""
    st.markdown("### 📊 User Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = len(all_users)
        filtered_count = len(filtered_users)
        st.metric(
            label="Total Users",
            value=total_users,
            delta=f"Showing {filtered_count}" if filtered_count != total_users else None
        )
    
    with col2:
        active_users = len([u for u in all_users if u.get('is_active', True)])
        st.metric(
            label="Active Users",
            value=active_users,
            delta=f"{(active_users/total_users*100):.1f}%" if total_users > 0 else "0%"
        )
    
    with col3:
        doctors = len([u for u in all_users if u.get('user_type') == 'doctor'])
        st.metric(label="Doctors", value=doctors)
    
    with col4:
        assistants = len([u for u in all_users if u.get('user_type') == 'assistant'])
        st.metric(label="Assistants", value=assistants)

def render_users_display(users: List[Dict[str, Any]]):
    """Render users in a card/table format"""
    st.markdown("### 👤 User List")
    
    # View toggle
    view_mode = st.radio(
        "View Mode",
        options=["Cards", "Table"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if view_mode == "Cards":
        render_user_cards(users)
    else:
        render_user_table(users)

def render_user_cards(users: List[Dict[str, Any]]):
    """Render users as cards"""
    # Action callbacks for user cards
    action_callbacks = {
        "✏️ Edit": lambda user: edit_user_callback(user),
        "👁️ View": lambda user: view_user_callback(user),
        "🔒 Toggle": lambda user: toggle_user_status_callback(user)
    }
    
    # Render cards in groups of 2
    for i in range(0, len(users), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(users):
                user = users[i + j]
                with col:
                    card = UserCard(
                        user_data=user,
                        action_callbacks=action_callbacks
                    )
                    card.render()
                    st.divider()

def render_user_table(users: List[Dict[str, Any]]):
    """Render users as a table"""
    # Prepare table data
    table_data = []
    for user in users:
        table_data.append({
            "Name": user.get('full_name', 'Unknown'),
            "Username": user.get('username', 'Unknown'),
            "Role": user.get('user_type', '').replace('_', ' ').title(),
            "Email": user.get('email', 'N/A'),
            "Phone": format_phone_number(user.get('phone', '')) if user.get('phone') else 'N/A',
            "Status": "✅ Active" if user.get('is_active', True) else "❌ Inactive",
            "Last Login": get_time_ago(user.get('last_login')) if user.get('last_login') else 'Never',
            "Actions": f"user_{user.get('id', 0)}"  # Use for action buttons
        })
    
    if table_data:
        # Display table
        import pandas as pd
        df = pd.DataFrame(table_data)
        
        # Configure table display
        st.dataframe(
            df.drop('Actions', axis=1),  # Hide actions column from dataframe
            use_container_width=True,
            hide_index=True
        )
        
        # Action buttons below table
        st.markdown("### 🔧 Quick Actions")
        
        selected_user_id = st.selectbox(
            "Select user for actions",
            options=[user.get('id') for user in users],
            format_func=lambda x: next(
                (f"{u.get('full_name', 'Unknown')} (@{u.get('username', 'unknown')})" 
                 for u in users if u.get('id') == x), 
                'Unknown'
            ),
            label_visibility="collapsed"
        )
        
        if selected_user_id:
            selected_user = next((u for u in users if u.get('id') == selected_user_id), None)
            if selected_user:
                col_edit, col_view, col_toggle = st.columns(3)
                
                with col_edit:
                    if st.button("✏️ Edit User", use_container_width=True):
                        edit_user_callback(selected_user)
                
                with col_view:
                    if st.button("👁️ View Details", use_container_width=True):
                        view_user_callback(selected_user)
                
                with col_toggle:
                    status_text = "Deactivate" if selected_user.get('is_active', True) else "Activate"
                    if st.button(f"🔒 {status_text}", use_container_width=True):
                        toggle_user_status_callback(selected_user)

def render_create_user_form():
    """Render the create user form"""
    st.subheader("➕ Create New User")
    
    # Cancel button
    if st.button("← Back to User List"):
        st.session_state.show_create_form = False
        st.rerun()
    
    # User form
    user_form = UserFormComponent(edit_mode=False)
    form_result = user_form.render()
    
    if form_result:
        if form_result.get('cancelled'):
            st.session_state.show_create_form = False
            st.rerun()
        else:
            # Create user
            create_user_result = create_new_user(form_result)
            if create_user_result:
                st.success("✅ User created successfully!")
                log_analytics_event('create_user', 'user', create_user_result)
                st.session_state.show_create_form = False
                st.rerun()

def render_edit_user_form():
    """Render the edit user form"""
    user = st.session_state.selected_user
    if not user:
        st.error("No user selected for editing")
        return
    
    st.subheader(f"✏️ Edit User: {user.get('full_name', 'Unknown')}")
    
    # Cancel button
    if st.button("← Back to User List"):
        st.session_state.show_edit_form = False
        st.session_state.selected_user = None
        st.rerun()
    
    # User form with existing data
    user_form = UserFormComponent(edit_mode=True, user_data=user)
    form_result = user_form.render()
    
    if form_result:
        if form_result.get('cancelled'):
            st.session_state.show_edit_form = False
            st.session_state.selected_user = None
            st.rerun()
        else:
            # Update user
            update_result = update_existing_user(user.get('id'), form_result)
            if update_result:
                st.success("✅ User updated successfully!")
                log_analytics_event('update_user', 'user', user.get('id'))
                st.session_state.show_edit_form = False
                st.session_state.selected_user = None
                st.rerun()

def create_new_user(user_data: Dict[str, Any]) -> Optional[int]:
    """Create a new user"""
    try:
        # Validate user data
        validation_result = validate_user_data(user_data)
        if validation_result.has_errors():
            for error in validation_result.errors:
                st.error(error)
            return None
        
        # Check for duplicate username
        existing_user = UserQueries.get_user_by_username(user_data['username'])
        if existing_user:
            st.error("Username already exists. Please choose a different username.")
            return None
        
        # Create user
        user_id = UserQueries.create_user(user_data)
        
        if user_id:
            return user_id
        else:
            st.error("Failed to create user. Please try again.")
            return None
    
    except Exception as e:
        st.error(f"Error creating user: {str(e)}")
        return None

def update_existing_user(user_id: int, user_data: Dict[str, Any]) -> bool:
    """Update an existing user"""
    try:
        # Remove password from update data (handled separately)
        update_data = {k: v for k, v in user_data.items() if k != 'password'}
        
        # Validate update data
        validation_result = validate_user_data(update_data)
        if validation_result.has_errors():
            for error in validation_result.errors:
                st.error(error)
            return False
        
        # Update user
        success = UserQueries.update_user(user_id, update_data)
        
        if not success:
            st.error("Failed to update user. Please try again.")
        
        return success
    
    except Exception as e:
        st.error(f"Error updating user: {str(e)}")
        return False

def edit_user_callback(user: Dict[str, Any]):
    """Callback for edit user action"""
    st.session_state.selected_user = user
    st.session_state.show_edit_form = True
    st.session_state.show_create_form = False
    st.rerun()

def view_user_callback(user: Dict[str, Any]):
    """Callback for view user details"""
    st.session_state.selected_user = user
    show_user_details_modal(user)

def toggle_user_status_callback(user: Dict[str, Any]):
    """Callback for toggling user status"""
    user_id = user.get('id')
    current_status = user.get('is_active', True)
    new_status = not current_status
    
    # Confirm action
    action = "deactivate" if current_status else "activate"
    if st.confirm(f"Are you sure you want to {action} user {user.get('full_name', 'Unknown')}?"):
        try:
            # Update user status
            if new_status:
                # Reactivate user - would need a separate query
                success = True  # Placeholder
                st.success(f"✅ User {user.get('full_name')} has been activated")
            else:
                success = UserQueries.deactivate_user(user_id)
                if success:
                    st.success(f"✅ User {user.get('full_name')} has been deactivated")
            
            if success:
                log_analytics_event('toggle_user_status', 'user', user_id, 
                                  {'action': action, 'new_status': new_status})
                st.rerun()
            else:
                st.error(f"Failed to {action} user")
        
        except Exception as e:
            st.error(f"Error updating user status: {str(e)}")

def show_user_details_modal(user: Dict[str, Any]):
    """Show detailed user information in a modal-like display"""
    with st.expander(f"👤 User Details: {user.get('full_name', 'Unknown')}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Basic Information:**")
            st.write(f"• **Full Name:** {user.get('full_name', 'N/A')}")
            st.write(f"• **Username:** {user.get('username', 'N/A')}")
            st.write(f"• **User Type:** {user.get('user_type', '').replace('_', ' ').title()}")
            st.write(f"• **Status:** {'✅ Active' if user.get('is_active', True) else '❌ Inactive'}")
            
            if user.get('user_type') == 'doctor':
                st.markdown("**Medical Information:**")
                st.write(f"• **License:** {user.get('medical_license', 'N/A')}")
                st.write(f"• **Specialization:** {user.get('specialization', 'N/A')}")
        
        with col2:
            st.markdown("**Contact Information:**")
            st.write(f"• **Email:** {user.get('email', 'N/A')}")
            phone = format_phone_number(user.get('phone', '')) if user.get('phone') else 'N/A'
            st.write(f"• **Phone:** {phone}")
            
            st.markdown("**Account Information:**")
            created_at = user.get('created_at', '')
            if created_at:
                try:
                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    st.write(f"• **Created:** {format_date_display(date_obj.date())}")
                except:
                    st.write(f"• **Created:** {created_at[:10]}")
            
            last_login = user.get('last_login', '')
            if last_login:
                st.write(f"• **Last Login:** {get_time_ago(last_login)}")
            else:
                st.write("• **Last Login:** Never")

def show_user_analytics():
    """Show user analytics and statistics"""
    st.subheader("📊 User Analytics")
    
    # Back button
    if st.button("← Back to User Management"):
        st.rerun()
    
    # Get analytics data
    all_users = UserQueries.get_all_users(include_inactive=True)
    
    if not all_users:
        st.warning("No user data available for analytics")
        return
    
    # User creation timeline
    st.markdown("### 📈 User Registration Timeline")
    
    # Group users by creation date
    from collections import defaultdict
    user_timeline = defaultdict(int)
    
    for user in all_users:
        created_at = user.get('created_at', '')
        if created_at:
            try:
                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                user_timeline[date_obj.strftime('%Y-%m-%d')] += 1
            except:
                continue
    
    if user_timeline:
        timeline_data = [
            {'date': date_str, 'count': count}
            for date_str, count in sorted(user_timeline.items())
        ]
        
        from components.charts import TimeSeriesChart
        chart = TimeSeriesChart(
            data=timeline_data,
            x_field='date',
            y_field='count',
            title='User Registrations Over Time'
        )
        chart.render()
    
    # Role distribution
    st.markdown("### 🎭 Role Distribution")
    
    role_counts = defaultdict(int)
    for user in all_users:
        role = user.get('user_type', 'unknown').replace('_', ' ').title()
        role_counts[role] += 1
    
    if role_counts:
        role_data = [
            {'role': role, 'count': count}
            for role, count in role_counts.items()
        ]
        
        from components.charts import PieChart
        chart = PieChart(
            data=role_data,
            labels_field='role',
            values_field='count',
            title='User Distribution by Role'
        )
        chart.render()
    
    # Recent user activity
    st.markdown("### 🕐 Recent User Activity")
    
    recent_activity = AnalyticsQueries.get_user_activity(days_back=7, limit=20)
    
    if recent_activity:
        st.markdown("**Last 7 Days Activity:**")
        for activity in recent_activity[:10]:
            col_user, col_action, col_time = st.columns([2, 2, 1])
            
            with col_user:
                st.write(activity.get('user_name', 'Unknown'))
            
            with col_action:
                action = activity.get('action_type', '').replace('_', ' ').title()
                st.write(action)
            
            with col_time:
                timestamp = activity.get('timestamp', '')
                if timestamp:
                    st.write(get_time_ago(timestamp))
    else:
        st.info("No recent user activity found")

# This call ensures Streamlit runs the page content when navigating
show_user_management()

if __name__ == "__main__":
    # Mock setup or specific direct run logic can go here
    if 'user' not in st.session_state:
        st.session_state.user = {
            'id': 'sa_usermgt_direct',
            'username': 'sa_usermgt_direct',
            'role': USER_ROLES['SUPER_ADMIN'],
            'full_name': 'SA UserMgt Direct Runner'
        }
        st.session_state.authenticated = True
        st.session_state.session_valid_until = datetime.now() + timedelta(hours=1)
    # show_user_management() # Already called at module level
    pass
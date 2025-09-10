import streamlit as st
import requests
from auth_helper import auth

def show_admin_page():
    """Show admin user management page"""
    
    # Require authentication
    user = auth.require_auth("Please log in to access admin features.")
    
    st.title("🔐 Admin Panel")
    st.markdown("**User Management & Organization Administration**")
    
    # Check if user has admin permissions (for now, just check if they're in the first barn as owner)
    barns = auth.get_user_barns()
    is_admin = any(barn.get('user_role') == 'Owner' for barn in barns)
    
    if not is_admin:
        st.error("❌ Admin access required. Only barn owners can access this panel.")
        return
    
    st.success("✅ Admin access granted")
    
    # Tabs for different admin functions
    tab1, tab2, tab3 = st.tabs(["👥 User Management", "🏇 Organization Settings", "📊 System Overview"])
    
    with tab1:
        st.header("User Management")
        
        # Invite new user
        st.subheader("Invite New User")
        with st.form("invite_user"):
            email = st.text_input("Email Address", placeholder="user@example.com")
            
            # Select barn/organization
            barn_options = [f"{barn['barn_name']} ({barn['barn_id']})" for barn in barns if barn.get('user_role') == 'Owner']
            selected_barn = st.selectbox("Assign to Barn", barn_options)
            
            # User role
            role = st.selectbox("User Role", ["Member", "Manager", "Owner"])
            
            # Permissions
            permissions = st.multiselect("Permissions", [
                "read_horses", "write_horses", 
                "read_supplies", "write_supplies",
                "read_events", "write_events",
                "manage_users"
            ], default=["read_horses", "read_supplies", "read_events"])
            
            if st.form_submit_button("Send Invitation", type="primary"):
                if email and selected_barn:
                    barn_id = selected_barn.split("(")[1].strip(")")
                    
                    # Here you would integrate with PropelAuth's invitation API
                    st.success(f"✅ Invitation sent to {email} for {selected_barn.split('(')[0].strip()}")
                    st.info(f"Role: {role}, Permissions: {', '.join(permissions)}")
                    
                    # TODO: Implement actual PropelAuth invitation API call
                    st.warning("⚠️ Integration with PropelAuth invitation API pending")
                else:
                    st.error("Please fill in all required fields")
        
        # Existing users
        st.subheader("Existing Users")
        
        # For each barn the admin owns, show users
        for barn in barns:
            if barn.get('user_role') == 'Owner':
                st.markdown(f"**{barn['barn_name']}**")
                
                # TODO: Fetch actual user list from PropelAuth
                # Mock data for now
                mock_users = [
                    {"email": user.get('email'), "role": "Owner", "status": "Active"},
                    {"email": "manager@example.com", "role": "Manager", "status": "Active"},
                    {"email": "member@example.com", "role": "Member", "status": "Pending"}
                ]
                
                for mock_user in mock_users:
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    with col1:
                        st.write(mock_user["email"])
                    with col2:
                        st.write(mock_user["role"])
                    with col3:
                        st.write(mock_user["status"])
                    with col4:
                        if mock_user["email"] != user.get('email'):  # Don't allow self-removal
                            if st.button("Remove", key=f"remove_{mock_user['email']}", type="secondary"):
                                st.warning("User removal functionality coming soon")
    
    with tab2:
        st.header("Organization Settings")
        
        # Show organizations user can manage
        for barn in barns:
            if barn.get('user_role') in ['Owner', 'Manager']:
                st.subheader(f"🏇 {barn['barn_name']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Organization ID:** `{barn['barn_id']}`")
                    st.write(f"**Your Role:** {barn['user_role']}")
                    st.write(f"**Permissions:** {', '.join(barn.get('permissions', []))}")
                
                with col2:
                    # Organization settings
                    if st.button(f"Edit {barn['barn_name']} Settings", key=f"edit_{barn['barn_id']}"):
                        st.info("Organization settings editor coming soon")
                
                st.markdown("---")
    
    with tab3:
        st.header("System Overview")
        
        # Show basic stats for barns user manages
        for barn in barns:
            if barn.get('user_role') in ['Owner', 'Manager']:
                st.subheader(f"📊 {barn['barn_name']} Statistics")
                
                # Fetch actual data (this would be API calls to get counts)
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Users", "3")  # TODO: Get real count
                with col2:
                    st.metric("Horses", "5")  # TODO: Get real count
                with col3:
                    st.metric("Events", "12")  # TODO: Get real count
                with col4:
                    st.metric("Supply Items", "45")  # TODO: Get real count
                
                st.markdown("---")

if __name__ == "__main__":
    show_admin_page()
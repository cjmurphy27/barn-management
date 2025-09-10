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
    tab1, tab2, tab3, tab4 = st.tabs(["👥 User Management", "🏇 Organization Settings", "📊 System Overview", "🐴 Horse Assignment"])
    
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
    
    with tab4:
        st.header("🐴 Horse-Barn Assignment")
        st.write("Assign horses to the correct barns for proper isolation.")
        
        backend_url = st.secrets.get("BACKEND_URL", "http://localhost:8002")
        
        # Get all horses
        try:
            response = requests.get(f"{backend_url}/api/v1/horses")
            if response.status_code == 200:
                horses = response.json()
                st.write(f"**Found {len(horses)} horses in database**")
                
                # Show current assignments
                with st.expander("Current Horse Assignments", expanded=True):
                    for i, horse in enumerate(horses):
                        barn_id = horse.get('barn_id', 'None')
                        st.write(f"{i+1}. **{horse.get('name', 'Unknown')}** (ID: {horse.get('id')}) - Barn: `{barn_id}`")
                
                # Assignment strategy
                st.subheader("📋 Recommended Barn Assignment Strategy")
                st.info("""
                **Strategy:** Based on PropelAuth organization setup:
                - **8 horses** → Fernbell (CJ Murphy's main barn)
                - **1 horse** → Sunset Stables  
                - **1 horse** → Golden Gate Ranch
                - **Remaining horses** → Fernbell
                """)
                
                assignments = []
                
                # First 8 to Fernbell
                fernbell_count = min(8, len(horses))
                for i in range(fernbell_count):
                    assignments.append({
                        'horse_id': horses[i]['id'],
                        'horse_name': horses[i]['name'],
                        'barn_id': 'fernbell_barn',
                        'barn_name': 'Fernbell'
                    })
                
                # 9th horse to Sunset Stables
                if len(horses) > 8:
                    assignments.append({
                        'horse_id': horses[8]['id'],
                        'horse_name': horses[8]['name'], 
                        'barn_id': 'sunset_stables',
                        'barn_name': 'Sunset Stables'
                    })
                
                # 10th horse to Golden Gate Ranch
                if len(horses) > 9:
                    assignments.append({
                        'horse_id': horses[9]['id'],
                        'horse_name': horses[9]['name'],
                        'barn_id': 'golden_gate_ranch', 
                        'barn_name': 'Golden Gate Ranch'
                    })
                
                # Remaining horses to Fernbell
                for i in range(10, len(horses)):
                    assignments.append({
                        'horse_id': horses[i]['id'],
                        'horse_name': horses[i]['name'],
                        'barn_id': 'fernbell_barn',
                        'barn_name': 'Fernbell'
                    })
                
                # Show assignment plan
                st.subheader("🗂️ Assignment Plan")
                barn_counts = {}
                for assignment in assignments:
                    barn_name = assignment['barn_name']
                    barn_counts[barn_name] = barn_counts.get(barn_name, 0) + 1
                    st.write(f"• **{assignment['horse_name']}** → {assignment['barn_name']}")
                
                # Summary
                st.subheader("📊 Assignment Summary")
                for barn_name, count in barn_counts.items():
                    st.write(f"• **{barn_name}:** {count} horses")
                
                # Execute button
                st.markdown("---")
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("🚀 Execute Barn Assignments", type="primary", use_container_width=True):
                        success_count = 0
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i, assignment in enumerate(assignments):
                            horse_id = assignment['horse_id']
                            barn_id = assignment['barn_id']
                            horse_name = assignment['horse_name']
                            barn_name = assignment['barn_name']
                            
                            status_text.text(f"Assigning {horse_name} to {barn_name}...")
                            
                            try:
                                update_response = requests.put(
                                    f"{backend_url}/api/v1/horses/{horse_id}",
                                    json={"barn_id": barn_id}
                                )
                                
                                if update_response.status_code == 200:
                                    success_count += 1
                                else:
                                    st.error(f"Failed to assign {horse_name}: {update_response.status_code}")
                                    
                            except Exception as e:
                                st.error(f"Error assigning {horse_name}: {str(e)}")
                            
                            progress_bar.progress((i + 1) / len(assignments))
                        
                        status_text.text("Assignment complete!")
                        
                        if success_count == len(assignments):
                            st.success(f"🎉 Successfully assigned all {success_count} horses to barns!")
                            st.balloons()
                            st.info("🔄 **Next step:** Go back to the main app and refresh to see horses in their assigned barns.")
                        else:
                            st.warning(f"⚠️ Assigned {success_count}/{len(assignments)} horses. Some assignments may have failed.")
                
                with col2:
                    st.info("⚠️ **Warning:** This will update all horse-barn assignments in the database. Make sure this is what you want to do.")
                
            else:
                st.error(f"❌ Failed to get horses from backend: {response.status_code}")
                st.code(f"URL: {backend_url}/api/v1/horses")
                if response.text:
                    st.code(response.text[:500])
                
        except Exception as e:
            st.error(f"❌ Error connecting to backend: {str(e)}")
            st.code(f"Backend URL: {backend_url}")

if __name__ == "__main__":
    show_admin_page()
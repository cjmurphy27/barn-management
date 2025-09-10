"""
PropelAuth integration for Streamlit using native OAuth
"""
import streamlit as st
from propelauth_py import init_base_auth, UnauthorizedException
from typing import Optional, Dict, Any, List

class StreamlitPropelAuth:
    def __init__(self):
        # Get configuration from Streamlit secrets
        self.auth_url = st.secrets.get("PROPELAUTH_URL", "https://34521247761.propelauthtest.com")
        self.backend_url = st.secrets.get("BACKEND_URL", "http://localhost:8002")
        
        # Initialize PropelAuth for backend operations (user lookup, etc.)
        # Note: This uses the API key for backend operations, not OAuth
        self.propelauth_api_key = "2952109078f3ac5b1ac7b529e2befa8175b6ec7e9ed2436f26e43f9b38b50240a67522915e956e33afd4e910f3de61a1"
        
        try:
            self.auth = init_base_auth(self.auth_url, self.propelauth_api_key)
        except Exception as e:
            st.error(f"Failed to initialize PropelAuth: {e}")
            self.auth = None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated using Streamlit's native OAuth"""
        return st.user.is_logged_in if hasattr(st, 'user') else False
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user information"""
        if not self.is_authenticated():
            return None
        
        try:
            # Get user info from Streamlit's native OAuth
            user_info = {
                "user_id": st.user.sub if hasattr(st.user, 'sub') else None,
                "email": st.user.email if hasattr(st.user, 'email') else None,
                "first_name": st.user.given_name if hasattr(st.user, 'given_name') else None,
                "last_name": st.user.family_name if hasattr(st.user, 'family_name') else None,
            }
            
            # Fetch additional user data from PropelAuth backend if we have user_id
            if user_info["user_id"] and self.auth:
                try:
                    # Get user organizations from PropelAuth
                    propel_user = self.auth.fetch_user_metadata_by_user_id(user_info["user_id"])
                    if propel_user:
                        user_info["organizations"] = propel_user.get("org_id_to_org_member_info", {})
                except Exception as e:
                    st.warning(f"Could not fetch user organizations: {e}")
                    user_info["organizations"] = {}
            
            return user_info
            
        except Exception as e:
            st.error(f"Error getting user info: {e}")
            return None
    
    def get_user_barns(self) -> List[Dict[str, Any]]:
        """Get barns/organizations the current user has access to"""
        user = self.get_current_user()
        if not user or not user.get("organizations"):
            return []
        
        barns = []
        for org_id, org_info in user["organizations"].items():
            barn = {
                "barn_id": org_id,
                "barn_name": org_info.get("org_name", "Unknown Barn"),
                "user_role": org_info.get("user_role", "Member"),
                "permissions": org_info.get("user_permissions", [])
            }
            barns.append(barn)
        
        return barns
    
    def show_login_interface(self):
        """Show native Streamlit login interface"""
        if not self.is_authenticated():
            st.info("🔐 **Please log in to access your barn management system**")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔑 Log In with PropelAuth", type="primary", use_container_width=True):
                    st.login()
        else:
            user = self.get_current_user()
            st.success(f"✅ Logged in as {user.get('email', 'User')}")
    
    def show_auth_sidebar(self):
        """Show authentication status and controls in sidebar"""
        with st.sidebar:
            if self.is_authenticated():
                user = self.get_current_user()
                
                # User info
                st.markdown("**Welcome Back:**")
                st.markdown(f'<div style="background-color: white; border: 1px solid #D2691E; border-radius: 8px; padding: 10px; margin-bottom: 16px;"><span style="color: #5D4037;">👤 {user.get("email", "User")}</span></div>', unsafe_allow_html=True)
                
                # Account management
                account_url = f"{self.auth_url}/account"
                if hasattr(st, 'link_button'):
                    st.link_button("🔧 Manage Account", account_url)
                
                # Barn selector
                barns = self.get_user_barns()
                if barns:
                    if len(barns) > 1:
                        st.markdown("**Select Barn:**")
                        barn_names = [f"{barn['barn_name']} ({barn['user_role']})" for barn in barns]
                        selected_barn_display = st.selectbox("Current Barn:", barn_names, label_visibility="collapsed")
                        
                        # Store selected barn in session state
                        selected_barn_name = selected_barn_display.split(" (")[0]
                        selected_barn_id = next((barn['barn_id'] for barn in barns if barn['barn_name'] == selected_barn_name), None)
                        
                        if selected_barn_id:
                            st.session_state.selected_barn_id = selected_barn_id
                            st.session_state.selected_barn_name = selected_barn_name
                    else:
                        st.markdown("**Your Barn:**")
                        st.markdown(f'<div style="background-color: white; border: 1px solid #D2691E; border-radius: 8px; padding: 10px; margin-bottom: 16px;"><span style="color: #5D4037;">🏇 {barns[0]["barn_name"]} ({barns[0]["user_role"]})</span></div>', unsafe_allow_html=True)
                        st.session_state.selected_barn_id = barns[0]['barn_id']
                        st.session_state.selected_barn_name = barns[0]['barn_name']
                
                # Logout button
                if st.button("🚪 Logout", use_container_width=True):
                    st.logout()
                    st.rerun()
            else:
                st.warning("🔒 Please log in")
                if st.button("Login", use_container_width=True):
                    st.login()
    
    def require_auth(self, message: str = "Please log in to access this page."):
        """Require authentication for a page"""
        if not self.is_authenticated():
            st.error(message)
            self.show_login_interface()
            st.stop()
        
        return self.get_current_user()

# Global auth instance
propel_auth = StreamlitPropelAuth()
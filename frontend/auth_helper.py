"""
Streamlit Authentication Helper for PropelAuth Integration

This module provides authentication functionality for the Streamlit frontend,
integrating with our PropelAuth-enabled FastAPI backend.

The approach uses PropelAuth's hosted login pages and JWT tokens.
"""

import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import jwt
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import time

class StreamlitAuth:
    def __init__(self):
        # Get configuration from Streamlit secrets or environment
        self.auth_url = "https://34521247761.propelauthtest.com"
        self.backend_url = "http://localhost:8002"
        self._config_loaded = False
    
    def _load_config(self):
        """Lazy load configuration to avoid Streamlit calls during import"""
        if not self._config_loaded:
            try:
                self.auth_url = st.secrets.get("PROPELAUTH_URL", "https://34521247761.propelauthtest.com")
                self.backend_url = st.secrets.get("BACKEND_URL", "http://localhost:8002")
            except:
                # Keep defaults
                pass
            self._config_loaded = True
        
    def get_login_url(self, redirect_uri: str = None) -> str:
        """Generate PropelAuth login URL with proper redirect"""
        self._load_config()
        if redirect_uri is None:
            redirect_uri = f"http://localhost:8501/?auth=callback"  # Default with callback
        
        # Use PropelAuth's simple login with redirect back to our app
        # PropelAuth handles the auth and redirects back to our callback URL
        params = urlencode({
            'redirect_uri': redirect_uri
        })
        return f"{self.auth_url}/login?{params}"
    
    def get_account_url(self) -> str:
        """Get PropelAuth account management URL"""
        self._load_config()
        return f"{self.auth_url}/account"
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.get_current_user() is not None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user from session state"""
        # First check session state
        if "user" in st.session_state and st.session_state.user:
            return st.session_state.user
        
        # Try to get access token (which handles backend OAuth flow)
        token = self.get_access_token()
        if not token:
            return None
        
        # If we have a token, user should be in session state
        if "user" in st.session_state and st.session_state.user:
            return st.session_state.user
        
        return None
    

    def get_access_token(self) -> Optional[str]:
        """Get access token from session - simplified working version"""
        # First check session state
        if "access_token" in st.session_state and st.session_state.access_token:
            return st.session_state.access_token
        
        # Don't process if user just logged out
        if st.session_state.get('user_logged_out', False):
            return None
        
        # For development, create a simple demo token
        # This allows testing the app functionality while we plan proper OAuth
        return None
    
    def set_access_token(self, token: str):
        """Set access token in session state"""
        st.session_state.access_token = token
    
    def _exchange_code_for_token(self, auth_code: str) -> Optional[str]:
        """Exchange OAuth authorization code for access token"""
        try:
            self._load_config()
            
            # Call our backend to exchange code for token
            response = requests.post(
                f"{self.backend_url}/api/v1/auth/exchange-code",
                json={
                    "code": auth_code,
                    "redirect_uri": "http://localhost:8501/?auth=callback"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("access_token"):
                    # Store user data
                    if "user" in result:
                        st.session_state.user = result["user"]
                    return result["access_token"]
            
            st.error(f"Token exchange failed: {response.status_code}")
            return None
                
        except Exception as e:
            st.error(f"Error exchanging authorization code: {str(e)}")
            return None
    
    def _fetch_real_propelauth_user(self, email: str) -> Optional[str]:
        """Fetch real user data from PropelAuth API (fallback method)"""
        try:
            self._load_config()
            
            # Call our backend endpoint to get real user data
            response = requests.post(
                f"{self.backend_url}/api/v1/auth/lookup-user",
                json={"email": email},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    user_data = result.get("user")
                    
                    # Store real user data in session
                    st.session_state.real_propelauth_user = user_data
                    
                    # Create a special token to indicate real auth
                    return f"real_propelauth_token_{user_data.get('user_id', 'unknown')}"
                else:
                    st.error(f"User lookup failed: {result.get('error')}")
                    return None
            else:
                st.error(f"API request failed: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Error fetching real user data: {str(e)}")
            return None

    def _create_demo_token(self, email: str) -> str:
        """Create a simple demo token for testing"""
        return f"demo_token_{email.split('@')[0]}"

    def _setup_demo_user(self, email: str):
        """Setup demo user with real barn data from backend"""
        with st.spinner(f"Setting up demo login for {email}..."):
            try:
                # Fetch real user data from the backend
                real_token = self._fetch_real_propelauth_user(email)
                if real_token:
                    if 'user_logged_out' in st.session_state:
                        del st.session_state.user_logged_out
                    
                    st.session_state.access_token = real_token
                    
                    # Get the real user data that was stored
                    if 'real_propelauth_user' in st.session_state:
                        user_data = st.session_state.real_propelauth_user
                        formatted_user = {
                            "user_id": user_data.get("user_id"),
                            "email": user_data.get("email"),
                            "first_name": user_data.get("first_name"),
                            "last_name": user_data.get("last_name"),
                            "barns": user_data.get("organizations", [])
                        }
                        st.session_state.user = formatted_user
                    
                    st.success(f"✅ Logged in as {email}")
                    st.rerun()
                else:
                    st.error(f"Failed to setup demo user for {email}")
                    
            except Exception as e:
                st.error(f"Error setting up demo user: {str(e)}")

    def clear_auth(self):
        """Clear authentication state"""
        if "user" in st.session_state:
            del st.session_state.user
        if "access_token" in st.session_state:
            del st.session_state.access_token
        if "real_propelauth_user" in st.session_state:
            del st.session_state.real_propelauth_user
        if "auth_callback_detected" in st.session_state:
            del st.session_state.auth_callback_detected
        if "processing_auth" in st.session_state:
            del st.session_state.processing_auth
        if "auth_completed" in st.session_state:
            del st.session_state.auth_completed
        if "callback_processed" in st.session_state:
            del st.session_state.callback_processed
        if "authentication_complete" in st.session_state:
            del st.session_state.authentication_complete
        if "processed_callback_id" in st.session_state:
            del st.session_state.processed_callback_id
        if "processing_callback" in st.session_state:
            del st.session_state.processing_callback
        
        # Mark that user explicitly logged out
        st.session_state.user_logged_out = True
    
    def get_user_barns(self) -> list:
        """Get barns the current user has access to"""
        token = self.get_access_token()
        if not token:
            return []
        
        # Handle real PropelAuth token
        if token and token.startswith("real_propelauth_token_"):
            real_user_data = st.session_state.get('real_propelauth_user')
            if real_user_data:
                return real_user_data.get("organizations", [])
        
        # Demo token handling removed
        
        try:
            self._load_config()
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{self.backend_url}/api/v1/auth/barns", headers=headers)
            
            if response.status_code == 200:
                return response.json().get("barns", [])
            else:
                return []
                
        except Exception as e:
            st.error(f"Error fetching barn access: {str(e)}")
            return []
    
    def show_login_interface(self):
        """Show simple demo login interface for development"""
        st.info("🔐 **Demo Login - Choose a test user**")
        
        # Center the login options
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("**Select demo user:**")
            
            if st.button("👤 CJ Murphy (cjmurphy.nyc@gmail.com)", use_container_width=True, type="primary"):
                # Set demo authentication for CJ and fetch real barn data
                self._setup_demo_user("cjmurphy.nyc@gmail.com")
                
            if st.button("👤 Chris Carril (chris@carril.com)", use_container_width=True, type="secondary"):
                # Set demo authentication for Chris and fetch real barn data
                self._setup_demo_user("chris@carril.com")
        
        st.markdown("---")
        
        # Next steps info
        with st.expander("🔧 Next Steps", expanded=False):
            st.write("**This is a temporary demo login for testing.**")
            st.write("**Next steps for production:**")
            st.write("1. Switch to Production PropelAuth environment")
            st.write("2. Implement proper OAuth 2.0 flow")
            st.write("3. Configure real multi-user authentication")
            st.write("4. Deploy to Railway with production settings")

    def show_login_button(self, text: str = "Login with PropelAuth"):
        """Show login button that redirects to PropelAuth"""
        login_url = self.get_login_url()
        
        # Use Streamlit's link_button (available in newer versions) or markdown link
        try:
            # Try using st.link_button if available (Streamlit 1.28+)
            if hasattr(st, 'link_button'):
                st.link_button(text, login_url)
            else:
                # Fallback to markdown link
                st.markdown(f'<a href="{login_url}" target="_blank" style="text-decoration: none;"><button style="background-color: #8BB6CC; color: #1A3A52; border: none; padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer;">{text}</button></a>', unsafe_allow_html=True)
        except:
            # Ultimate fallback
            st.markdown(f"[{text}]({login_url})")
    
    def show_auth_sidebar(self):
        """Show clean authentication status and controls in sidebar"""
        user = self.get_current_user()
        
        with st.sidebar:
            if user:
                # User info with consistent styling matching pulldowns
                st.markdown("**Welcome Back:**")
                st.markdown(f'<div style="background-color: white; border: 1px solid #D2691E; border-radius: 8px; padding: 10px; margin-bottom: 16px;"><span style="color: #5D4037;">👤 {user.get("email", "User")}</span></div>', unsafe_allow_html=True)
                
                # Account button under username
                account_url = self.get_account_url()
                if hasattr(st, 'link_button'):
                    st.link_button("🔧 Manage Account", account_url)
                else:
                    st.markdown(f'<a href="{account_url}" target="_blank" style="text-decoration: none;"><button style="background-color: #D2691E; color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer; width: 100%;">🔧 Manage Account</button></a>', unsafe_allow_html=True)
                
                # Show barn selector
                barns = self.get_user_barns()
                if barns:
                    if len(barns) > 1:
                        st.markdown("**Select Barn:**")
                        barn_names = [f"{barn['barn_name']} ({barn['user_role']})" for barn in barns]
                        selected_barn_display = st.selectbox("Current Barn:", barn_names, label_visibility="collapsed")
                        
                        # Get the selected barn ID for filtering
                        selected_barn_name = selected_barn_display.split(" (")[0]  # Extract barn name
                        selected_barn_id = next((barn['barn_id'] for barn in barns if barn['barn_name'] == selected_barn_name), None)
                        
                        # Store selected barn in session state for filtering
                        if selected_barn_id:
                            st.session_state.selected_barn_id = selected_barn_id
                            st.session_state.selected_barn_name = selected_barn_name
                    else:
                        st.markdown("**Your Barn:**")
                        st.markdown(f'<div style="background-color: white; border: 1px solid #D2691E; border-radius: 8px; padding: 10px; margin-bottom: 16px;"><span style="color: #5D4037;">🏇 {barns[0]["barn_name"]} ({barns[0]["user_role"]})</span></div>', unsafe_allow_html=True)
                        # Store single barn info
                        st.session_state.selected_barn_id = barns[0]['barn_id']
                        st.session_state.selected_barn_name = barns[0]['barn_name']
            else:
                st.warning("🔒 Please log in")
                self.show_login_button("Login")
    
    def logout(self):
        """Logout user and clear all authentication state"""
        # Clear URL parameters that might contain auth callback
        try:
            st.experimental_set_query_params()
        except:
            pass
        
        # Clear all authentication state
        self.clear_auth()
        
        # Clear all session state related to authentication
        if "selected_barn_id" in st.session_state:
            del st.session_state.selected_barn_id
        if "selected_barn_name" in st.session_state:
            del st.session_state.selected_barn_name
        
        st.success("Logged out successfully!")
        
        # Provide link to complete logout on PropelAuth
        logout_url = f"{self.auth_url}/logout"
        st.info("To completely log out from all applications:")
        if hasattr(st, 'link_button'):
            st.link_button("Complete PropelAuth Logout", logout_url, type="secondary")
        else:
            st.markdown(f"[Complete PropelAuth Logout]({logout_url})")
    
    def require_auth(self, message: str = "Please log in to access this page."):
        """Require authentication for a page"""
        if not self.is_authenticated():
            st.error(message)
            self.show_login_button()
            st.stop()
        
        return self.get_current_user()

# Global auth instance
auth = StreamlitAuth()
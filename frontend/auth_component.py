import streamlit as st
import requests
import json
from typing import Optional, Dict, Any

class AuthManager:
    """Authentication manager for Streamlit frontend"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url.rstrip('/')
        
    def set_auth_token(self, token: str):
        """Store auth token in session state"""
        st.session_state.auth_token = token
        
    def get_auth_token(self) -> Optional[str]:
        """Get auth token from session state"""
        return st.session_state.get('auth_token')
        
    def clear_auth_token(self):
        """Clear auth token and user info"""
        keys_to_clear = ['auth_token', 'user_info', 'current_org']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
                
    def get_headers(self) -> Dict[str, str]:
        """Get headers with auth token"""
        token = self.get_auth_token()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
        
    def check_auth(self) -> Optional[Dict[str, Any]]:
        """Check if user is authenticated and get user info"""
        token = self.get_auth_token()
        if not token:
            return None
            
        try:
            response = requests.get(
                f"{self.api_base_url}/api/v1/horses/organizations/current",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                user_info = response.json()
                st.session_state.user_info = user_info
                return user_info
            elif response.status_code == 401:
                # Token is invalid
                self.clear_auth_token()
                return None
            else:
                st.error(f"Authentication check failed: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            st.error(f"Failed to connect to API: {e}")
            return None
        
    def api_request(self, method: str, endpoint: str, **kwargs) -> 
requests.Response:
        """Make authenticated API request"""
        headers = self.get_headers()
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"
        return requests.request(method, url, timeout=30, **kwargs)

# Global auth manager instance
auth = AuthManager()

def show_login_page():
    """Show login page for development authentication"""
    
    st.title("🐴 Barn Lady - Multi-Barn Horse Management")
    st.markdown("---")
    
    # Check if PropelAuth is configured by testing the API
    try:
        response = requests.get(f"{auth.api_base_url}/health", timeout=5)
        api_available = response.status_code == 200
    except:
        api_available = False
    
    if not api_available:
        st.error("❌ Cannot connect to Barn Lady API. Please ensure the backend is 
running.")
        st.code("docker-compose up -d")
        return
    
    st.success("✅ Connected to Barn Lady API")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔐 Development Login")
        st.info("""
        **For Development & Testing**
        
        Enter your PropelAuth JWT token to access your barns.
        """)
        
        with st.form("login_form"):
            token_input = st.text_area(
                "JWT Token:",
                height=100,
                placeholder="Paste your PropelAuth JWT token here...",
                help="Get this from your PropelAuth dashboard"
            )
            
            submitted = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submitted and token_input:
                auth.set_auth_token(token_input.strip())
                user_info = auth.check_auth()
                
                if user_info:
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid token. Please check your token and try 
again.")
    
    with col2:
        st.subheader("📋 How to Get Your Token")
        st.markdown("""
        **Step 1:** Go to your PropelAuth dashboard
        - URL: `https://34521247761.propelauthtest.com`
        
        **Step 2:** Create or login as a test user
        
        **Step 3:** Create an organization (barn)
        
        **Step 4:** Generate a JWT token for testing
        
        **Step 5:** Copy and paste the token above
        """)
        
        st.markdown("---")
        
        st.subheader("🌟 What You'll Get")
        st.markdown("""
        ✅ **Multi-Barn Management** - Switch between different barns
        
        ✅ **Secure Horse Data** - Each barn sees only their horses
        
        ✅ **AI-Powered Insights** - Claude understands your barn context
        
        ✅ **Team Collaboration** - Multiple users per barn
        
        ✅ **Professional Features** - Search, sort, manage horses
        """)

def show_organization_selector():
    """Show organization selector in sidebar"""
    user_info = st.session_state.get('user_info', {})
    organizations = user_info.get('all_organizations', [])
    current_org_id = user_info.get('current_org_id')
    
    if not organizations:
        st.sidebar.error("No organizations found")
        return
    
    st.sidebar.markdown("### 🏢 Your Barns")
    
    if len(organizations) > 1:
        # Multiple organizations - show selector
        org_options = {}
        for org in organizations:
            org_options[org['org_name']] = org['org_id']
            
        # Find current selection
        current_selection = None
        for name, org_id in org_options.items():
            if org_id == current_org_id:
                current_selection = name
                break
                
        if current_selection not in org_options:
            current_selection = list(org_options.keys())[0]
            
        selected_org_name = st.sidebar.selectbox(
            "Select barn:",
            options=list(org_options.keys()),
            index=list(org_options.keys()).index(current_selection) if 
current_selection in org_options else 0,
            key="org_selector"
        )
        
        selected_org_id = org_options[selected_org_name]
        
        # Switch organization if changed
        if selected_org_id != current_org_id:
            try:
                response = auth.api_request(
                    'POST', 
                    f'/api/v1/horses/organizations/{selected_org_id}/select'
                )
                
                if response.status_code == 200:
                    # Update user info in session
                    updated_info = auth.check_auth()
                    if updated_info:
                        st.sidebar.success(f"Switched to {selected_org_name}")
                        st.rerun()
                else:
                    st.sidebar.error("Failed to switch organization")
                    
            except requests.RequestException:
                st.sidebar.error("Failed to switch organization")
    
    else:
        # Single organization
        org = organizations[0]
        st.sidebar.markdown(f"**{org['org_name']}**")
        st.sidebar.caption(f"Role: {org.get('role', 'Member')}")

def show_user_menu():
    """Show user menu in sidebar"""
    user_info = st.session_state.get('user_info', {})
    current_org = user_info.get('current_org', {})
    
    st.sidebar.markdown("---")
    
    # Current organization info
    if current_org:
        st.sidebar.markdown(f"**📍 Current Barn:** {current_org.get('org_name', 
'Unknown')}")
        st.sidebar.caption(f"Role: {current_org.get('role', 'Member')}")
    
    st.sidebar.markdown("---")
    
    # User info
    email = user_info.get('current_org', {}).get('email', 'Unknown User')
    st.sidebar.markdown(f"**👤 Logged in**")
    st.sidebar.caption(f"User ID: {user_info.get('current_org_id', 
'Unknown')[:8]}...")
    
    # Logout button
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        auth.clear_auth_token()
        st.rerun()

def require_auth():
    """Decorator/function to require authentication"""
    user_info = auth.check_auth()
    
    if not user_info:
        show_login_page()
        return False
    
    # Show organization selector and user menu
    show_organization_selector()
    show_user_menu()
    
    return True

def get_auth_headers() -> Dict[str, str]:
    """Get headers for API requests"""
    return auth.get_headers()

def make_api_request(method: str, endpoint: str, **kwargs) -> requests.Response:
    """Make an authenticated API request"""
    return auth.api_request(method, endpoint, **kwargs)

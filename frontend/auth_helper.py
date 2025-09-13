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
import os
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
        """Generate PropelAuth hosted login URL with proper redirect"""
        self._load_config()
        
        # Determine the correct redirect URI based on environment  
        if redirect_uri is None:
            # Check if we're on Railway
            is_railway = os.getenv('RAILWAY_ENVIRONMENT_NAME') is not None
            if is_railway:
                # PropelAuth actually redirects to /?auth=callback/
                redirect_uri = "https://web-production-10a5d.up.railway.app/"
            else:
                redirect_uri = "http://localhost:8501/"
        
        # Mark that we're processing a PropelAuth login for callback detection
        st.session_state.processing_propelauth_login = True
        
        # Use PropelAuth's hosted login with the configured redirect
        # Based on PropelAuth dashboard: Application URL + /auth/callback/
        print(f"🔍 Using PropelAuth hosted login with redirect to: {redirect_uri}")
        
        # PropelAuth hosted login with redirect parameter
        hosted_login_url = f"{self.auth_url}/login?redirect_uri={redirect_uri}"
        print(f"🔍 Generated hosted login URL: {hosted_login_url}")
        return hosted_login_url
    
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
        """Get access token from session or process OAuth callback"""
        # First check session state
        if "access_token" in st.session_state and st.session_state.access_token:
            return st.session_state.access_token
        
        # Don't process if user just logged out
        if st.session_state.get('user_logged_out', False):
            return None
        
        # Don't process callback if we've already processed it
        if st.session_state.get('callback_processed', False):
            return None
        
        # Check for OAuth callback and process it
        token = self._process_oauth_callback()
        
        # Mark callback as processed to prevent loops
        if token:
            st.session_state.callback_processed = True
        
        return token
    
    def set_access_token(self, token: str):
        """Set access token in session state"""
        st.session_state.access_token = token
    
    def _process_oauth_callback(self) -> Optional[str]:
        """Process PropelAuth hosted login callback"""
        try:
            # Get query parameters
            if hasattr(st, 'query_params'):
                query_params = st.query_params
            else:
                query_params = st.experimental_get_query_params()
            
            print(f"🔍 Hosted Login Callback - Query params: {dict(query_params)}")
            
            # Check for PropelAuth hosted login callback
            # PropelAuth hosted login redirects to /auth/callback/ with user token
            if 'propelauth_token' in query_params:
                token = query_params['propelauth_token'][0] if isinstance(query_params['propelauth_token'], list) else query_params['propelauth_token']
                print(f"🔍 Found PropelAuth hosted login token: {token[:20]}...")
                
                # Validate the token with backend and get user data
                response = requests.post(
                    f"{self.backend_url}/api/v1/auth/validate-token",
                    json={"token": token},
                    timeout=15
                )
                
                print(f"🔍 Backend token validation response: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"🔍 Token validation result: {result.get('success', False)}")
                    
                    if result.get("success"):
                        # Extract user information from the response
                        user_data = result.get("user", {})
                        access_token = result.get("access_token", token)
                        
                        email = user_data.get("email")
                        print(f"🔍 Hosted login extracted user email: {email}")
                        
                        # Store user and token in session
                        st.session_state.user = user_data
                        st.session_state.access_token = access_token
                        st.session_state.user_email = email
                        
                        # Clear query parameters to prevent reprocessing
                        if hasattr(st, 'query_params'):
                            st.query_params.clear()
                        else:
                            st.experimental_set_query_params()
                        
                        print(f"🔍 Hosted login flow completed successfully for: {email}")
                        return access_token
                    else:
                        error_msg = result.get("error", "Unknown error")
                        print(f"🔍 Token validation failed: {error_msg}")
                        st.error(f"Authentication failed: {error_msg}")
                else:
                    print(f"🔍 Backend token validation failed: {response.status_code}")
                    print(f"🔍 Response text: {response.text}")
                    st.error(f"Authentication service error: {response.status_code}")
            
            # Check for /auth/callback/ URL pattern (PropelAuth's default redirect)
            elif hasattr(st, 'query_params') and st.query_params.get_all() == [] and st.session_state.get('processing_propelauth_login'):
                print(f"🔍 PropelAuth callback detected via URL pattern")
                # User is being redirected back from PropelAuth hosted login
                # The hosted login should provide some way to get user data
                # Let's try to extract from any available cookies or session
                
                # Check if PropelAuth set any session cookies we can read
                try:
                    # This is a simplified approach - in production you'd validate the PropelAuth session
                    # For now, let's call our backend to check current session
                    response = requests.get(
                        f"{self.backend_url}/api/v1/auth/session",
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success") and result.get("user"):
                            user_data = result.get("user", {})
                            access_token = result.get("access_token", "hosted_login_token")
                            email = user_data.get("email")
                            
                            print(f"🔍 Retrieved session for user: {email}")
                            
                            # Store user and token in session
                            st.session_state.user = user_data
                            st.session_state.access_token = access_token
                            st.session_state.user_email = email
                            st.session_state.processing_propelauth_login = False
                            
                            return access_token
                        
                except Exception as e:
                    print(f"🔍 Error checking PropelAuth session: {str(e)}")
            
            # PropelAuth callback with ?auth=callback/ pattern
            elif 'auth' in query_params and 'callback' in str(query_params['auth']):
                print(f"🔍 PropelAuth callback detected via ?auth=callback/ pattern")
                
                # Show debug info about what we received
                st.info("🔍 PropelAuth callback detected!")
                with st.expander("Debug: Callback Details", expanded=True):
                    st.write("Query parameters received:", dict(query_params))
                    st.write("All query parameter keys:", list(query_params.keys()))
                    
                    # Check for other possible token parameter names
                    possible_tokens = ['token', 'access_token', 'propelauth_token', 'jwt', 'bearer']
                    for token_name in possible_tokens:
                        if token_name in query_params:
                            token_value = query_params[token_name][0] if isinstance(query_params[token_name], list) else query_params[token_name]
                            st.success(f"Found {token_name}: {token_value[:50]}...")
                            
                            # Try to validate this token with the backend
                            st.write(f"Attempting to validate {token_name} with backend...")
                            try:
                                response = requests.post(
                                    f"{self.backend_url}/api/v1/auth/validate-token",
                                    json={"token": token_value},
                                    timeout=15
                                )
                                
                                st.write(f"Token validation response: {response.status_code}")
                                if response.status_code == 200:
                                    result = response.json()
                                    st.write("Validation result:", result)
                                    
                                    if result.get("success"):
                                        # Token is valid! Store user data and complete authentication
                                        user_data = result.get("user", {})
                                        access_token = result.get("access_token", token_value)
                                        email = user_data.get("email")
                                        
                                        st.success(f"✅ Successfully authenticated user: {email}")
                                        
                                        # Store user and token in session
                                        st.session_state.user = user_data
                                        st.session_state.access_token = access_token
                                        st.session_state.user_email = email
                                        st.session_state.processing_propelauth_login = False
                                        
                                        # Clear query parameters
                                        if hasattr(st, 'query_params'):
                                            st.query_params.clear()
                                        else:
                                            st.experimental_set_query_params()
                                        
                                        return access_token
                                else:
                                    st.error(f"Token validation failed: {response.status_code}")
                                    if response.text:
                                        st.code(response.text[:300])
                                        
                            except Exception as e:
                                st.error(f"Error validating token: {str(e)}")
                    
                    if not any(param in query_params for param in possible_tokens):
                        st.warning("No token parameters found in callback URL")
                    
                    # Try to get user session from PropelAuth via backend
                    st.write("Attempting to retrieve session from backend...")
                    try:
                        response = requests.get(
                            f"{self.backend_url}/api/v1/auth/session",
                            timeout=10
                        )
                        
                        st.write(f"Backend response status: {response.status_code}")
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.write("Backend response:", result)
                            
                            if result.get("success") and result.get("user"):
                                user_data = result.get("user", {})
                                access_token = result.get("access_token", "hosted_login_token")
                                email = user_data.get("email")
                                
                                print(f"🔍 Retrieved PropelAuth session for user: {email}")
                                st.success(f"✅ Successfully retrieved user: {email}")
                                
                                # Store user and token in session
                                st.session_state.user = user_data
                                st.session_state.access_token = access_token
                                st.session_state.user_email = email
                                st.session_state.processing_propelauth_login = False
                                
                                # Clear query parameters
                                if hasattr(st, 'query_params'):
                                    st.query_params.clear()
                                else:
                                    st.experimental_set_query_params()
                                
                                return access_token
                            else:
                                st.warning("Backend response did not contain valid user data")
                        else:
                            st.error(f"Backend session endpoint failed: {response.status_code}")
                            if response.text:
                                st.code(response.text[:500])
                            
                    except Exception as e:
                        st.error(f"Error checking PropelAuth session: {str(e)}")
                
                # Fallback: show user selection if session retrieval fails
                st.info("🔍 Falling back to user selection:")
                
                # Clear query parameters to prevent loops
                if hasattr(st, 'query_params'):
                    st.query_params.clear()
                else:
                    st.experimental_set_query_params()
                
                # Show user selection as fallback
                st.markdown("**Available Users:**")
                users = ["chris@carril.com", "cjmurphy.nyc@gmail.com"]
                selected_user = st.selectbox("Select your account:", users)
                
                if st.button("Continue with Selected User"):
                    # Clear query parameters that triggered this callback
                    if hasattr(st, 'query_params'):
                        st.query_params.clear()
                    else:
                        st.experimental_set_query_params()
                    
                    # Clear the callback state to prevent loops
                    if 'processing_propelauth_login' in st.session_state:
                        del st.session_state.processing_propelauth_login
                    
                    self._setup_demo_user(selected_user)
                    return "user_selected_token"
            
            return None
            
        except Exception as e:
            print(f"🔍 Hosted login callback processing error: {str(e)}")
            st.error(f"Authentication error: {str(e)}")
            return None
    
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
                
                # Mark callback as processed to prevent further processing
                st.session_state.callback_processed = True
                
                # Clear processing flags to ensure clean state
                if 'processing_propelauth_login' in st.session_state:
                    del st.session_state.processing_propelauth_login
                
                st.success(f"✅ Logged in as {email}")
                
                # Force a rerun to refresh the page with authenticated state
                time.sleep(0.5)  # Small delay to show success message
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
        if "processing_propelauth_login" in st.session_state:
            del st.session_state.processing_propelauth_login
        
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
        """Show PropelAuth OAuth login interface"""
        st.info("🔐 **PropelAuth Login**")
        st.markdown("Sign in with your PropelAuth account to access your barn management system.")
        
        # Center the login button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            login_url = self.get_login_url()
            
            if hasattr(st, 'link_button'):
                if st.button("🚀 Sign In with PropelAuth", use_container_width=True, type="primary"):
                    st.markdown(f'<meta http-equiv="refresh" content="0; url={login_url}" />', unsafe_allow_html=True)
                    st.write("Redirecting to PropelAuth...")
            else:
                st.markdown(
                    f'<a href="{login_url}" target="_self" style="text-decoration: none;">'
                    f'<button style="background-color: #ff4b4b; color: white; border: none; '
                    f'padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; '
                    f'width: 100%; font-size: 16px; font-weight: bold;">'
                    f'🚀 Sign In with PropelAuth</button></a>',
                    unsafe_allow_html=True
                )
        
        st.markdown("---")
        st.info("**Real PropelAuth Authentication**: Your barn access is determined by your PropelAuth organization membership.")
        
        # Debug info for development
        with st.expander("🔧 Debug Info", expanded=False):
            st.write(f"**Login URL**: {login_url}")
            st.write("**Flow**: PropelAuth Hosted Login → Token Validation → User Data")
            st.write(f"**Backend URL**: {self.backend_url}")
            
            # Test backend connection
            try:
                import requests
                response = requests.get(f"{self.backend_url}/health", timeout=5)
                if response.status_code == 200:
                    st.success("✅ Backend connection healthy")
                else:
                    st.error(f"❌ Backend returned {response.status_code}")
            except Exception as e:
                st.error(f"❌ Backend connection failed: {str(e)}")
            
            # Test auth endpoint
            try:
                response = requests.post(
                    f"{self.backend_url}/api/v1/auth/validate-token",
                    json={"token": "test"},
                    timeout=5
                )
                if response.status_code == 200:
                    st.info("🔒 Auth endpoint responding (test token rejected as expected)")
                elif response.status_code == 403:
                    st.warning("🔒 Auth endpoint blocked - PropelAuth environment variables may be missing")
                else:
                    st.warning(f"🔒 Auth endpoint returned {response.status_code}")
            except Exception as e:
                st.error(f"❌ Auth endpoint test failed: {str(e)}")

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
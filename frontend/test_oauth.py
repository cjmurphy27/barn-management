"""
Simple test of Streamlit native OAuth with PropelAuth
"""
import streamlit as st

st.set_page_config(page_title="OAuth Test", page_icon="🔐")

st.title("🔐 PropelAuth OAuth Test")

# Show authentication status
if hasattr(st, 'user') and st.user.is_logged_in:
    st.success("✅ You are logged in!")
    
    # Display user information
    st.subheader("User Information:")
    user_info = {
        "Logged In": st.user.is_logged_in,
        "Email": getattr(st.user, 'email', 'Not available'),
        "First Name": getattr(st.user, 'given_name', 'Not available'),
        "Last Name": getattr(st.user, 'family_name', 'Not available'),
        "User ID": getattr(st.user, 'sub', 'Not available'),
    }
    
    for key, value in user_info.items():
        st.write(f"**{key}:** {value}")
    
    # Show all available user attributes
    with st.expander("🔍 All User Attributes"):
        st.write("Available attributes on st.user:")
        for attr in dir(st.user):
            if not attr.startswith('_'):
                try:
                    value = getattr(st.user, attr)
                    st.write(f"**{attr}:** {value}")
                except:
                    st.write(f"**{attr}:** (could not access)")
    
    # Logout button
    if st.button("🚪 Logout", type="secondary"):
        st.logout()
        st.rerun()

else:
    st.info("🔒 You are not logged in")
    
    st.write("**OAuth Configuration Status:**")
    st.write(f"- Redirect URI: `{st.secrets['auth']['redirect_uri']}`")
    st.write(f"- Server Metadata URL: `{st.secrets['auth']['server_metadata_url']}`")
    st.write(f"- Client ID: `{st.secrets['auth']['client_id'][:8]}...`")
    
    if st.button("🔑 Login with PropelAuth", type="primary"):
        st.login()

st.markdown("---")
st.markdown("**Testing Streamlit 1.49.1 native OAuth with PropelAuth**")
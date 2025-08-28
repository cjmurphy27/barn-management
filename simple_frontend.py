import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="🐴 Barn Lady", page_icon="🐴")

st.title("🐴 Barn Lady - Simple Version")
st.markdown("### Just Testing That Everything Works")

# Show current time to prove it's live
st.info(f"⏰ Current time: {datetime.now().strftime('%H:%M:%S')}")

# Test API connection
st.markdown("---")
st.markdown("## 🔌 API Connection Test")

try:
    response = requests.get("http://localhost:8000/", timeout=3)
    if response.status_code == 200:
        st.success("✅ API is working!")
        data = response.json()
        st.json(data)
        
        # Test another endpoint
        test_response = requests.get("http://localhost:8000/test", timeout=3)
        if test_response.status_code == 200:
            st.success("✅ API test endpoint working!")
            st.json(test_response.json())
            
    else:
        st.error(f"❌ API returned status {response.status_code}")
        
except requests.exceptions.ConnectionError:
    st.error("❌ Cannot connect to API")
    st.markdown("**The API might not be running**")
    
except Exception as e:
    st.error(f"❌ Error: {str(e)}")

# Simple interactive elements
st.markdown("---")
st.markdown("## 🧪 Interactive Test")

if st.button("🔄 Refresh Page"):
    st.rerun()

name = st.text_input("Enter a horse name:", placeholder="Thunder")
if name:
    st.success(f"🐎 Hello {name}!")

# Show this is working
st.markdown("---")
st.success("✅ If you can see this page, your Streamlit frontend is working!")
st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

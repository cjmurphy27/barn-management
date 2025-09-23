import streamlit as st

# Configure page - MUST be first Streamlit command
st.set_page_config(
    page_title="Stable Genius - Horse Management",
    page_icon="🏇",  # Use emoji instead of problematic file path
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import requests
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List
import json
from auth_helper import auth
from whiteboard import show_whiteboard_page

# Custom CSS for button styling and to hide automatic navigation
st.markdown("""
<style>
/* CSS Version 3.1 - Clean sidebar with beige background and better navigation */

/* Modern clean white sidebar with subtle border */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E5E7EB !important;
}

section[data-testid="stSidebar"] > div {
    background-color: #FFFFFF !important;
}

/* Clean styling for sidebar text */
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #000000 !important;
}

/* Style the selectbox dropdowns consistently */
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: white !important;
    border: 1px solid #4A90E2 !important;
    border-radius: 8px !important;
}

/* Style info boxes and alerts in sidebar */
section[data-testid="stSidebar"] .stAlert {
    background-color: rgba(74, 144, 226, 0.1) !important;
    border: 1px solid #4A90E2 !important;
    border-radius: 8px !important;
    color: #0052a4 !important;
}

/* Style buttons in sidebar - FORCE logout button to be orange */
section[data-testid="stSidebar"] .stButton > button,
section[data-testid="stSidebar"] button,
section[data-testid="stSidebar"] button[kind="secondary"],
section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"],
section[data-testid="stSidebar"] div[data-testid="stButton"] button,
section[data-testid="stSidebar"] div[data-baseweb="button"] {
    background-color: #D2691E !important;
    background: #D2691E !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
}

section[data-testid="stSidebar"] .stButton > button:hover,
section[data-testid="stSidebar"] button:hover,
section[data-testid="stSidebar"] button[kind="secondary"]:hover,
section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover,
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover,
section[data-testid="stSidebar"] div[data-baseweb="button"]:hover {
    background-color: #CD853F !important;
    background: #CD853F !important;
    color: white !important;
}

/* Remove unnecessary horizontal lines */
section[data-testid="stSidebar"] hr {
    display: none !important;
}

/* Primary buttons - all variations */
div.stButton > button[data-testid="baseButton-primary"],
div.stButton > button[kind="primary"],
.stButton button[data-baseweb="button"][kind="primary"],
button[data-testid="baseButton-primary"] {
    background-color: #8BB6CC !important;
    background: #8BB6CC !important;
    border: none !important;
    color: #1A3A52 !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    min-height: 2.5rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Primary button hover states */
div.stButton > button[data-testid="baseButton-primary"]:hover,
div.stButton > button[kind="primary"]:hover,
.stButton button[data-baseweb="button"][kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover {
    background-color: #4A6B82 !important;
    background: #4A6B82 !important;
    color: white !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    transform: translateY(-1px) !important;
}

/* Secondary buttons */
div.stButton > button[data-testid="baseButton-secondary"],
div.stButton > button[kind="secondary"],
.stButton button[data-baseweb="button"][kind="secondary"],
button[data-testid="baseButton-secondary"] {
    background-color: transparent !important;
    background: transparent !important;
    border: 2px solid #8BB6CC !important;
    color: #8BB6CC !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
}

/* Secondary button hover */
div.stButton > button[data-testid="baseButton-secondary"]:hover,
div.stButton > button[kind="secondary"]:hover,
.stButton button[data-baseweb="button"][kind="secondary"]:hover,
button[data-testid="baseButton-secondary"]:hover {
    background-color: #8BB6CC !important;
    background: #8BB6CC !important;
    color: #1A3A52 !important;
    border-color: #8BB6CC !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    transform: translateY(-1px) !important;
}

/* Regular buttons (no type specified) */
div.stButton > button:not([data-testid*="primary"]):not([data-testid*="secondary"]),
.stButton button:not([kind]),
button[data-testid="baseButton-minimal"] {
    background-color: #8BB6CC !important;
    background: #8BB6CC !important;
    border: none !important;
    color: #1A3A52 !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    min-height: 2.5rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Regular button hover */
div.stButton > button:not([data-testid*="primary"]):not([data-testid*="secondary"]):hover,
.stButton button:not([kind]):hover,
button[data-testid="baseButton-minimal"]:hover {
    background-color: #8BB6CC !important;
    background: #8BB6CC !important;
    color: white !important;
    border-color: #4A6B82 !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.15) !important;
    transform: translateY(-1px) !important;
}

/* Form submit buttons */
.stForm .stButton > button,
form button[type="submit"] {
    background-color: #8BB6CC !important;
    background: #8BB6CC !important;
    border: none !important;
    color: #1A3A52 !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}

.stForm .stButton > button:hover,
form button[type="submit"]:hover {
    background-color: #4A6B82 !important;
    background: #4A6B82 !important;
    color: white !important;
}

/* Catch-all for any remaining buttons - AGGRESSIVE OVERRIDE */
button,
[data-testid*="button"],
[class*="button"],
.stButton button,
div.stButton button,
*[role="button"] {
    background-color: #8BB6CC !important;
    background: #8BB6CC !important;
    background-image: none !important;
    background-color: #8BB6CC !important;
    border: 2px solid #8BB6CC !important;
    color: #1A3A52 !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    min-height: 2.5rem !important;
    white-space: nowrap !important;
}

/* Extra aggressive background override for default state */
button:not(:hover):not(:active):not(:focus),
.stButton button:not(:hover):not(:active):not(:focus),
[data-testid*="button"]:not(:hover):not(:active):not(:focus) {
    background-color: #8BB6CC !important;
    background: #8BB6CC !important;
    background-image: none !important;
    border: 2px solid #8BB6CC !important;
    border-color: #8BB6CC !important;
    color: #1A3A52 !important;
}

/* Remove any pseudo-elements that might override background */
button::before,
button::after,
.stButton button::before,
.stButton button::after {
    display: none !important;
}

button:hover,
[data-testid*="button"]:hover,
[class*="button"]:hover,
.stButton button:hover,
div.stButton button:hover,
*[role="button"]:hover {
    background-color: #4A6B82 !important;
    background: #4A6B82 !important;
    background-image: none !important;
    border: 2px solid #4A6B82 !important;
    border-color: #4A6B82 !important;
    color: white !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
}

/* Target only emoji characters for health status - more specific approach */
/* This CSS uses a different method - targeting the actual emoji unicode ranges */

/* Health status emojis - using CSS to target emoji characters specifically */
.health-emoji {
    font-size: 0.7rem !important;
    display: inline-block !important;
    vertical-align: middle !important;
}
</style>
""", unsafe_allow_html=True)

# API Configuration
# For Railway deployment, use localhost since both frontend and backend run in same container
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8002")

# Helper Functions
def api_request(method: str, endpoint: str, data: dict = None) -> dict:
    """Make API request with error handling and authentication"""
    url = f"{API_BASE_URL}{endpoint}"
    
    # Get authentication token
    token = auth.get_access_token()
    headers = {}
    
    # Add authorization header if we have a real token (not demo token)
    if token and token != "demo_token_from_callback":
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=data, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        
        response.raise_for_status()
        return response.json() if response.content else {}
    
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {}

def api_request_with_conflict_handling(method: str, endpoint: str, data: dict = None) -> dict:
    """Make API request that handles 409 conflicts gracefully for inventory operations"""
    url = f"{API_BASE_URL}{endpoint}"
    
    # Get authentication token
    token = auth.get_access_token()
    headers = {}
    
    # Add authorization header if we have a real token (not demo token)
    if token and token != "demo_token_from_callback":
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=data, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        
        response.raise_for_status()
        return response.json() if response.content else {}
    
    except requests.exceptions.HTTPError as e:
        # Handle 409 conflicts silently (item already exists)
        if e.response.status_code == 409:
            return None  # Signal that item already exists
        else:
            st.error(f"API Error: {str(e)}")
            return {}
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {}

def format_date(date_obj) -> str:
    """Format date for display"""
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00')).date()
        except:
            return date_obj
    
    if date_obj:
        return date_obj.strftime("%B %d, %Y")
    return "Not specified"

def show_authenticated_app():
    """Show the full application for authenticated users"""
    
    # Custom CSS for Modern Professional Theme
    st.markdown("""
    <style>
    /* Modern color scheme: Navy Blue (#0052a4), Light Blue (#4A90E2), Clean White (#FFFFFF), Light Gray (#F8F9FA) */

    /* Main app styling */
    .main > div {
        background-color: #FFFFFF;
    }

    /* App background */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Primary buttons - Barn Lady Orange */
    .stButton > button[kind="primary"] {
        background-color: #D2691E !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #CD853F !important;
        color: white !important;
    }
    
    /* Secondary buttons - Sage Green */
    .stButton > button:not([kind="primary"]) {
        background-color: #A5B68D !important;
        color: #000000 !important;
        border: 1px solid #8FA876 !important;
        border-radius: 8px !important;
    }
    
    .stButton > button:not([kind="primary"]):hover {
        background-color: #8FA876 !important;
        color: #000000 !important;
    }
    
    /* Sidebar styling - slightly darker cream */
    .css-1d391kg, .css-k1vhr4, [data-testid="stSidebar"] > div {
        background-color: #F0EDE5 !important;
    }
    
    /* Sidebar content */
    .css-1d391kg .stSelectbox, .css-1d391kg .stButton {
        background-color: #F0EDE5 !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #000000 !important;
    }
    
    /* Cards and containers - Warm off-white */
    .stMarkdown > div > div {
        background-color: #FEFCF8;
        border-left: 4px solid #D2691E;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    
    /* Modern alert styling */
    .stAlert > div {
        background-color: #f8f9fa !important;
        border: none !important;
        border-left: 4px solid #4A90E2 !important;
        border-radius: 8px !important;
        color: #000000 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        padding: 16px 20px !important;
    }

    /* Success alerts */
    .stAlert[data-baseweb="notification"][kind="success"] > div {
        border-left-color: #28a745 !important;
        background-color: #f8fff9 !important;
    }

    /* Warning alerts */
    .stAlert[data-baseweb="notification"][kind="warning"] > div {
        border-left-color: #ffc107 !important;
        background-color: #fffef8 !important;
    }

    /* Error alerts */
    .stAlert[data-baseweb="notification"][kind="error"] > div {
        border-left-color: #dc3545 !important;
        background-color: #fff8f8 !important;
    }

    /* Info alerts */
    .stAlert[data-baseweb="notification"][kind="info"] > div {
        border-left-color: #4A90E2 !important;
        background-color: #f8f9fa !important;
    }
    
    /* Form styling */
    .stTextInput, .stSelectbox, .stDateInput, .stTextArea {
        background-color: #FEFCF8;
    }
    
    /* Metric styling */
    [data-testid*="button"],
    .js-plotly-plot {
        background-color: #FEFCF8 !important;
        border-radius: 8px !important;
        border: 1px solid #A5B68D !important;
    }
    
    /* Remove focus outlines on buttons to prevent blue highlights */
    [data-testid*="button"]:not(:hover):not(:active):not(:focus) {
        outline: none !important;
        border: 1px solid #A5B68D !important;
    }
    
    /* File uploader */
    .uploadedFile {
        background-color: #FEFCF8 !important;
        border: 1px solid #A5B68D !important;
    }
    
    /* Focus states */
    [data-testid*="button"]:hover,
    .stTextInput:hover,
    .stSelectbox:hover {
        border-color: #D2691E !important;
        box-shadow: 0 0 0 1px #D2691E !important;
    }
    
    /* Progress bars */
    .stProgress {
        background-color: #A5B68D !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display logo and tagline
    col1, col2 = st.columns([1, 4])
    with col1:
        # Try different path approaches for the logo
        import os
        logo_paths = [
            "assets/barn_lady_logo.png",
            "./assets/barn_lady_logo.png", 
            "frontend/assets/barn_lady_logo.png",
            os.path.join(os.path.dirname(__file__), "assets", "barn_lady_logo.png")
        ]
        
        logo_displayed = False
        for logo_path in logo_paths:
            try:
                if os.path.exists(logo_path):
                    st.image(logo_path, width=180)
                    logo_displayed = True
                    break
            except:
                continue
                
        if not logo_displayed:
            # Fallback to emoji if logo not found
            st.markdown("<div style='font-size: 50px; text-align: center; margin-right: 20px;'>🏇</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add space above tagline
        st.markdown("<h2 style='margin-bottom: 0px; margin-left: 40px; padding-top: 15px;'>Intelligent Barn Management System</h2>", unsafe_allow_html=True)
        st.markdown("---")
    
    # Page Navigation - Always visible and consistent
    with st.sidebar:
        st.markdown("**Navigate to:**")
        
        # Initialize current page
        current_page = "Horse Directory"
        
        # Check for AI navigation from query params
        try:
            query_params = st.experimental_get_query_params()
            if "page" in query_params and query_params["page"][0] == "ai":
                current_page = "🤖 AI Assistant"
                # Clear the query params after using them
                st.experimental_set_query_params()
        except:
            pass
        
        # Check for force AI page navigation
        if st.session_state.get('force_ai_page', False):
            current_page = "🤖 AI Assistant"
            # Clear the flag after using it
            del st.session_state['force_ai_page']
        # Check if we have an active AI context (should stay on AI Assistant page)
        elif 'ai_horse_id' in st.session_state and st.session_state.ai_horse_id:
            current_page = "🤖 AI Assistant"
        # Check if we're in a specific horse context to determine current page
        elif 'selected_horse_id' in st.session_state and st.session_state.selected_horse_id:
            if 'edit_mode' in st.session_state and st.session_state.edit_mode:
                current_page = "Edit Horse"
            else:
                current_page = "Horse Profile"
        
        # Always show the same navigation options
        all_pages = ["Horse Directory", "Add New Horse", "📋 Message Board", "📅 Calendar", "📦 Supplies", "🤖 AI Assistant", "Reports"]
        
        # Add horse-specific pages when viewing a horse
        if 'selected_horse_id' in st.session_state and st.session_state.selected_horse_id:
            all_pages = ["Horse Profile", "Edit Horse"] + ["—————————————"] + all_pages
        
        # Set default selection
        try:
            default_index = all_pages.index(current_page)
        except ValueError:
            default_index = 0
            
        page = st.selectbox(
            "Navigate to:",
            all_pages,
            index=default_index,
            label_visibility="collapsed"
        )
    
    # Clear horse context when navigating away from horse pages
    if page == "Horse Directory" and 'selected_horse_id' in st.session_state:
        # Clear horse selection when explicitly navigating to Horse Directory
        del st.session_state['selected_horse_id']
        if 'selected_horse_name' in st.session_state:
            del st.session_state['selected_horse_name']
        if 'edit_mode' in st.session_state:
            del st.session_state['edit_mode']
        st.rerun()
    
    
    # Route to appropriate page
    if page == "Horse Directory":
        show_horse_directory()
    elif page == "Add New Horse":
        show_add_horse_form()
    elif page == "📋 Message Board":
        show_whiteboard()
    elif page == "📅 Calendar":
        show_calendar()
    elif page == "📦 Supplies":
        show_supplies()
    elif page == "Horse Profile":
        show_horse_profile()
    elif page == "Edit Horse":
        show_edit_horse_form()
    elif page == "🤖 AI Assistant":
        show_ai_assistant()
    elif page == "Reports":
        show_reports()

# Main App
def main():
    # Authentication Check - using auth_helper
    user = auth.get_current_user()
    token = auth.get_access_token()
    
    # Check if callback was detected by auth_helper
    auth_callback = st.session_state.get('auth_callback_detected', False)
    
    # Use authenticated user only
    active_user = user
    
    if active_user:
        # User is authenticated - show full multi-barn functionality
        email = active_user.get('email', 'User')
        
        
        # Get barns from authenticated user
        barns = auth.get_user_barns()
        
        # Show user info and barn selector in sidebar for clean layout
        auth.show_auth_sidebar()
        
        # USER IS AUTHENTICATED - SHOW FULL APPLICATION
        show_authenticated_app()
        
    else:
        # User not authenticated - show simplified login interface
        auth.show_login_interface()
        
        st.markdown("---")
        st.markdown("**Need an account?** Contact your barn administrator to get access.")
        st.markdown("**New barn setup?** Contact us to set up your barn management system.")
        st.stop()  # Stop execution here - don't load the rest of the app

def show_horse_directory():
    """Display list of all horses with search and filtering"""
    st.subheader("Horse Directory")
    
    # Upcoming Events Dashboard Widget
    with st.expander("📅 Upcoming Events (Next 7 Days)", expanded=False):
        # Get upcoming events with organization filter
        upcoming_params = {"days_ahead": 7, "limit": 5}
        if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
            upcoming_params["organization_id"] = st.session_state.selected_barn_id
        
        upcoming = api_request("GET", "/api/v1/calendar/upcoming", upcoming_params)
        
        if upcoming and "upcoming_events" in upcoming and upcoming["upcoming_events"]:
            for event in upcoming["upcoming_events"]:
                type_icons = {
                    "veterinary": "🏥", "farrier": "🔨", "dental": "🦷",
                    "supply_delivery": "🚛", "training": "⭐", "other": "📅"
                }
                icon = type_icons.get(event["event_type"], "📅")
                event_dt = datetime.fromisoformat(event['scheduled_date'])
                horse_info = f"🐴 {event['horse_name']}" if event.get('horse_name') else ""

                # Build HTML parts conditionally
                horse_html = f'<p style="margin: 0; color: #666; font-size: 0.9em;">{horse_info}</p>' if horse_info else ''

                st.markdown(f"""
                <div style="border: none; border-radius: 12px; padding: 20px; margin: 10px 0; background-color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08); display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0 0 5px 0; font-size: 1.1em; font-weight: bold; color: #000000;">{icon} {event['title']}</h4>
                        {horse_html}
                    </div>
                    <div style="text-align: right;">
                        <p style="margin: 0; color: #000000; font-size: 0.9em; font-weight: 500;">📅 {event_dt.strftime('%m/%d')} at {event_dt.strftime('%I:%M %p')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if len(upcoming["upcoming_events"]) >= 5:
                st.write("*View more in the Calendar tab*")
        else:
            st.write("No upcoming events in the next 7 days")
    
    st.write("")  # Add some spacing
    
    # Search and Filter Controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_term = st.text_input("🔍 Search horses", placeholder="Name, breed, owner...")
    
    with col2:
        active_only = st.checkbox("Active horses only", value=True)
    
    with col3:
        sort_by = st.selectbox("Sort by", ["age_years", "weight_lbs", "color", "gender"])
    
    with col4:
        sort_order = st.selectbox("Order", ["asc", "desc"])
    
    # Fetch horses
    params = {
        "search": search_term if search_term else None,
        "active_only": active_only,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "limit": 100
    }
    
    # Add organization_id if available
    if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
        params["organization_id"] = st.session_state.selected_barn_id
    
    horses = api_request("GET", "/api/v1/horses/", params)
    
    if not horses:
        st.warning("No horses found or unable to connect to API.")
        return
    
    # Display Summary Stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Horses", len(horses))
    
    with col2:
        active_horses = [h for h in horses if h.get('is_active', True)]
        st.metric("Active Horses", len(active_horses))
    
    with col3:
        retired_horses = [h for h in horses if h.get('is_retired', False)]
        st.metric("Retired Horses", len(retired_horses))
    
    with col4:
        for_sale_horses = [h for h in horses if h.get('is_for_sale', False)]
        st.metric("For Sale", len(for_sale_horses))
    
    st.divider()
    
    # Display Horses in Cards
    if horses:
        # Create responsive columns
        num_cols = 2
        cols = st.columns(num_cols)
        
        for idx, horse in enumerate(horses):
            col = cols[idx % num_cols]
            
            with col:
                # Horse Card with optional background image
                status_color = {
                    "Excellent": "🟢",
                    "Good": "🟢", 
                    "Fair": "🟡",
                    "Poor": "🟠",
                    "Critical": "🔴"
                }.get(horse.get('current_health_status', 'Good'), "⚪")
                
                # Check for profile photo and handle safely
                profile_photo = horse.get('profile_photo_path')
                has_background = False
                
                if profile_photo and profile_photo.strip():  # Check if not empty or just whitespace
                    import os
                    import base64
                    try:
                        # Check if file exists and is readable
                        if os.path.exists(profile_photo) and os.path.isfile(profile_photo):
                            with open(profile_photo, "rb") as img_file:
                                img_data = base64.b64encode(img_file.read()).decode()
                                img_extension = profile_photo.split('.')[-1].lower()
                                mime_type = f"image/{img_extension}" if img_extension in ['jpg', 'jpeg', 'png', 'gif', 'webp'] else "image/jpeg"
                                
                                # Render with background image using HTML
                                background_style = f"""
                                    background-image: url('data:{mime_type};base64,{img_data}');
                                    background-size: cover;
                                    background-position: center;
                                    background-repeat: no-repeat;
                                    position: relative;
                                """
                                overlay_style = """
                                    background: linear-gradient(to bottom,
                                        rgba(255,255,255,0.85) 0%,
                                        rgba(255,255,255,0.75) 60%,
                                        rgba(255,255,255,0.45) 100%);
                                    position: absolute;
                                    top: 0;
                                    left: 0;
                                    right: 0;
                                    bottom: 0;
                                    border-radius: 10px;
                                """
                                card_style = f"border: none; border-radius: 12px; padding: 20px; margin: 15px 0; min-height: 250px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08); transition: transform 0.2s ease, box-shadow 0.2s ease; {background_style}"
                                
                                st.markdown(f"""
                                <div style="border: none; border-radius: 12px; padding: 0; margin: 15px 0; min-height: 250px; background-color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08); display: flex; align-items: stretch;">
                                    <div style="flex: 1; padding: 20px; display: flex; flex-direction: column; justify-content: center;">
                                        <h3 style="margin: 0 0 15px 0; font-size: 1.5em; font-weight: bold; color: #000000;">{horse.get('name', 'Unknown')} <span style="font-size: 0.8em;">{status_color}</span></h3>
                                        <p style="margin: 5px 0; color: #000000; font-size: 0.9em;"><strong>Barn Name:</strong> {horse.get('barn_name', 'N/A')}</p>
                                        <p style="margin: 5px 0; color: #000000; font-size: 0.9em;"><strong>Breed:</strong> {horse.get('breed', 'Unknown')}</p>
                                        <p style="margin: 5px 0; color: #000000; font-size: 0.9em;"><strong>Age:</strong> {horse.get('age_display', 'Unknown')}</p>
                                        <p style="margin: 5px 0; color: #000000; font-size: 0.9em;"><strong>Location:</strong> {horse.get('current_location', 'Not specified')}</p>
                                        <p style="margin: 5px 0; color: #000000; font-size: 0.9em;"><strong>Stall:</strong> {horse.get('stall_number', 'N/A')}</p>
                                        <p style="margin: 5px 0; color: #000000; font-size: 0.9em;"><strong>Owner:</strong> {horse.get('owner_name', 'Not specified')}</p>
                                    </div>
                                    <div style="width: 200px; border-radius: 0 12px 12px 0; background-image: url('data:{mime_type};base64,{img_data}'); background-size: cover; background-position: center; background-repeat: no-repeat;"></div>
                                </div>
                                """, unsafe_allow_html=True)
                                has_background = True
                    except Exception as e:
                        # Silently handle any image loading errors
                        has_background = False
                
                # If no background image, use native Streamlit components
                if not has_background:
                    with st.container():
                        st.markdown(f"""
                        <div style="border: none; border-radius: 12px; padding: 0; margin: 15px 0; min-height: 250px; background-color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08); display: flex; align-items: stretch;">
                            <div style="flex: 1; padding: 20px; display: flex; flex-direction: column; justify-content: center;">
                                <h3 style="margin: 0 0 15px 0; font-size: 1.5em; font-weight: bold; color: #000000;">{horse.get('name', 'Unknown')} <span style="font-size: 0.8em;">{status_color}</span></h3>
                                <p style="margin: 5px 0; color: #000000; font-size: 0.9em;"><strong>Barn Name:</strong> {horse.get('barn_name', 'N/A')}</p>
                                <p style="margin: 5px 0; color: #000000; font-size: 0.9em;"><strong>Breed:</strong> {horse.get('breed', 'Unknown')}</p>
                                <p style="margin: 5px 0; color: #000000; font-size: 0.9em;"><strong>Age:</strong> {horse.get('age_display', 'Unknown')}</p>
                                <p style="margin: 5px 0; color: #000000; font-size: 0.9em;"><strong>Location:</strong> {horse.get('current_location', 'Not specified')}</p>
                                <p style="margin: 5px 0; color: #000000; font-size: 0.9em;"><strong>Stall:</strong> {horse.get('stall_number', 'N/A')}</p>
                                <p style="margin: 5px 0; color: #000000; font-size: 0.9em;"><strong>Owner:</strong> {horse.get('owner_name', 'Not specified')}</p>
                            </div>
                            <div style="width: 200px; border-radius: 0 12px 12px 0; background-color: #f0f0f0; display: flex; align-items: center; justify-content: center; color: #888; font-style: italic;">No Photo</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Action buttons
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.button(f"👁️ View", key=f"view_{horse['id']}", use_container_width=True):
                        st.session_state['selected_horse_id'] = horse['id']
                        if 'edit_mode' in st.session_state:
                            del st.session_state['edit_mode']
                        st.rerun()
                
                with col_btn2:
                    if st.button(f"✏️ Edit", key=f"edit_{horse['id']}", use_container_width=True):
                        st.session_state['selected_horse_id'] = horse['id']
                        st.session_state['edit_mode'] = True
                        st.rerun()
                
                with col_btn3:
                    if st.button(f"🤖 Ask AI", key=f"ai_{horse['id']}", use_container_width=True):
                        # Set AI context for the horse and navigate to AI page
                        st.session_state['ai_horse_id'] = horse['id']
                        st.session_state['ai_horse_name'] = horse['name']
                        # Set force AI page flag for navigation
                        st.session_state['force_ai_page'] = True
                        st.rerun()

def show_ai_assistant():
    """AI Assistant page with multiple interaction modes"""
    st.header("🤖 AI Horse Care Assistant")
    
    st.markdown("""
    Welcome to your AI Horse Care Assistant! Ask questions about horse management, 
    get personalized recommendations for your horses, or compare different horses.
    """)
    
    # Check if we have a specific horse to analyze
    if 'ai_horse_id' in st.session_state and st.session_state.ai_horse_id:
        st.info(f"💡 Ready to analyze **{st.session_state.ai_horse_name}**! Ask a question below or get a full analysis.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Get Full AI Analysis", type="primary"):
                with st.spinner(f"Analyzing {st.session_state.ai_horse_name}..."):
                    result = api_request("POST", "/api/v1/ai/analyze-horse", {
                        "horse_id": st.session_state.ai_horse_id
                    })
                    
                    if result and 'response' in result:
                        st.subheader(f"🐴 AI Analysis for {st.session_state.ai_horse_name}")
                        st.write(result['response'])
                    else:
                        st.error("Failed to get AI analysis")
        
        with col2:
            if st.button("❌ Clear Horse Selection"):
                del st.session_state['ai_horse_id']
                del st.session_state['ai_horse_name']
                st.rerun()
    
    # Tabs for different AI interactions
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Ask Question", "🔍 Horse Analysis", "⚖️ Compare Horses", "📚 General Questions"])
    
    with tab1:
        st.subheader("💬 Ask About a Specific Horse")
        
        # Horse selection for questions
        horses = api_request("GET", "/api/v1/horses/")
        if horses:
            # Use pre-selected horse or let user choose
            if 'ai_horse_id' in st.session_state:
                selected_horse_id = st.session_state.ai_horse_id
                selected_horse_name = st.session_state.ai_horse_name
                st.write(f"**Selected Horse:** {selected_horse_name}")
            else:
                horse_options = {f"{h['name']} ({h.get('breed', 'Unknown')})": h['id'] for h in horses}
                if horse_options:
                    selected_horse_display = st.selectbox("Select a horse:", [""] + list(horse_options.keys()))
                    if selected_horse_display:
                        selected_horse_id = horse_options[selected_horse_display]
                        selected_horse_name = selected_horse_display.split(" (")[0]
                    else:
                        selected_horse_id = None
                        selected_horse_name = None
                else:
                    st.warning("No horses found")
                    selected_horse_id = None
                    selected_horse_name = None
            
            if selected_horse_id:
                question = st.text_area(
                    f"Ask a question about {selected_horse_name}:",
                    placeholder="e.g., What feeding schedule do you recommend? How should I manage their training? What health issues should I watch for?",
                    height=100
                )

                # Photo upload section with improved styling
                st.markdown("**📸 Optional: Upload a photo for visual analysis**")

                # Add CSS styling to match Create Post page
                st.markdown("""
                <style>
                /* Target the file uploader container */
                [data-testid="stFileUploader"] {
                    background-color: white !important;
                }

                /* Target the drag and drop area */
                [data-testid="stFileUploader"] > div > div > div {
                    background-color: white !important;
                    background: white !important;
                    border: 2px dashed #1f77b4 !important;
                }

                /* Target the inner content */
                [data-testid="stFileUploader"] section {
                    background-color: white !important;
                    background: white !important;
                }

                /* Remove blue background from file uploader */
                .stFileUploader section {
                    background-color: white !important;
                    background: white !important;
                }

                .stFileUploader section div {
                    background-color: white !important;
                    background: white !important;
                }

                /* Hide the Browse files button inside the drag area */
                [data-testid="stFileUploader"] button {
                    display: none !important;
                }

                /* Hide the button text in the file uploader */
                [data-testid="stFileUploader"] section button {
                    display: none !important;
                }
                </style>
                """, unsafe_allow_html=True)

                # Create two columns for the buttons
                col_browse, col_camera = st.columns(2)

                uploaded_file = None
                camera_photo = None

                with col_browse:
                    st.markdown("**📁 Browse Files**")
                    uploaded_file = st.file_uploader(
                        "",  # Remove the label since we have it above
                        type=['png', 'jpg', 'jpeg', 'webp'],
                        help="Upload a photo of your horse for visual analysis",
                        key="ai_file_upload",
                        label_visibility="collapsed"
                    )

                with col_camera:
                    st.markdown("**📷 Camera**")
                    # Camera toggle button
                    if 'ai_camera_enabled' not in st.session_state:
                        st.session_state.ai_camera_enabled = False

                    if st.button("📷 Enable Camera" if not st.session_state.ai_camera_enabled else "📷 Disable Camera",
                                type="secondary", key="ai_camera_toggle"):
                        st.session_state.ai_camera_enabled = not st.session_state.ai_camera_enabled
                        st.rerun()

                    if st.session_state.ai_camera_enabled:
                        camera_photo = st.camera_input("Take a photo", help="Take a photo directly with your camera", key="ai_camera")

                # Use either uploaded file or camera photo
                photo_to_analyze = uploaded_file if uploaded_file else camera_photo

                if photo_to_analyze:
                    st.image(photo_to_analyze, caption="Photo for AI analysis", width=300)

                if st.button("🤖 Ask AI", type="primary", use_container_width=True):
                    if question:
                        with st.spinner("Getting AI response..."):
                            # Prepare request data
                            request_data = {
                                "horse_id": selected_horse_id,
                                "question": question
                            }
                            
                            # Add image if provided
                            if photo_to_analyze:
                                import base64
                                # Convert image to base64
                                image_bytes = photo_to_analyze.read()
                                image_base64 = base64.b64encode(image_bytes).decode()
                                request_data["image"] = image_base64
                                request_data["image_type"] = photo_to_analyze.type
                            
                            result = api_request("POST", "/api/v1/ai/analyze-horse", request_data)
                            
                            if result and 'response' in result:
                                st.subheader(f"🤖 AI Response about {selected_horse_name}")
                                st.write(result['response'])
                            else:
                                st.error("Failed to get AI response")
                    else:
                        st.warning("Please enter a question")
    
    with tab2:
        st.subheader("🔍 Get Full Horse Analysis")
        
        horses = api_request("GET", "/api/v1/horses/")
        if horses:
            horse_options = {f"{h['name']} ({h.get('breed', 'Unknown')})": h['id'] for h in horses}
            if horse_options:
                selected_horse_display = st.selectbox("Select a horse for analysis:", [""] + list(horse_options.keys()), 
                                                    key="analysis_horse")
                
                if selected_horse_display:
                    selected_horse_id = horse_options[selected_horse_display]
                    selected_horse_name = selected_horse_display.split(" (")[0]
                    
                    if st.button("🔍 Analyze This Horse", type="primary", use_container_width=True):
                        with st.spinner(f"Analyzing {selected_horse_name}..."):
                            result = api_request("POST", "/api/v1/ai/analyze-horse", {
                                "horse_id": selected_horse_id
                            })
                            
                            if result and 'response' in result:
                                st.subheader(f"🐴 Complete AI Analysis for {selected_horse_name}")
                                st.write(result['response'])
                            else:
                                st.error("Failed to get AI analysis")
    
    with tab3:
        st.subheader("⚖️ Compare Multiple Horses")
        
        horses = api_request("GET", "/api/v1/horses/")
        if horses:
            horse_options = {f"{h['name']} ({h.get('breed', 'Unknown')})": h['id'] for h in horses}
            
            selected_horses = st.multiselect(
                "Select horses to compare (minimum 2):",
                list(horse_options.keys())
            )
            
            if len(selected_horses) >= 2:
                comparison_question = st.text_area(
                    "Specific comparison question (optional):",
                    placeholder="e.g., Which horse would be better for a beginner rider? How should I adjust their feeding schedules?",
                    height=80
                )
                
                if st.button("🤖 Compare Horses", type="primary"):
                    selected_ids = [horse_options[horse] for horse in selected_horses]
                    
                    with st.spinner("Comparing horses..."):
                        result = api_request("POST", "/api/v1/ai/compare-horses", {
                            "horse_ids": selected_ids,
                            "comparison_question": comparison_question if comparison_question else None
                        })
                        
                        if result and 'response' in result:
                            st.subheader("🤖 AI Horse Comparison")
                            st.write(result['response'])
                        else:
                            st.error("Failed to get comparison")
            elif selected_horses:
                st.info("Please select at least 2 horses to compare")
    
    with tab4:
        st.subheader("📚 General Horse Management Questions")
        
        general_question = st.text_area(
            "Ask any general horse management question:",
            placeholder="e.g., What's the best way to introduce a new horse to the herd? How often should I have the vet check my horses? What are signs of colic?",
            height=100
        )
        
        include_context = st.checkbox("Include my barn's horses for context", value=True)
        
        if st.button("🤖 Get Expert Advice", type="primary"):
            if general_question:
                with st.spinner("Getting expert advice..."):
                    result = api_request("POST", "/api/v1/ai/general-question", {
                        "question": general_question,
                        "include_barn_context": include_context
                    })
                    
                    if result and 'response' in result:
                        st.subheader("🤖 Expert Advice")
                        st.write(result['response'])
                    else:
                        st.error("Failed to get advice")
            else:
                st.warning("Please enter a question")

def show_horse_profile():
    """Display detailed horse profile with all available fields"""
    horse_id = st.session_state.get('selected_horse_id')
    
    if not horse_id:
        st.error("No horse selected. Please go back to the directory.")
        return
    
    # Fetch FULL horse details using individual endpoint
    horse = api_request("GET", f"/api/v1/horses/{horse_id}")
    
    if not horse:
        st.error("Horse not found or unable to load profile.")
        return
    
    # Horse Header with Photo
    if horse.get('profile_photo_path'):
        import os
        if os.path.exists(horse['profile_photo_path']):
            col_photo, col_info, col_status, col_buttons = st.columns([1, 2, 1, 1])
            with col_photo:
                st.image(horse['profile_photo_path'], width=150, caption="Profile Photo")
        else:
            col_photo, col_info, col_status, col_buttons = st.columns([1, 2, 1, 1])
            with col_photo:
                st.markdown("📷")
                st.caption("No photo")
    else:
        col_photo, col_info, col_status, col_buttons = st.columns([1, 2, 1, 1])
        with col_photo:
            st.markdown("📷")
            st.caption("No photo")
    
    with col_info:
        st.title(f"🐴 {horse.get('name', 'Unknown')}")
        if horse.get('barn_name') and horse['barn_name'] != horse['name'] and horse['barn_name']:
            st.subheader(f"'{horse['barn_name']}'")
    
    with col_status:
        status_text = horse.get('current_health_status', 'Good')
        status_emoji = {
            "Excellent": "🟢",
            "Good": "🟢", 
            "Fair": "🟡",
            "Poor": "🟠",
            "Critical": "🔴"
        }.get(status_text, "⚪")
        
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ff4b4b;">
            <p style="color: #262730; font-size: 0.75rem; margin: 0; font-weight: 600;">HEALTH STATUS</p>
            <p style="color: #262730; font-size: 1.5rem; margin: 0; font-weight: 700;">
                <span class="health-emoji">{status_emoji}</span> {status_text}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_buttons:
        col_back, col_edit, col_ai = st.columns(3)
        with col_back:
            if st.button("🏠", help="Back to Directory", use_container_width=True):
                del st.session_state['selected_horse_id']
                st.rerun()
        with col_edit:
            if st.button("✏️", help="Edit Horse", use_container_width=True):
                st.session_state['edit_mode'] = True
                st.rerun()
        with col_ai:
            if st.button("🤖", help="Ask AI", type="primary", use_container_width=True):
                # Set AI context for current horse
                st.session_state['ai_horse_id'] = horse_id
                st.session_state['ai_horse_name'] = horse['name']
                # Clear horse profile context to allow navigation to AI page
                if 'selected_horse_id' in st.session_state:
                    del st.session_state['selected_horse_id']
                if 'edit_mode' in st.session_state:
                    del st.session_state['edit_mode']
                # Set a flag to force AI Assistant page
                st.session_state['force_ai_page'] = True
                st.rerun()
    
    st.divider()
    
    # Horse Information Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📋 Basic Info", "📏 Physical", "🏠 Management", "🏥 Health", "📝 Notes", "📚 Documents"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Identity")
            st.write(f"**Name:** {horse.get('name', 'Not specified')}")
            barn_name = horse.get('barn_name')
            st.write(f"**Barn Name:** {barn_name if barn_name else 'Not specified'}")
            st.write(f"**Breed:** {horse.get('breed', 'Not specified')}")
            st.write(f"**Color:** {horse.get('color', 'Not specified')}")
            st.write(f"**Gender:** {horse.get('gender', 'Not specified')}")
            
            # Show both age formats if available
            age_display = horse.get('age_display')
            age_years = horse.get('age_years')
            if age_display:
                st.write(f"**Age:** {age_display}")
            elif age_years:
                st.write(f"**Age:** {age_years} years")
            else:
                st.write("**Age:** Unknown")
        
        with col2:
            st.subheader("Registration")
            reg_number = horse.get('registration_number')
            st.write(f"**Registration #:** {reg_number if reg_number else 'Not registered'}")
            
            registry = horse.get('registration_organization')
            st.write(f"**Registry:** {registry if registry else 'Not specified'}")
            
            microchip = horse.get('microchip_number')
            st.write(f"**Microchip:** {microchip if microchip else 'Not specified'}")
            
            passport = horse.get('passport_number')
            st.write(f"**Passport #:** {passport if passport else 'Not specified'}")
            
            st.subheader("Status")
            status_items = []
            if horse.get('is_active', True):
                status_items.append("✅ Active")
            if horse.get('is_retired', False):
                status_items.append("🏖️ Retired")
            if horse.get('is_for_sale', False):
                status_items.append("💰 For Sale")
            
            for item in status_items:
                st.write(item)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Physical Measurements")
            
            # Height
            height = horse.get('height_hands')
            if height:
                st.metric("Height", f"{height} hands")
            else:
                st.write("**Height:** Not recorded")
            
            # Weight
            weight = horse.get('weight_lbs')
            if weight:
                st.metric("Weight", f"{weight} lbs")
            else:
                st.write("**Weight:** Not recorded")
            
            # Body Condition Score
            bcs = horse.get('body_condition_score')
            if bcs:
                st.metric("Body Condition Score", f"{bcs}/9")
            else:
                st.write("**Body Condition Score:** Not assessed")
        
        with col2:
            st.subheader("Markings & Features")
            markings = horse.get('markings')
            if markings:
                st.write("**Markings:**")
                st.write(markings)
            else:
                st.write("**Markings:** No special markings noted")
            
            # Additional physical notes
            physical_notes = horse.get('physical_notes')
            if physical_notes:
                st.write("**Physical Notes:**")
                st.write(physical_notes)
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Location & Housing")
            current_location = horse.get('current_location')
            st.write(f"**Current Location:** {current_location if current_location else 'Not specified'}")
            
            stall_number = horse.get('stall_number')
            st.write(f"**Stall/Paddock:** {stall_number if stall_number else 'Not specified'}")
            
            pasture_group = horse.get('pasture_group')
            st.write(f"**Pasture Group:** {pasture_group if pasture_group else 'Not specified'}")
            
            boarding_type = horse.get('boarding_type')
            st.write(f"**Boarding Type:** {boarding_type if boarding_type else 'Not specified'}")
            
            st.subheader("Owner Information")
            owner_name = horse.get('owner_name')
            st.write(f"**Owner:** {owner_name if owner_name else 'Not specified'}")
            
            owner_contact = horse.get('owner_contact')
            if owner_contact:
                st.write(f"**Contact:** {owner_contact}")
        
        with col2:
            st.subheader("Training & Disciplines")
            training_level = horse.get('training_level')
            st.write(f"**Training Level:** {training_level if training_level else 'Not specified'}")
            
            disciplines = horse.get('disciplines')
            st.write(f"**Disciplines:** {disciplines if disciplines else 'Not specified'}")
            
            trainer_name = horse.get('trainer_name')
            st.write(f"**Trainer:** {trainer_name if trainer_name else 'Not specified'}")
            
            trainer_contact = horse.get('trainer_contact')
            if trainer_contact:
                st.write(f"**Trainer Contact:** {trainer_contact}")
            
            st.subheader("Care Schedule")
            feeding_schedule = horse.get('feeding_schedule')
            if feeding_schedule:
                st.write(f"**Feeding Schedule:** {feeding_schedule}")
            
            exercise_schedule = horse.get('exercise_schedule')
            if exercise_schedule:
                st.write(f"**Exercise Schedule:** {exercise_schedule}")
    
    with tab4:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Current Health")
            current_health = horse.get('current_health_status', 'Good')
            st.write(f"**Status:** {current_health}")
            
            # Allergies
            allergies = horse.get('allergies')
            if allergies:
                st.write("**Allergies:**")
                st.write(allergies)
            else:
                st.write("**Allergies:** None specified")
            
            # Current Medications
            medications = horse.get('medications')
            if medications:
                st.write("**Current Medications:**")
                st.write(medications)
            else:
                st.write("**Current Medications:** None specified")
            
            # Special Needs
            special_needs = horse.get('special_needs')
            if special_needs:
                st.write("**Special Needs:**")
                st.write(special_needs)
        
        with col2:
            st.subheader("Veterinary Team")
            vet_name = horse.get('veterinarian_name')
            st.write(f"**Primary Veterinarian:** {vet_name if vet_name else 'Not specified'}")
            
            vet_contact = horse.get('veterinarian_contact')
            if vet_contact:
                st.write(f"**Vet Contact:** {vet_contact}")
            
            farrier_name = horse.get('farrier_name')
            if farrier_name:
                st.write(f"**Farrier:** {farrier_name}")
            
            st.subheader("Emergency Contact")
            emergency_name = horse.get('emergency_contact_name')
            st.write(f"**Emergency Contact:** {emergency_name if emergency_name else 'Not specified'}")
            
            emergency_phone = horse.get('emergency_contact_phone')
            if emergency_phone:
                st.write(f"**Emergency Phone:** {emergency_phone}")
            
            st.subheader("Health History")
            last_vet_visit = horse.get('last_vet_visit')
            if last_vet_visit:
                st.write(f"**Last Vet Visit:** {format_date(last_vet_visit)}")
            
            last_dental = horse.get('last_dental')
            if last_dental:
                st.write(f"**Last Dental:** {format_date(last_dental)}")
            
            last_farrier = horse.get('last_farrier')
            if last_farrier:
                st.write(f"**Last Farrier:** {format_date(last_farrier)}")

    with tab5:
        st.subheader("Notes & Instructions")
        
        # General Notes
        notes = horse.get('notes')
        if notes:
            st.write("**General Notes:**")
            st.write(notes)
        else:
            st.write("**General Notes:** No notes recorded")
        
        # Special Instructions
        instructions = horse.get('special_instructions')
        if instructions:
            st.write("**Special Instructions:**")
            st.write(instructions)
        else:
            st.write("**Special Instructions:** No special instructions")
        
        # Feeding Notes
        feeding_notes = horse.get('feeding_notes')
        if feeding_notes:
            st.write("**Feeding Notes:**")
            st.write(feeding_notes)
        
        # Training Notes
        training_notes = horse.get('training_notes')
        if training_notes:
            st.write("**Training Notes:**")
            st.write(training_notes)
        
        st.divider()
        
        # Record Information
        st.subheader("Record Information")
        created_at = horse.get('created_at')
        if created_at:
            st.write(f"**Added to system:** {format_date(created_at)}")
        
        updated_at = horse.get('updated_at')
        if updated_at:
            st.write(f"**Last updated:** {format_date(updated_at)}")
        else:
            st.write("**Last updated:** Not recorded")
    
    with tab6:
        show_horse_documents(horse['id'], horse['name'])

def show_horse_documents(horse_id: int, horse_name: str):
    """Display and manage documents for a horse"""
    
    st.subheader(f"📚 Documents for {horse_name}")
    
    # Document upload section
    st.write("### Upload New Document")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a document",
            type=['pdf', 'docx', 'doc', 'txt', 'jpg', 'jpeg', 'png', 'tiff'],
            help="Supported formats: PDF, DOCX, DOC, TXT, JPG, PNG, TIFF (Max 10MB)"
        )
    
    with col2:
        document_categories = {
            "medical_record": "🏥 Medical Record",
            "veterinary_report": "👩‍⚕️ Veterinary Report", 
            "vaccination_record": "💉 Vaccination Record",
            "training_notes": "🏃 Training Notes",
            "feed_evaluation": "🌾 Feed Evaluation",
            "behavioral_notes": "🧠 Behavioral Notes",
            "breeding_record": "🐎 Breeding Record",
            "ownership_papers": "📋 Ownership Papers",
            "insurance_document": "🛡️ Insurance Document",
            "competition_record": "🏆 Competition Record",
            "general": "📄 General"
        }
        
        selected_category = st.selectbox(
            "Document Category",
            options=list(document_categories.keys()),
            format_func=lambda x: document_categories[x]
        )
    
    # Additional metadata
    col3, col4 = st.columns(2)
    with col3:
        title = st.text_input("Document Title (optional)", placeholder="e.g., Annual Vaccination Record 2025")
    with col4:
        description = st.text_area("Description (optional)", placeholder="Brief description of the document content...")
    
    # Upload button
    if uploaded_file is not None:
        if st.button("📤 Upload Document", type="primary"):
            with st.spinner("Uploading document..."):
                try:
                    # Prepare form data
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data = {
                        "document_category": selected_category,
                    }
                    if title:
                        data["title"] = title
                    if description:
                        data["description"] = description
                    
                    # Upload via API
                    response = requests.post(
                        f"{API_BASE_URL}/api/v1/horses/{horse_id}/documents",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 201:
                        st.success(f"✅ Document '{uploaded_file.name}' uploaded successfully!")
                        st.rerun()
                    else:
                        error_detail = response.json().get("detail", "Upload failed") if response.content else "Upload failed"
                        st.error(f"❌ Upload failed: {error_detail}")
                        
                except Exception as e:
                    st.error(f"❌ Upload error: {str(e)}")
    
    st.divider()
    
    # Document list section
    st.write("### Existing Documents")
    
    # Category filter
    col1, col2 = st.columns([2, 1])
    with col1:
        filter_categories = ["All Categories"] + [document_categories[k] for k in document_categories.keys()]
        selected_filter = st.selectbox(
            "Filter by Category",
            options=filter_categories,
            key=f"doc_filter_{horse_id}"
        )
    
    # Get documents
    try:
        params = {}
        if selected_filter != "All Categories":
            # Find the category key for the selected display value
            category_key = next(k for k, v in document_categories.items() if v == selected_filter)
            params["category"] = category_key
        
        response = api_request("GET", f"/api/v1/horses/{horse_id}/documents", params)
        
        if response and isinstance(response, list):
            if len(response) > 0:
                # Display documents
                for doc in response:
                    with st.expander(f"{document_categories.get(doc['document_category'], doc['document_category'])} - {doc.get('title', doc['original_filename'])}"):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**Filename:** {doc['original_filename']}")
                            st.write(f"**Upload Date:** {format_date(doc['upload_date'])}")
                            if doc.get('description'):
                                st.write(f"**Description:** {doc['description']}")
                            if doc.get('ai_summary'):
                                st.info(f"**AI Summary:** {doc['ai_summary']}")
                        
                        with col2:
                            file_size_mb = doc['file_size_bytes'] / (1024 * 1024)
                            st.write(f"**Size:** {file_size_mb:.1f} MB")
                            st.write(f"**Type:** {doc['file_type']}")
                            st.write(f"**Status:** {doc['processing_status'].title()}")
                        
                        with col3:
                            if st.button("📥 Download", key=f"download_{doc['id']}"):
                                # Download file
                                try:
                                    download_url = f"{API_BASE_URL}/api/v1/horses/{horse_id}/documents/{doc['id']}/download"
                                    st.write(f"[Download {doc['original_filename']}]({download_url})")
                                except Exception as e:
                                    st.error(f"Download failed: {str(e)}")
                            
                            if st.button("🗑️ Delete", key=f"delete_{doc['id']}", help="Delete document"):
                                if st.session_state.get(f"confirm_delete_{doc['id']}", False):
                                    # Perform delete
                                    try:
                                        delete_response = api_request("DELETE", f"/api/v1/horses/{horse_id}/documents/{doc['id']}")
                                        st.success("Document deleted!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Delete failed: {str(e)}")
                                else:
                                    st.session_state[f"confirm_delete_{doc['id']}"] = True
                                    st.warning("Click again to confirm deletion")
            else:
                st.info("📄 No documents uploaded yet. Use the form above to upload the first document for this horse.")
        else:
            st.error("Failed to load documents")
            
    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")

def show_edit_horse_form():
    """Form to edit an existing horse"""
    horse_id = st.session_state.get('selected_horse_id')
    
    if not horse_id:
        st.error("No horse selected for editing.")
        return
    
    # Fetch current horse data
    horse = api_request("GET", f"/api/v1/horses/{horse_id}")
    
    if not horse:
        st.error("Horse not found.")
        return
    
    st.header(f"✏️ Edit {horse.get('name', 'Horse')}")
    
    with st.form("edit_horse_form"):
        # Basic Information
        st.subheader("📋 Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Horse Name*", value=horse.get('name', ''))
            barn_name = st.text_input("Barn/Call Name", value=horse.get('barn_name', '') or '')
            breed = st.text_input("Breed", value=horse.get('breed', '') or '')
            color = st.text_input("Color", value=horse.get('color', '') or '')
            
        with col2:
            gender_options = ["", "Mare", "Stallion", "Gelding"]
            gender_index = 0
            if horse.get('gender') in gender_options:
                gender_index = gender_options.index(horse.get('gender'))
            gender = st.selectbox("Gender", gender_options, index=gender_index)
            
            age_years = st.number_input("Age (years)", min_value=0, max_value=50, 
                                       value=horse.get('age_years') or 0)
            height_hands = st.number_input("Height (hands)", min_value=8.0, max_value=22.0, step=0.1, 
                                          value=float(horse.get('height_hands', 8.00)) if horse.get('height_hands') else 8.0)
            weight_lbs = st.number_input("Weight (lbs)", min_value=200, max_value=3000, step=25, 
                                        value=horse.get('weight_lbs') or 200)
        
        # Registration Information
        st.subheader("📄 Registration & Identification")
        col1, col2 = st.columns(2)
        
        with col1:
            registration_number = st.text_input("Registration Number", value=horse.get('registration_number', '') or '')
            microchip_number = st.text_input("Microchip Number", value=horse.get('microchip_number', '') or '')
            
        with col2:
            registration_organization = st.text_input("Registration Organization", value=horse.get('registration_organization', '') or '')
            passport_number = st.text_input("Passport Number", value=horse.get('passport_number', '') or '')
        
        # Location Information
        st.subheader("🏠 Location & Management")
        col1, col2 = st.columns(2)
        
        with col1:
            current_location = st.text_input("Current Location/Facility", value=horse.get('current_location', '') or '')
            stall_number = st.text_input("Stall/Paddock Number", value=horse.get('stall_number', '') or '')
            
        with col2:
            owner_name = st.text_input("Owner Name", value=horse.get('owner_name', '') or '')
            boarding_options = ["", "Full Care", "Partial Care", "Self Care", "Pasture Board"]
            boarding_index = 0
            if horse.get('boarding_type') in boarding_options:
                boarding_index = boarding_options.index(horse.get('boarding_type'))
            boarding_type = st.selectbox("Boarding Type", boarding_options, index=boarding_index)
        
        # Training & Disciplines  
        st.subheader("🏇 Training & Disciplines")
        col1, col2 = st.columns(2)
        
        with col1:
            training_level = st.text_input("Training Level", value=horse.get('training_level', '') or '')
            disciplines = st.text_input("Disciplines", value=horse.get('disciplines', '') or '')
            
        with col2:
            trainer_name = st.text_input("Trainer Name", value=horse.get('trainer_name', '') or '')
            trainer_contact = st.text_input("Trainer Contact", value=horse.get('trainer_contact', '') or '')
        
        # Care Schedule
        st.subheader("📅 Care Schedule")
        col1, col2 = st.columns(2)
        
        with col1:
            feeding_schedule = st.text_area("Feeding Schedule", value=horse.get('feeding_schedule', '') or '', height=80)
            
        with col2:
            exercise_schedule = st.text_area("Exercise Schedule", value=horse.get('exercise_schedule', '') or '', height=80)
        
        # Health Information
        st.subheader("🏥 Health Information")
        col1, col2 = st.columns(2)
        
        with col1:
            health_options = ["Good", "Excellent", "Fair", "Poor", "Critical"]
            health_index = 0
            if horse.get('current_health_status') in health_options:
                health_index = health_options.index(horse.get('current_health_status'))
            current_health_status = st.selectbox("Current Health Status", health_options, index=health_index)
            
            veterinarian_name = st.text_input("Primary Veterinarian", value=horse.get('veterinarian_name', '') or '')
            
        with col2:
            allergies = st.text_area("Known Allergies", value=horse.get('allergies', '') or '', height=80)
            medications = st.text_area("Current Medications", value=horse.get('medications', '') or '', height=80)
        
        # Emergency & Veterinary Contacts
        st.subheader("🚨 Emergency & Veterinary Contacts")
        col1, col2 = st.columns(2)
        
        with col1:
            emergency_contact_name = st.text_input("Emergency Contact Name", value=horse.get('emergency_contact_name', '') or '')
            emergency_contact_phone = st.text_input("Emergency Contact Phone", value=horse.get('emergency_contact_phone', '') or '')
            
        with col2:
            veterinarian_contact = st.text_input("Veterinarian Contact", value=horse.get('veterinarian_contact', '') or '')
            farrier_name = st.text_input("Farrier Name", value=horse.get('farrier_name', '') or '')
        
        # Health History
        st.subheader("📋 Health History")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            last_vet_visit = st.date_input("Last Vet Visit", value=None if not horse.get('last_vet_visit') else datetime.fromisoformat(horse.get('last_vet_visit')).date())
            
        with col2:
            last_dental = st.date_input("Last Dental", value=None if not horse.get('last_dental') else datetime.fromisoformat(horse.get('last_dental')).date())
            
        with col3:
            last_farrier = st.date_input("Last Farrier", value=None if not horse.get('last_farrier') else datetime.fromisoformat(horse.get('last_farrier')).date())
        
        # Profile Photo
        st.subheader("📸 Profile Photo")
        col_current, col_new = st.columns(2)
        
        with col_current:
            if horse.get('profile_photo_path'):
                import os
                if os.path.exists(horse['profile_photo_path']):
                    st.image(horse['profile_photo_path'], width=150, caption="Current Photo")
                else:
                    st.write("📷 Current photo not found")
            else:
                st.write("📷 No current photo")
        
        with col_new:
            uploaded_photo = st.file_uploader(
                "Upload new profile photo",
                type=['png', 'jpg', 'jpeg', 'webp'],
                help="Upload a new profile photo (will replace current photo if any)"
            )
        
        # Notes
        st.subheader("📝 Additional Information")
        notes = st.text_area("General Notes", value=horse.get('notes', '') or '', height=100)
        
        # Status checkboxes
        st.subheader("Status")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            is_active = st.checkbox("Active", value=horse.get('is_active', True))
        with col2:
            is_retired = st.checkbox("Retired", value=horse.get('is_retired', False))
        with col3:
            is_for_sale = st.checkbox("For Sale", value=horse.get('is_for_sale', False))
        
        # Submit buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            submitted = st.form_submit_button("💾 Save Changes", type="primary")
        
        with col2:
            cancel = st.form_submit_button("❌ Cancel")
        
        if cancel:
            del st.session_state['edit_mode']
            st.rerun()
        
        if submitted:
            if not name:
                st.error("Horse name is required!")
                return
            
            # Prepare update data
            update_data = {
                "name": name,
                "barn_name": barn_name if barn_name else None,
                "breed": breed if breed else None,
                "color": color if color else None,
                "gender": gender if gender else None,
                "age_years": int(age_years) if age_years and age_years > 0 else None,
                "height_hands": height_hands if height_hands else None,
                "weight_lbs": int(weight_lbs) if weight_lbs and weight_lbs > 0 else None,
                "registration_number": registration_number if registration_number else None,
                "registration_organization": registration_organization if registration_organization else None,
                "microchip_number": microchip_number if microchip_number else None,
                "passport_number": passport_number if passport_number else None,
                "owner_name": owner_name if owner_name else None,
                "current_location": current_location if current_location else None,
                "stall_number": stall_number if stall_number else None,
                "boarding_type": boarding_type if boarding_type else None,
                "training_level": training_level if training_level else None,
                "disciplines": disciplines if disciplines else None,
                "trainer_name": trainer_name if trainer_name else None,
                "trainer_contact": trainer_contact if trainer_contact else None,
                "feeding_schedule": feeding_schedule if feeding_schedule else None,
                "exercise_schedule": exercise_schedule if exercise_schedule else None,
                "current_health_status": current_health_status,
                "veterinarian_name": veterinarian_name if veterinarian_name else None,
                "veterinarian_contact": veterinarian_contact if veterinarian_contact else None,
                "farrier_name": farrier_name if farrier_name else None,
                "emergency_contact_name": emergency_contact_name if emergency_contact_name else None,
                "emergency_contact_phone": emergency_contact_phone if emergency_contact_phone else None,
                "last_vet_visit": last_vet_visit.isoformat() if last_vet_visit else None,
                "last_dental": last_dental.isoformat() if last_dental else None,
                "last_farrier": last_farrier.isoformat() if last_farrier else None,
                "allergies": allergies if allergies else None,
                "medications": medications if medications else None,
                "notes": notes if notes else None,
                "is_active": is_active,
                "is_retired": is_retired,
                "is_for_sale": is_for_sale
            }
            
            # Handle photo upload if provided
            if uploaded_photo:
                import os
                import uuid
                # Get absolute path to storage directory
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                storage_dir = os.path.join(project_root, "storage", "horse_photos")
                os.makedirs(storage_dir, exist_ok=True)
                
                # Save photo with unique name
                photo_filename = f"{uuid.uuid4()}_{uploaded_photo.name}"
                photo_path = os.path.join(storage_dir, photo_filename)
                
                with open(photo_path, "wb") as f:
                    f.write(uploaded_photo.read())
                update_data["profile_photo_path"] = photo_path
            
            # Submit to API
            result = api_request("PUT", f"/api/v1/horses/{horse_id}", update_data)
            
            if result:
                st.success(f"✅ Successfully updated {name}!")
                del st.session_state['edit_mode']
                st.rerun()
            else:
                st.error("Failed to update horse. Please try again.")

def show_add_horse_form():
    """Form to add a new horse"""
    st.header("➕ Add New Horse")
    
    with st.form("add_horse_form", clear_on_submit=True):
        # Basic Information
        st.subheader("📋 Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Horse Name*", help="Registered name")
            barn_name = st.text_input("Barn/Call Name", help="Nickname or barn call name")
            breed = st.text_input("Breed")
            color = st.text_input("Color")
            
        with col2:
            gender = st.selectbox("Gender", ["", "Mare", "Stallion", "Gelding"])
            age_years = st.number_input("Age (years)", min_value=0, max_value=50, value=None)
            height_hands = st.number_input("Height (hands)", min_value=8.0, max_value=22.0, step=0.1, value=None)
            weight_lbs = st.number_input("Weight (lbs)", min_value=200, max_value=3000, step=25, value=None)
        
        # Registration Information
        st.subheader("📄 Registration & Identification")
        col1, col2 = st.columns(2)
        
        with col1:
            registration_number = st.text_input("Registration Number")
            microchip_number = st.text_input("Microchip Number")
            
        with col2:
            registration_organization = st.text_input("Registration Organization")
            passport_number = st.text_input("Passport Number")
        
        # Location Information
        st.subheader("🏠 Location & Management")
        col1, col2 = st.columns(2)
        
        with col1:
            current_location = st.text_input("Current Location/Facility")
            stall_number = st.text_input("Stall/Paddock Number")
            
        with col2:
            owner_name = st.text_input("Owner Name")
            boarding_type = st.selectbox("Boarding Type", ["", "Full Care", "Partial Care", "Self Care", "Pasture Board"])
        
        # Training & Disciplines  
        st.subheader("🏇 Training & Disciplines")
        col1, col2 = st.columns(2)
        
        with col1:
            training_level = st.text_input("Training Level")
            disciplines = st.text_input("Disciplines")
            
        with col2:
            trainer_name = st.text_input("Trainer Name")
            trainer_contact = st.text_input("Trainer Contact")
        
        # Care Schedule
        st.subheader("📅 Care Schedule")
        col1, col2 = st.columns(2)
        
        with col1:
            feeding_schedule = st.text_area("Feeding Schedule", height=80)
            
        with col2:
            exercise_schedule = st.text_area("Exercise Schedule", height=80)
        
        # Health Information
        st.subheader("🏥 Health Information")
        col1, col2 = st.columns(2)
        
        with col1:
            current_health_status = st.selectbox("Current Health Status", 
                                               ["Good", "Excellent", "Fair", "Poor", "Critical"])
            veterinarian_name = st.text_input("Primary Veterinarian")
            
        with col2:
            allergies = st.text_area("Known Allergies", height=80)
            medications = st.text_area("Current Medications", height=80)
        
        # Emergency & Veterinary Contacts
        st.subheader("🚨 Emergency & Veterinary Contacts")
        col1, col2 = st.columns(2)
        
        with col1:
            emergency_contact_name = st.text_input("Emergency Contact Name")
            emergency_contact_phone = st.text_input("Emergency Contact Phone")
            
        with col2:
            veterinarian_contact = st.text_input("Veterinarian Contact")
            farrier_name = st.text_input("Farrier Name")
        
        # Health History
        st.subheader("📋 Health History")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            last_vet_visit = st.date_input("Last Vet Visit", value=None)
            
        with col2:
            last_dental = st.date_input("Last Dental", value=None)
            
        with col3:
            last_farrier_date = st.date_input("Last Farrier", value=None)
        
        # Profile Photo
        st.subheader("📸 Profile Photo")
        uploaded_photo = st.file_uploader(
            "Upload horse profile photo",
            type=['png', 'jpg', 'jpeg', 'webp'],
            help="Upload a profile photo of this horse"
        )
        
        # Notes
        st.subheader("📝 Additional Information")
        notes = st.text_area("General Notes", height=100, 
                             help="Any additional information about this horse")
        
        # Submit button
        submitted = st.form_submit_button("🐴 Add Horse", type="primary")
        
        if submitted:
            if not name:
                st.error("Horse name is required!")
                return
            
            # Prepare data
            horse_data = {
                "name": name,
                "barn_name": barn_name if barn_name else None,
                "breed": breed if breed else None,
                "color": color if color else None,
                "gender": gender if gender else None,
                "age_years": int(age_years) if age_years and age_years > 0 else None,
                "height_hands": height_hands if height_hands and height_hands > 0 else None,
                "weight_lbs": int(weight_lbs) if weight_lbs and weight_lbs > 0 else None,
                "registration_number": registration_number if registration_number else None,
                "registration_organization": registration_organization if registration_organization else None,
                "microchip_number": microchip_number if microchip_number else None,
                "passport_number": passport_number if passport_number else None,
                "owner_name": owner_name if owner_name else None,
                "current_location": current_location if current_location else None,
                "stall_number": stall_number if stall_number else None,
                "boarding_type": boarding_type if boarding_type else None,
                "training_level": training_level if training_level else None,
                "disciplines": disciplines if disciplines else None,
                "trainer_name": trainer_name if trainer_name else None,
                "trainer_contact": trainer_contact if trainer_contact else None,
                "feeding_schedule": feeding_schedule if feeding_schedule else None,
                "exercise_schedule": exercise_schedule if exercise_schedule else None,
                "current_health_status": current_health_status,
                "veterinarian_name": veterinarian_name if veterinarian_name else None,
                "veterinarian_contact": veterinarian_contact if veterinarian_contact else None,
                "farrier_name": farrier_name if farrier_name else None,
                "emergency_contact_name": emergency_contact_name if emergency_contact_name else None,
                "emergency_contact_phone": emergency_contact_phone if emergency_contact_phone else None,
                "last_vet_visit": last_vet_visit.isoformat() if last_vet_visit else None,
                "last_dental": last_dental.isoformat() if last_dental else None,
                "last_farrier": last_farrier_date.isoformat() if last_farrier_date else None,
                "allergies": allergies if allergies else None,
                "medications": medications if medications else None,
                "notes": notes if notes else None,
                "is_active": True,
                "is_retired": False,
                "is_for_sale": False
            }
            
            # Handle photo upload if provided
            if uploaded_photo:
                import os
                import uuid
                # Get absolute path to storage directory
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                storage_dir = os.path.join(project_root, "storage", "horse_photos")
                os.makedirs(storage_dir, exist_ok=True)
                
                # Save photo with unique name
                photo_filename = f"{uuid.uuid4()}_{uploaded_photo.name}"
                photo_path = os.path.join(storage_dir, photo_filename)
                
                with open(photo_path, "wb") as f:
                    f.write(uploaded_photo.read())
                horse_data["profile_photo_path"] = photo_path
            
            # Submit to API with organization context
            endpoint = "/api/v1/horses/"
            if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
                endpoint = f"/api/v1/horses/?organization_id={st.session_state.selected_barn_id}"
            
            result = api_request("POST", endpoint, horse_data)
            
            if result:
                st.success(f"✅ Successfully added {name} to the barn!")
                st.balloons()
                st.info("Horse has been added! Go to Horse Directory to see all horses.")
            else:
                st.error("Failed to add horse. Please check your inputs and try again.")

def show_whiteboard():
    """Display whiteboard page"""
    show_whiteboard_page()

def show_calendar():
    """Display calendar view and event management"""
    st.header("📅 Event Calendar")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Calendar View", "Upcoming Events", "Add Event"])
    
    with tab1:
        st.subheader("📅 Monthly Calendar")
        
        # Month selector
        col1, col2 = st.columns(2)
        with col1:
            current_year = datetime.now().year
            year_options = [current_year - 1, current_year, current_year + 1]
            selected_year = st.selectbox("Year", year_options, index=1)
        with col2:
            current_month = datetime.now().month
            selected_month = st.selectbox("Month", 
                                        [(i, datetime(2025, i, 1).strftime('%B')) for i in range(1, 13)],
                                        format_func=lambda x: x[1],
                                        index=current_month - 1)
        
        # Get events for the month with organization filter
        month_params = {
            "year": selected_year,
            "month": selected_month[0]
        }
        if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
            month_params["organization_id"] = st.session_state.selected_barn_id
        
        events = api_request("GET", "/api/v1/calendar/view/month", month_params)
        
        if events and "events" in events:
            st.subheader(f"Events in {selected_month[1]} {selected_year}")
            
            if events["events"]:
                # Group events by date
                events_by_date = {}
                for event in events["events"]:
                    event_date = datetime.fromisoformat(event["scheduled_date"]).date()
                    if event_date not in events_by_date:
                        events_by_date[event_date] = []
                    events_by_date[event_date].append(event)
                
                # Display events by date
                for event_date in sorted(events_by_date.keys()):
                    st.write(f"**{event_date.strftime('%A, %B %d, %Y')}**")
                    
                    for event in events_by_date[event_date]:
                        # Color code by event type
                        type_colors = {
                            "veterinary": "🏥",
                            "farrier": "🔨",
                            "dental": "🦷",
                            "supply_delivery": "🚛",
                            "training": "⭐",
                            "breeding": "💕",
                            "health_treatment": "💊",
                            "other": "📅"
                        }

                        icon = type_colors.get(event["event_type"], "📅")
                        status_color = "🔴" if event["is_overdue"] else "🟢"
                        horse_info = f"{event['horse_name']}" if event["horse_name"] else ""
                        provider_info = f"👤 {event['provider_name']}" if event.get('provider_name') else ""
                        location_info = event.get('location', 'No location')
                        time_info = datetime.fromisoformat(event['scheduled_date']).strftime('%I:%M %p')

                        with st.container():
                            event_col1, event_col2 = st.columns([4, 1])

                            with event_col1:
                                st.markdown(f"""
                                <div style="background-color: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 10px 0;">
                                    <h4 style="margin: 0 0 10px 0; color: #000;">{icon} {event['title']}</h4>
                                    <p style="margin: 5px 0; color: #666; font-size: 0.9em;">📍 {location_info} | ⏰ {time_info}</p>
                                </div>
                                """, unsafe_allow_html=True)

                            with event_col2:
                                st.write("")  # Spacing
                                st.write(f"{status_color}")
                                if horse_info:
                                    st.write(f"🐴 {horse_info}")
                                if provider_info:
                                    st.write(provider_info)
                    
                # Summary stats
                st.subheader("📊 Month Summary")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Events", events["total_events"])
                
                with col2:
                    overdue_count = sum(1 for e in events["events"] if e["is_overdue"])
                    st.metric("Overdue Events", overdue_count)
                
                with col3:
                    upcoming_count = sum(1 for e in events["events"] if not e["is_overdue"])
                    st.metric("Upcoming Events", upcoming_count)
                
            else:
                st.info(f"No events scheduled for {selected_month[1]} {selected_year}")
        else:
            st.error("Unable to load calendar events")
    
    with tab2:
        st.subheader("🔜 Upcoming Events")
        
        # Get upcoming events
        upcoming = api_request("GET", "/api/v1/calendar/upcoming", {"days_ahead": 14})
        
        if upcoming and "upcoming_events" in upcoming:
            if upcoming["upcoming_events"]:
                for event in upcoming["upcoming_events"]:
                    # Event card
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        
                        with col1:
                            st.write(f"**{event['title']}**")
                            if event['horse_name']:
                                st.write(f"Horse: {event['horse_name']}")
                            if event.get('provider_name'):
                                st.write(f"Provider: {event['provider_name']}")
                        
                        with col2:
                            event_datetime = datetime.fromisoformat(event['scheduled_date'])
                            st.write(f"📅 {event_datetime.strftime('%b %d, %Y')}")
                            st.write(f"⏰ {event_datetime.strftime('%I:%M %p')}")
                            if event.get('duration_display'):
                                st.write(f"⏱️ {event['duration_display']}")
                        
                        with col3:
                            edit_col, delete_col = st.columns(2)
                            with edit_col:
                                if st.button("✏️", key=f"edit_event_{event['id']}", help="Edit event"):
                                    st.session_state['editing_event_id'] = event['id']
                                    st.rerun()
                            with delete_col:
                                if st.button("🗑️", key=f"delete_event_{event['id']}", help="Delete event"):
                                    st.session_state['deleting_event_id'] = event['id']
                                    st.rerun()
                    
                    st.write("---")
            else:
                st.info("No upcoming events in the next 14 days")
        else:
            st.error("Unable to load upcoming events")
        
        # Handle event editing
        if 'editing_event_id' in st.session_state:
            event_id = st.session_state['editing_event_id']
            st.write("---")
            st.subheader("✏️ Edit Event")
            show_edit_event_form(event_id)
        
        # Handle event deletion
        if 'deleting_event_id' in st.session_state:
            event_id = st.session_state['deleting_event_id']
            st.write("---")
            st.subheader("🗑️ Delete Event")
            
            # Get event details for confirmation
            event_detail = api_request("GET", f"/api/v1/calendar/events/{event_id}")
            
            if event_detail:
                st.warning(f"Are you sure you want to delete the event: **{event_detail['title']}**?")
                st.write(f"📅 Scheduled for: {datetime.fromisoformat(event_detail['scheduled_date']).strftime('%B %d, %Y at %I:%M %p')}")
                
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    if st.button("❌ Cancel", type="secondary"):
                        del st.session_state['deleting_event_id']
                        st.rerun()
                
                with col2:
                    if st.button("🗑️ Delete", type="primary"):
                        result = api_request("DELETE", f"/api/v1/calendar/events/{event_id}")
                        if result:
                            st.success("✅ Event deleted successfully!")
                            del st.session_state['deleting_event_id']
                            st.rerun()
                        else:
                            st.error("Failed to delete event")
            else:
                st.error("Could not load event details")
                if st.button("❌ Cancel"):
                    del st.session_state['deleting_event_id']
                    st.rerun()
    
    with tab3:
        st.subheader("➕ Add New Event")
        show_add_event_form()

def show_add_event_form():
    """Form to add a new event"""
    with st.form("add_event"):
        # Basic event info
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Event Title*", placeholder="e.g., Farrier Visit")
            event_type = st.selectbox("Event Type*", [
                ("veterinary", "🏥 Veterinary"),
                ("farrier", "🔨 Farrier"),
                ("dental", "🦷 Dental"),
                ("supply_delivery", "🚛 Supply Delivery"),
                ("training", "⭐ Training"),
                ("breeding", "💕 Breeding"),
                ("health_treatment", "💊 Health Treatment"),
                ("other", "📅 Other")
            ], format_func=lambda x: x[1])
        
        with col2:
            # Get horses for dropdown
            horses = api_request("GET", "/api/v1/horses/", {"active_only": True})
            horse_options = [("", "No specific horse")] + [(str(h["id"]), h["name"]) for h in horses] if horses else []
            
            selected_horse = st.selectbox("Horse", horse_options, format_func=lambda x: x[1])
            priority = st.selectbox("Priority", ["low", "medium", "high", "urgent"], index=1)
        
        # Date and time
        col1, col2, col3 = st.columns(3)
        
        with col1:
            event_date = st.date_input("Date*", min_value=date.today())
        
        with col2:
            event_time = st.time_input("Time*", value=datetime.now().replace(minute=0, second=0, microsecond=0).time())
        
        with col3:
            duration = st.number_input("Duration (minutes)", min_value=15, max_value=480, value=60, step=15)
        
        # Additional details
        col1, col2 = st.columns(2)
        
        with col1:
            location = st.text_input("Location", placeholder="e.g., Barn stall 5")
            provider_name = st.text_input("Service Provider", placeholder="e.g., Dr. Smith Veterinary")
        
        with col2:
            estimated_cost = st.number_input("Estimated Cost ($)", min_value=0.0, value=0.0, step=10.0)
            weather_dependent = st.checkbox("Weather Dependent")
        
        # Notes
        description = st.text_area("Description", height=100)
        notes = st.text_area("Notes", height=60)
        
        # Submit button
        submitted = st.form_submit_button("📅 Add Event", type="primary")
        
        if submitted:
            if not title or not event_date or not event_time:
                st.error("Title, date, and time are required!")
                return
            
            # Combine date and time
            event_datetime = datetime.combine(event_date, event_time)
            
            # Prepare event data
            event_data = {
                "title": title,
                "description": description if description else None,
                "event_type": event_type[0],
                "scheduled_date": event_datetime.isoformat(),
                "duration_minutes": duration,
                "location": location if location else None,
                "provider_name": provider_name if provider_name else None,
                "priority": priority,
                "estimated_cost": estimated_cost if estimated_cost > 0 else None,
                "horse_id": int(selected_horse[0]) if selected_horse[0] else None,
                "notes": notes if notes else None,
                "weather_dependent": weather_dependent
            }
            
            # Submit to API with organization context
            endpoint = "/api/v1/calendar/events"
            if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
                endpoint = f"/api/v1/calendar/events?organization_id={st.session_state.selected_barn_id}"
            
            result = api_request("POST", endpoint, event_data)
            
            if result:
                st.success(f"✅ Successfully added event: {title}")
                st.balloons()
                st.rerun()
            else:
                st.error("Failed to add event. Please check your inputs and try again.")

def show_edit_event_form(event_id: int):
    """Form to edit an existing event"""
    
    # Get existing event data
    event_data = api_request("GET", f"/api/v1/calendar/events/{event_id}")
    
    if not event_data:
        st.error("Could not load event data")
        if st.button("❌ Cancel Edit"):
            del st.session_state['editing_event_id']
            st.rerun()
        return
    
    # Parse existing data
    existing_datetime = datetime.fromisoformat(event_data['scheduled_date'])
    existing_date = existing_datetime.date()
    existing_time = existing_datetime.time()
    
    with st.form(f"edit_event_{event_id}"):
        st.write(f"**Editing: {event_data['title']}**")
        
        # Basic event info
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Event Title*", value=event_data['title'])
            
            # Event type dropdown with current selection
            event_type_options = [
                ("veterinary", "🏥 Veterinary"),
                ("farrier", "🔨 Farrier"),
                ("dental", "🦷 Dental"),
                ("supply_delivery", "🚛 Supply Delivery"),
                ("training", "⭐ Training"),
                ("breeding", "💕 Breeding"),
                ("health_treatment", "💊 Health Treatment"),
                ("other", "📅 Other")
            ]
            
            # Find current type index
            current_type_index = 0
            for i, (type_val, _) in enumerate(event_type_options):
                if type_val == event_data['event_type']:
                    current_type_index = i
                    break
            
            event_type = st.selectbox("Event Type*", event_type_options, 
                                    format_func=lambda x: x[1], 
                                    index=current_type_index)
        
        with col2:
            # Get horses for dropdown
            horses = api_request("GET", "/api/v1/horses/", {"active_only": True})
            horse_options = [("", "No specific horse")] + [(str(h["id"]), h["name"]) for h in horses] if horses else []
            
            # Find current horse selection
            current_horse_index = 0
            if event_data['horse_id']:
                for i, (horse_id, _) in enumerate(horse_options):
                    if horse_id == str(event_data['horse_id']):
                        current_horse_index = i
                        break
            
            selected_horse = st.selectbox("Horse", horse_options, 
                                        format_func=lambda x: x[1],
                                        index=current_horse_index)
            
            # Priority with current selection
            priority_options = ["low", "medium", "high", "urgent"]
            current_priority_index = priority_options.index(event_data.get('priority', 'medium'))
            priority = st.selectbox("Priority", priority_options, index=current_priority_index)
        
        # Date and time
        col1, col2, col3 = st.columns(3)
        
        with col1:
            event_date = st.date_input("Date*", value=existing_date, min_value=date.today())
        
        with col2:
            event_time = st.time_input("Time*", value=existing_time)
        
        with col3:
            duration = st.number_input("Duration (minutes)", 
                                     min_value=15, max_value=480, 
                                     value=event_data.get('duration_minutes', 60), 
                                     step=15)
        
        # Additional details
        col1, col2 = st.columns(2)
        
        with col1:
            location = st.text_input("Location", value=event_data.get('location', '') or '')
            provider_name = st.text_input("Service Provider", value=event_data.get('provider_name', '') or '')
        
        with col2:
            estimated_cost = st.number_input("Estimated Cost ($)", 
                                           min_value=0.0, 
                                           value=float(event_data.get('estimated_cost', 0) or 0), 
                                           step=10.0)
            weather_dependent = st.checkbox("Weather Dependent", 
                                          value=event_data.get('weather_dependent', False))
        
        # Notes
        description = st.text_area("Description", 
                                 value=event_data.get('description', '') or '', 
                                 height=100)
        notes = st.text_area("Notes", 
                           value=event_data.get('notes', '') or '', 
                           height=60)
        
        # Submit buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submitted = st.form_submit_button("💾 Update Event", type="primary")
        
        with col2:
            cancelled = st.form_submit_button("❌ Cancel")
        
        if cancelled:
            del st.session_state['editing_event_id']
            st.rerun()
        
        if submitted:
            if not title or not event_date or not event_time:
                st.error("Title, date, and time are required!")
                return
            
            # Combine date and time
            event_datetime = datetime.combine(event_date, event_time)
            
            # Prepare event data - only include changed fields
            update_data = {
                "title": title,
                "description": description if description else None,
                "event_type": event_type[0],
                "scheduled_date": event_datetime.isoformat(),
                "duration_minutes": duration,
                "location": location if location else None,
                "provider_name": provider_name if provider_name else None,
                "priority": priority,
                "estimated_cost": estimated_cost if estimated_cost > 0 else None,
                "horse_id": int(selected_horse[0]) if selected_horse[0] else None,
                "notes": notes if notes else None,
                "weather_dependent": weather_dependent
            }
            
            # Submit update to API
            result = api_request("PUT", f"/api/v1/calendar/events/{event_id}", update_data)
            
            if result:
                st.success(f"✅ Successfully updated event: {title}")
                del st.session_state['editing_event_id']
                st.rerun()
            else:
                st.error("Failed to update event. Please check your inputs and try again.")

def show_supplies():
    """Display supply tracking and management"""
    st.header("📦 Supply Tracking & Inventory")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📋 Inventory", "🧾 Receipt Scanner", "📈 Analytics"])
    
    with tab1:
        st.subheader("📊 Supply Dashboard")
        show_supply_dashboard()
    
    with tab2:
        st.subheader("📋 Inventory Management")
        show_inventory_management()
    
    with tab3:
        st.subheader("🧾 AI Receipt Scanner")
        show_receipt_scanner()
    
    with tab4:
        st.subheader("📈 Supply Analytics")
        show_supply_analytics()

def show_supply_dashboard():
    """Display supply dashboard with key metrics"""
    
    # Get dashboard data
    # Get dashboard data with organization filter
    dashboard_params = {}
    if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
        dashboard_params["organization_id"] = st.session_state.selected_barn_id
    
    dashboard_data = api_request("GET", "/api/v1/supplies/dashboard", dashboard_params)
    
    if not dashboard_data:
        st.error("Unable to load dashboard data")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Supplies", dashboard_data.get("total_supplies", 0))
    
    with col2:
        low_stock = dashboard_data.get("low_stock_count", 0)
        st.metric("Low Stock Items", low_stock, delta=None if low_stock == 0 else f"⚠️")
    
    with col3:
        out_stock = dashboard_data.get("out_of_stock_count", 0)
        st.metric("Out of Stock", out_stock, delta=None if out_stock == 0 else f"🚨")
    
    with col4:
        inventory_value = dashboard_data.get("total_inventory_value", 0)
        st.metric("Inventory Value", f"${inventory_value:,.2f}")
    
    # Low stock alerts
    low_stock_items = dashboard_data.get("low_stock_items", [])
    if low_stock_items:
        st.subheader("🚨 Low Stock Alerts")
        
        for item in low_stock_items:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{item['name']}**")
                st.write(f"Current: {item['current_stock']} | Reorder at: {item['reorder_point']}")
            
            with col2:
                days_left = item.get('estimated_days_remaining')
                if days_left:
                    st.write(f"📅 {days_left} days left")
                else:
                    st.write("📅 Usage unknown")
            
            with col3:
                if st.button(f"Reorder", key=f"reorder_{item['id']}"):
                    st.info("Reorder functionality coming soon!")
        
        st.write("---")
    
    # Recent transactions
    recent_transactions = dashboard_data.get("recent_transactions", [])
    if recent_transactions:
        st.subheader("📋 Recent Purchases")
        
        for transaction in recent_transactions:
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**{transaction['vendor_name']}**")
                st.write(f"Status: {transaction['status'].title()}")
            
            with col2:
                st.write(f"📅 {transaction['purchase_date']}")
                total_amount = transaction['total_amount']
                if total_amount is not None:
                    st.write(f"💰 ${total_amount:.2f}")
                else:
                    st.write("💰 No total available")
            
            with col3:
                if st.button("View", key=f"view_transaction_{transaction['id']}"):
                    st.session_state[f"viewing_transaction_{transaction['id']}"] = True
                    st.rerun()
        
        # Check if any transaction is being viewed
        for transaction in recent_transactions:
            if st.session_state.get(f"viewing_transaction_{transaction['id']}"):
                show_transaction_details(transaction['id'])
                break

def show_transaction_details(transaction_id: int):
    """Display detailed transaction view with editing capabilities"""
    
    # Get transaction details
    transaction_data = api_request("GET", f"/api/v1/supplies/transactions/{transaction_id}")
    
    if not transaction_data:
        st.error("Failed to load transaction details")
        return
    
    st.subheader(f"📋 Transaction Details - {transaction_data.get('vendor_name', 'Unknown Vendor')}")
    
    # Close button
    if st.button("✖️ Close", key=f"close_transaction_{transaction_id}"):
        if f"viewing_transaction_{transaction_id}" in st.session_state:
            del st.session_state[f"viewing_transaction_{transaction_id}"]
        st.rerun()
    
    # Transaction info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Vendor:**", transaction_data.get('vendor_name', 'Unknown'))
        st.write("**Date:**", transaction_data.get('purchase_date', 'Unknown'))
    
    with col2:
        total_amount = transaction_data.get('total_amount')
        if total_amount:
            st.write("**Total:**", f"${total_amount:.2f}")
        else:
            st.write("**Total:**", "No total available")
        st.write("**Status:**", transaction_data.get('status', 'Unknown').title())
    
    with col3:
        st.write("**Confidence:**", f"{transaction_data.get('ai_confidence_score', 0):.1%}")
        if transaction_data.get('manual_review_required'):
            st.warning("⚠️ Manual review required")
    
    # AI processing notes
    if transaction_data.get('ai_processing_notes'):
        st.info(f"**AI Notes:** {transaction_data['ai_processing_notes']}")
    
    st.write("---")
    
    # Line items
    items = transaction_data.get('items', [])
    if items:
        st.subheader("📦 Transaction Items")
        
        for i, item in enumerate(items):
            with st.expander(f"{item.get('item_description', 'Unknown Item')} - Qty: {item.get('quantity', 0)}"):
                # Editable fields
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Description:**", item.get('item_description', 'Unknown'))
                    st.write("**Quantity:**", item.get('quantity', 0))
                    if item.get('brand'):
                        st.write("**Brand:**", item['brand'])
                
                with col2:
                    unit_cost = st.number_input(
                        "Unit Cost ($)", 
                        value=float(item.get('unit_cost') or 0),
                        min_value=0.0,
                        step=0.01,
                        key=f"unit_cost_{transaction_id}_{i}"
                    )
                    total_cost = st.number_input(
                        "Total Cost ($)", 
                        value=float(item.get('total_cost') or 0),
                        min_value=0.0,
                        step=0.01,
                        key=f"total_cost_{transaction_id}_{i}"
                    )
                
                with col3:
                    st.write("**Confidence:**", f"{item.get('ai_confidence', 0):.1%}")
                    if item.get('product_code'):
                        st.write("**Product Code:**", item['product_code'])
                    
                    # Update button
                    if st.button(f"💾 Update Item", key=f"update_item_{transaction_id}_{i}"):
                        # Here you could add API call to update the transaction item
                        st.success("Update functionality coming soon!")
    else:
        st.warning("No items found for this transaction")
    
    st.write("---")

def show_inventory_management():
    """Display and manage inventory items"""
    
    # Search and filter controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_term = st.text_input("🔍 Search supplies", placeholder="Name, brand, category...")
    
    with col2:
        category_options = [
            ("", "All Categories"),
            ("feed_nutrition", "🌾 Feed & Nutrition"),
            ("bedding", "🛏️ Bedding"),
            ("health_medical", "🏥 Health & Medical"),
            ("tack_equipment", "🎒 Tack & Equipment"),
            ("facility_maintenance", "🔧 Facility Maintenance"),
            ("grooming", "✨ Grooming")
        ]
        selected_category = st.selectbox("Category", category_options, format_func=lambda x: x[1])
    
    with col3:
        stock_filter = st.selectbox("Stock Level", ["All Items", "Low Stock Only", "In Stock Only"])
    
    with col4:
        add_supply_clicked = st.button("➕ Add New Supply", key="add_supply_btn")
        if add_supply_clicked:
            st.session_state['adding_supply'] = True
            st.rerun()
    
    # Fetch supplies with filters
    params = {}
    if search_term:
        params["search"] = search_term
    if selected_category[0]:
        params["category"] = selected_category[0]
    if stock_filter == "Low Stock Only":
        params["low_stock_only"] = True
    
    # Add organization_id if available
    if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
        params["organization_id"] = st.session_state.selected_barn_id
    
    supplies = api_request("GET", "/api/v1/supplies/", params)
    
    if not supplies:
        st.info("No supplies found or unable to load data")
        return
    
    # Display supplies
    st.write(f"**Found {len(supplies)} supplies**")
    
    for supply in supplies:
        # Stock status indicator
        if supply['current_stock'] <= 0:
            status = "🚨"  # Out of stock
            status_color = "#dc3545"  # Red
        elif supply['is_low_stock']:
            status = "⚠️"  # Low stock
            status_color = "#ffc107"  # Yellow
        else:
            status = "✅"  # Good stock
            status_color = "#28a745"  # Green

        # Prepare all the data
        brand_info = f"Brand: {supply['brand']}" if supply['brand'] else ""
        category_info = f"Category: {supply['category'].replace('_', ' ').title()}"
        stock_info = f"📦 Stock: {supply['current_stock']} {supply['unit_type']}"
        reorder_info = f"🔄 Reorder at: {supply['reorder_point']}" if supply['reorder_point'] else ""
        days_info = f"📅 {supply['estimated_days_remaining']} days left" if supply.get('estimated_days_remaining') else ""
        cost_info = f"💰 ${supply['last_cost_per_unit']:.2f} per {supply['unit_type'][:-1]}" if supply['last_cost_per_unit'] else ""
        location_info = f"📍 {supply['storage_location']}" if supply['storage_location'] else ""

        # Build HTML parts conditionally
        brand_html = f'<p style="margin: 3px 0; color: #666; font-size: 0.9em;">{brand_info}</p>' if brand_info else ''
        reorder_html = f'<p style="margin: 3px 0; color: #666; font-size: 0.9em;">{reorder_info}</p>' if reorder_info else ''
        days_html = f'<p style="margin: 3px 0; color: #4A90E2; font-size: 0.9em;">{days_info}</p>' if days_info else ''
        cost_html = f'<p style="margin: 3px 0; color: #000000; font-size: 0.9em; font-weight: 500;">{cost_info}</p>' if cost_info else ''
        location_html = f'<p style="margin: 3px 0; color: #666; font-size: 0.9em;">{location_info}</p>' if location_info else ''

        with st.container():
            card_col1, card_col2 = st.columns([3, 1])

            with card_col1:
                st.markdown(f"""
                <div style="background-color: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 10px 0;">
                    <h4 style="margin: 0 0 10px 0; color: #000;">{status} {supply['name']}</h4>
                    <p style="margin: 5px 0; color: #666; font-size: 0.9em;">{category_info}</p>
                    <p style="margin: 5px 0; color: #000; font-weight: 500;">{stock_info}</p>
                </div>
                """, unsafe_allow_html=True)

            with card_col2:
                st.write("")  # Spacing
                if cost_info:
                    st.write(cost_info)
                if location_info:
                    st.write(location_info)

        # Edit button below the card
        col1, col2, col3 = st.columns([1, 1, 8])
        with col1:
            if st.button("✏️ Edit", key=f"edit_supply_{supply['id']}", help="Edit supply"):
                st.session_state[f'editing_supply_{supply["id"]}'] = True
                st.rerun()
    
    # Handle adding new supply
    if 'adding_supply' in st.session_state:
        st.subheader("➕ Add New Supply")
        show_add_supply_form()
    
    # Handle editing supplies
    for key in st.session_state.keys():
        if key.startswith('editing_supply_'):
            supply_id = int(key.split('_')[2])
            st.subheader("✏️ Edit Supply")
            show_edit_supply_form(supply_id)
            break

def show_add_supply_form():
    """Form to add a new supply"""
    
    with st.form("add_supply"):
        # Basic information
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Supply Name*", placeholder="e.g., Premium Timothy Hay")
            category = st.selectbox("Category*", [
                ("feed_nutrition", "🌾 Feed & Nutrition"),
                ("bedding", "🛏️ Bedding"),
                ("health_medical", "🏥 Health & Medical"),
                ("tack_equipment", "🎒 Tack & Equipment"),
                ("facility_maintenance", "🔧 Facility Maintenance"),
                ("grooming", "✨ Grooming"),
                ("other", "📦 Other")
            ], format_func=lambda x: x[1])
            
            brand = st.text_input("Brand", placeholder="e.g., Purina")
        
        with col2:
            unit_type = st.selectbox("Unit Type*", [
                ("bags", "Bags"),
                ("bales", "Bales"),
                ("pounds", "Pounds"),
                ("gallons", "Gallons"),
                ("bottles", "Bottles"),
                ("boxes", "Boxes"),
                ("each", "Each"),
                ("yards", "Yards"),
                ("rolls", "Rolls")
            ], format_func=lambda x: x[1])
            
            current_stock = st.number_input("Current Stock", min_value=0.0, value=0.0, step=1.0)
            reorder_point = st.number_input("Reorder Point", min_value=0.0, value=0.0, step=1.0)
        
        # Additional details
        col1, col2 = st.columns(2)
        
        with col1:
            last_cost = st.number_input("Cost per Unit ($)", min_value=0.0, value=0.0, step=0.01)
            storage_location = st.text_input("Storage Location", placeholder="e.g., Barn A, Shelf 2")
        
        with col2:
            monthly_usage = st.number_input("Estimated Monthly Usage", min_value=0.0, value=0.0, step=1.0)
            expiration_tracking = st.checkbox("Track Expiration Dates")
        
        description = st.text_area("Description", placeholder="Additional details about this supply...")
        
        # Submit buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submitted = st.form_submit_button("💾 Add Supply", type="primary")
        
        with col2:
            cancelled = st.form_submit_button("❌ Cancel")
        
        if cancelled:
            del st.session_state['adding_supply']
            st.rerun()
        
        if submitted:
            if not name or not category or not unit_type:
                st.error("Name, category, and unit type are required!")
                return
            
            supply_data = {
                "name": name,
                "description": description if description else None,
                "category": category[0],
                "brand": brand if brand else None,
                "unit_type": unit_type[0],
                "current_stock": current_stock,
                "reorder_point": reorder_point if reorder_point > 0 else None,
                "last_cost_per_unit": last_cost if last_cost > 0 else None,
                "average_cost_per_unit": last_cost if last_cost > 0 else None,
                "estimated_monthly_usage": monthly_usage if monthly_usage > 0 else None,
                "storage_location": storage_location if storage_location else None,
                "expiration_tracking": expiration_tracking
            }
            
            # Submit to API with organization context
            endpoint = "/api/v1/supplies/"
            if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
                endpoint = f"/api/v1/supplies/?organization_id={st.session_state.selected_barn_id}"
            
            result = api_request("POST", endpoint, supply_data)
            
            if result:
                st.success(f"✅ Successfully added {name}!")
                del st.session_state['adding_supply']
                st.balloons()
                st.rerun()
            else:
                st.error("Failed to add supply. Please check your inputs and try again.")

def show_edit_supply_form(supply_id: int):
    """Form to edit an existing supply"""
    
    # Get existing supply data
    supply_data = api_request("GET", f"/api/v1/supplies/{supply_id}")
    
    if not supply_data:
        st.error("Could not load supply data")
        if st.button("❌ Cancel Edit"):
            del st.session_state[f'editing_supply_{supply_id}']
            st.rerun()
        return
    
    with st.form(f"edit_supply_{supply_id}"):
        st.write(f"**Editing: {supply_data['name']}**")
        
        # Basic information
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Supply Name*", value=supply_data['name'])
            
            # Category selection with current value
            category_options = [
                ("feed_nutrition", "🌾 Feed & Nutrition"),
                ("bedding", "🛏️ Bedding"),
                ("health_medical", "🏥 Health & Medical"),
                ("tack_equipment", "🎒 Tack & Equipment"),
                ("facility_maintenance", "🔧 Facility Maintenance"),
                ("grooming", "✨ Grooming"),
                ("other", "📦 Other")
            ]
            
            current_category_index = 0
            for i, (cat_val, _) in enumerate(category_options):
                if cat_val == supply_data['category']:
                    current_category_index = i
                    break
            
            category = st.selectbox("Category*", category_options, 
                                  format_func=lambda x: x[1], 
                                  index=current_category_index)
            
            brand = st.text_input("Brand", value=supply_data.get('brand', '') or '')
        
        with col2:
            # Unit type selection
            unit_options = [
                ("bags", "Bags"),
                ("bales", "Bales"),
                ("pounds", "Pounds"),
                ("gallons", "Gallons"),
                ("bottles", "Bottles"),
                ("boxes", "Boxes"),
                ("each", "Each"),
                ("yards", "Yards"),
                ("rolls", "Rolls")
            ]
            
            current_unit_index = 0
            for i, (unit_val, _) in enumerate(unit_options):
                if unit_val == supply_data['unit_type']:
                    current_unit_index = i
                    break
            
            unit_type = st.selectbox("Unit Type*", unit_options,
                                   format_func=lambda x: x[1],
                                   index=current_unit_index)
            
            current_stock = st.number_input("Current Stock", 
                                          min_value=0.0, 
                                          value=float(supply_data.get('current_stock', 0)), 
                                          step=1.0)
            
            reorder_point = st.number_input("Reorder Point", 
                                          min_value=0.0, 
                                          value=float(supply_data.get('reorder_point', 0) or 0), 
                                          step=1.0)
        
        # Additional details
        col1, col2 = st.columns(2)
        
        with col1:
            last_cost = st.number_input("Cost per Unit ($)", 
                                      min_value=0.0, 
                                      value=float(supply_data.get('last_cost_per_unit', 0) or 0), 
                                      step=0.01)
            
            storage_location = st.text_input("Storage Location", 
                                           value=supply_data.get('storage_location', '') or '')
        
        with col2:
            monthly_usage = st.number_input("Estimated Monthly Usage", 
                                          min_value=0.0, 
                                          value=float(supply_data.get('estimated_monthly_usage', 0) or 0), 
                                          step=1.0)
            
            expiration_tracking = st.checkbox("Track Expiration Dates",
                                            value=supply_data.get('expiration_tracking', False))
        
        description = st.text_area("Description", 
                                 value=supply_data.get('description', '') or '')
        
        # Submit buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submitted = st.form_submit_button("💾 Update Supply", type="primary")
        
        with col2:
            cancelled = st.form_submit_button("❌ Cancel")
        
        if cancelled:
            del st.session_state[f'editing_supply_{supply_id}']
            st.rerun()
        
        if submitted:
            if not name or not category or not unit_type:
                st.error("Name, category, and unit type are required!")
                return
            
            update_data = {
                "name": name,
                "description": description if description else None,
                "category": category[0],
                "brand": brand if brand else None,
                "unit_type": unit_type[0],
                "current_stock": current_stock,
                "reorder_point": reorder_point if reorder_point > 0 else None,
                "last_cost_per_unit": last_cost if last_cost > 0 else None,
                "average_cost_per_unit": last_cost if last_cost > 0 else None,
                "estimated_monthly_usage": monthly_usage if monthly_usage > 0 else None,
                "storage_location": storage_location if storage_location else None,
                "expiration_tracking": expiration_tracking
            }
            
            result = api_request("PUT", f"/api/v1/supplies/{supply_id}", update_data)
            
            if result:
                st.success(f"✅ Successfully updated {name}!")
                del st.session_state[f'editing_supply_{supply_id}']
                st.rerun()
            else:
                st.error("Failed to update supply. Please check your inputs and try again.")

def show_receipt_scanner():
    """AI-powered receipt scanner"""
    
    st.write("📷 Upload a receipt image and let AI automatically extract items and costs!")
    
    # Receipt upload
    uploaded_receipt = st.file_uploader(
        "Choose receipt image",
        type=['png', 'jpg', 'jpeg'],
        help="Upload a clear photo of your barn supply receipt"
    )
    
    if uploaded_receipt is not None:
        # Show image preview
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(uploaded_receipt, caption="Receipt Preview", width=300)
        
        with col2:
            # Optional processing hints
            vendor_hint = st.text_input("Vendor Name (optional)", 
                                      placeholder="e.g., Tractor Supply Co",
                                      help="Help AI identify the vendor")
            
            expected_total = st.number_input("Expected Total (optional)", 
                                           min_value=0.0, 
                                           value=0.0, 
                                           step=0.01,
                                           help="Help validate the extracted total")
            
            if st.button("🤖 Process Receipt with AI", type="primary"):
                with st.spinner("🔍 Analyzing receipt with AI..."):
                    try:
                        # Prepare multipart form data
                        import requests
                        
                        # Prepare the file data
                        files = {"receipt_image": (uploaded_receipt.name, uploaded_receipt.getvalue(), uploaded_receipt.type)}
                        
                        # Prepare form data
                        data = {}
                        if vendor_hint:
                            data["vendor_hint"] = vendor_hint
                        if expected_total > 0:
                            data["expected_total"] = expected_total
                        
                        # Add organization context
                        if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
                            data["organization_id"] = st.session_state.selected_barn_id
                        
                        # Make the request directly with requests
                        response = requests.post(
                            f"{API_BASE_URL}/api/v1/supplies/transactions/process-receipt",
                            files=files,
                            data=data
                        )
                        
                        if response.status_code == 201:
                            result = response.json()
                        else:
                            result = {"success": False, "error": f"Server error: {response.status_code}"}
                        
                        if result and result.get("success"):
                            st.success("🎉 Receipt processed successfully!")
                            
                            # Store results in session state for adding to inventory
                            st.session_state['processed_receipt'] = result
                            st.session_state['show_extracted_items'] = True
                    
                    except Exception as e:
                        st.error(f"❌ Error processing receipt: {str(e)}")
                        st.info("Make sure the image is clear and contains a valid receipt")
            
            # Display extracted items if they exist in session state
            if st.session_state.get('show_extracted_items') and st.session_state.get('processed_receipt'):
                result = st.session_state['processed_receipt']
                
                # Display extracted information
                st.subheader("📋 Extracted Items")
                
                items = result.get("line_items", [])
                if items:
                    for i, item in enumerate(items):
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        
                        with col1:
                            st.write(f"**{item.get('description', 'Unknown Item')}**")
                            if item.get('category'):
                                st.write(f"*Category: {item['category']}*")
                        
                        with col2:
                            st.write(f"Qty: {item.get('quantity', 1)}")
                        
                        with col3:
                            cost = item.get('unit_price') or item.get('total_price') or 0
                            if cost:
                                st.write(f"${cost:.2f}")
                            else:
                                st.write("No price")
                        
                        with col4:
                            if st.button("➕", key=f"add_item_{i}", help="Add to inventory"):
                                # Map package_size to proper unit_type
                                package_size = item.get('package_size', 'each').lower()
                                unit_type_map = {
                                    'bag': 'bags',
                                    'bale': 'bales', 
                                    'pound': 'pounds',
                                    'lb': 'pounds',
                                    'gallon': 'gallons',
                                    'bottle': 'bottles',
                                    'box': 'boxes',
                                    'each': 'each',
                                    'yard': 'yards',
                                    'roll': 'rolls'
                                }
                                unit_type = unit_type_map.get(package_size, 'each')
                                
                                # Add individual item to inventory
                                supply_data = {
                                    "name": item.get('description', 'Receipt Item'),
                                    "category": item.get('category', 'other'),
                                    "unit_type": unit_type,
                                    "current_stock": item.get('quantity', 1),
                                    "last_cost_per_unit": item.get('unit_price') or item.get('total_price')
                                }
                                
                                # Add to inventory with organization context
                                endpoint = "/api/v1/supplies/"
                                if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
                                    endpoint = f"/api/v1/supplies/?organization_id={st.session_state.selected_barn_id}"
                                
                                add_result = api_request("POST", endpoint, supply_data)
                                if add_result:
                                    st.success(f"✅ Added {item.get('description')} to inventory!")
                                else:
                                    st.error(f"Failed to add {item.get('description')}")
                    
                    # Summary and Add All button (outside the item loop)
                    st.write("---")
                    total_amount = result.get('total_amount')
                    if total_amount:
                        st.write(f"**Total:** ${total_amount:.2f}")
                    else:
                        st.write("**Total:** No total available (delivery receipt)")
                    if result.get('vendor_name'):
                        st.write(f"**Vendor:** {result['vendor_name']}")
                    if result.get('purchase_date'):
                        st.write(f"**Date:** {result['purchase_date']}")
                    if result.get('notes'):
                        st.info(f"**Notes:** {result['notes']}")
                    
                    # Add all items button
                    if st.button("📦 Add All Items to Inventory"):
                        success_count = 0
                        error_count = 0
                        updated_count = 0
                        
                        for item in items:
                            # Map package_size to proper unit_type
                            package_size = item.get('package_size', 'each').lower()
                            unit_type_map = {
                                'bag': 'bags',
                                'bags': 'bags',
                                'bale': 'bales',
                                'bales': 'bales', 
                                'pound': 'pounds',
                                'pounds': 'pounds',
                                'lb': 'pounds',
                                'gallon': 'gallons',
                                'gallons': 'gallons',
                                'bottle': 'bottles',
                                'bottles': 'bottles',
                                'box': 'boxes',
                                'boxes': 'boxes',
                                'each': 'each',
                                'yard': 'yards',
                                'yards': 'yards',
                                'roll': 'rolls',
                                'rolls': 'rolls'
                            }
                            unit_type = unit_type_map.get(package_size, 'each')
                            
                            supply_data = {
                                "name": item.get('description', 'Receipt Item'),
                                "category": item.get('category', 'other'),
                                "unit_type": unit_type, 
                                "current_stock": item.get('quantity', 1),
                                "last_cost_per_unit": item.get('unit_price') or item.get('total_price')
                            }
                            
                            # First, try to create new supply item
                            endpoint = "/api/v1/supplies/"
                            if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
                                endpoint = f"/api/v1/supplies/?organization_id={st.session_state.selected_barn_id}"
                            
                            # Use specialized API request that handles 409 conflicts gracefully
                            add_result = api_request_with_conflict_handling("POST", endpoint, supply_data)
                            
                            if add_result:
                                # New item created successfully
                                success_count += 1
                            elif add_result is None:
                                # Item might already exist, try to find it and add stock
                                # Get existing supplies to find matching item
                                search_endpoint = "/api/v1/supplies/"
                                if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
                                    search_endpoint = f"/api/v1/supplies/?organization_id={st.session_state.selected_barn_id}"
                                
                                existing_supplies = api_request("GET", search_endpoint, {"search": item.get('description', '')})
                                
                                # Find matching supply by name and category
                                matching_supply = None
                                if existing_supplies:
                                    for existing in existing_supplies:
                                        if (existing.get('name', '').lower() == supply_data['name'].lower() and 
                                            existing.get('category', '').lower() == supply_data['category'].lower()):
                                            matching_supply = existing
                                            break
                                
                                if matching_supply:
                                    # Add stock using stock movement
                                    movement_data = {
                                        "supply_id": matching_supply['id'],
                                        "quantity_change": item.get('quantity', 1),
                                        "movement_type": "purchase",
                                        "reason": "Receipt upload",
                                        "unit_cost": item.get('unit_price') or item.get('total_price')
                                    }
                                    
                                    movement_result = api_request("POST", "/api/v1/supplies/stock-movements", movement_data)
                                    if movement_result:
                                        updated_count += 1
                                    else:
                                        error_count += 1
                                else:
                                    error_count += 1
                            else:
                                # Other API error occurred
                                error_count += 1
                        
                        # Show results
                        if success_count > 0 or updated_count > 0:
                            st.balloons()
                            message_parts = []
                            if success_count > 0:
                                message_parts.append(f"{success_count} new items added")
                            if updated_count > 0:
                                message_parts.append(f"{updated_count} existing items updated")
                            st.success(f"✅ {' and '.join(message_parts)} to inventory!")
                        
                        if error_count > 0:
                            st.warning(f"⚠️ {error_count} items could not be processed")
                        
                        if success_count == 0 and updated_count == 0:
                            st.error("Failed to add any items to inventory")
                else:
                    st.warning("No items found in receipt")

def show_supply_analytics():
    """Display supply analytics and trends"""
    
    st.write("📊 Supply analytics and spending trends coming soon!")
    
    # Placeholder charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Monthly Spending")
        # This would show a real chart
        st.info("Chart showing monthly supply spending trends")
    
    with col2:
        st.subheader("📦 Stock Levels")
        # This would show current stock levels
        st.info("Chart showing current stock levels by category")
    
    st.subheader("🔄 Reorder Recommendations")
    st.info("AI-powered reorder recommendations based on usage patterns")

def show_reports():
    """Display reports and analytics"""
    st.header("📊 Reports & Analytics")
    st.info("Reports and analytics will be implemented in future phases.")

if __name__ == "__main__":
    main()

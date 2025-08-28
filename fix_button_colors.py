with open('frontend/app.py', 'r') as f:
    content = f.read()

# Replace the CSS with more specific button styling
old_css_section = '''# Custom CSS matching button designs
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stSelectbox > div > div {
        background-color: #f5f5f0;
    }
    
    /* Default buttons - brown/orange like View and Edit */
    .stButton > button {
        background-color: #B8860B;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: background-color 0.3s;
    }
    .stButton > button:hover {
        background-color: #8B4513;
    }
    
    /* AI buttons - sage green */
    .stButton button[key*="ai_"], 
    .stButton button[key*="profile_ai"] {
        background-color: #8B9A5B !important;
        color: white !important;
    }
    .stButton button[key*="ai_"]:hover,
    .stButton button[key*="profile_ai"]:hover {
        background-color: #6B7A3B !important;
    }
    
    /* Primary buttons (AI assistant buttons) */
    .stButton > button[kind="primary"] {
        background-color: #8B9A5B !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #6B7A3B !important;
    }
    
    .sidebar .sidebar-content {
        background-color: #f8f5f0;
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e8e0 100%);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #D2691E;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)'''

new_css_section = '''# Custom CSS matching button designs
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stSelectbox > div > div {
        background-color: #f5f5f0;
    }
    
    /* Default buttons - brown/orange like View and Edit */
    .stButton > button {
        background-color: #B8860B;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: background-color 0.3s;
    }
    .stButton > button:hover {
        background-color: #8B4513;
    }
    
    .sidebar .sidebar-content {
        background-color: #f8f5f0;
    }
</style>
""", unsafe_allow_html=True)'''

content = content.replace(old_css_section, new_css_section)

# Now let's modify the buttons to use different approaches for different colors
# Replace Ask AI buttons to use type="primary" and add custom CSS for primary buttons

# Fix the card AI buttons
old_ai_button_card = '''if st.button("Ask AI", key=f"ai_{horse['id']}", use_container_width=True):'''
new_ai_button_card = '''# Add green styling for AI button
                    st.markdown("""
                    <style>
                    .stButton > button[data-testid*="ai_"] {
                        background-color: #8B9A5B !important;
                        color: white !important;
                    }
                    .stButton > button[data-testid*="ai_"]:hover {
                        background-color: #6B7A3B !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    if st.button("🤖 Ask AI", key=f"ai_{horse['id']}", use_container_width=True):'''

content = content.replace(old_ai_button_card, new_ai_button_card)

# Fix the profile AI button
old_ai_button_profile = '''if st.button("Ask AI", key="profile_ai", use_container_width=True):'''
new_ai_button_profile = '''st.markdown("""
                <style>
                div[data-testid="stButton"]:has(button[key="profile_ai"]) button {
                    background-color: #8B9A5B !important;
                    color: white !important;
                }
                div[data-testid="stButton"]:has(button[key="profile_ai"]) button:hover {
                    background-color: #6B7A3B !important;
                }
                </style>
                """, unsafe_allow_html=True)
                if st.button("🤖 Ask AI", key="profile_ai", use_container_width=True):'''

content = content.replace(old_ai_button_profile, new_ai_button_profile)

# Add icons back to distinguish the buttons
content = content.replace('if st.button("View", key=f"view_{horse[\'id\']}"', 'if st.button("👁️ View", key=f"view_{horse[\'id\']}"')
content = content.replace('if st.button("Edit", key=f"edit_{horse[\'id\']}"', 'if st.button("✏️ Edit", key=f"edit_{horse[\'id\']}"')
content = content.replace('if st.button("Edit", key="profile_edit"', 'if st.button("✏️ Edit", key="profile_edit"')
content = content.replace('if st.button("Back", key="profile_back"', 'if st.button("🏠 Back", key="profile_back"')

with open('frontend/app.py', 'w' as f:
    f.write(content)

print("Fixed button colors with more specific targeting")

#!/usr/bin/env python3
"""
Script to fix the AI navigation logic in frontend/app.py
"""

import re

def fix_navigation():
    # Read the current file
    with open('frontend/app.py', 'r') as f:
        content = f.read()
    
    # Find the problematic section and replace it
    # Look for the existing else block
    pattern = r'(\s+)else:\s*\n(\s+)page = st\.sidebar\.selectbox\(\s*\n(\s+)"Choose a page:",\s*\n(\s+)\["Horse Directory", "Add New Horse", "🤖 AI Assistant", "Reports"\]\s*\n(\s+)\)'
    
    # Replacement with proper indentation (using 4 spaces per level)
    replacement = '''    else:
        # Check if AI assistant should be auto-selected
        if 'ai_horse_id' in st.session_state and st.session_state.ai_horse_id:
            page = "🤖 AI Assistant"
        else:
            page = st.sidebar.selectbox(
                "Choose a page:",
                ["Horse Directory", "Add New Horse", "🤖 AI Assistant", "Reports"]
            )'''
    
    # Try to find and replace the pattern
    new_content = re.sub(pattern, replacement, content)
    
    # If the regex didn't work, try a simpler approach
    if new_content == content:
        # Look for a simpler pattern
        simple_pattern = r'else:\s*\n\s*page = st\.sidebar\.selectbox\(\s*\n\s*"Choose a page:",\s*\n\s*\["Horse Directory", "Add New Horse", "🤖 AI Assistant", "Reports"\]\s*\n\s*\)'
        
        new_content = re.sub(simple_pattern, replacement, content)
    
    # If still no change, do manual replacement by finding the line
    if new_content == content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'Choose a page:' in line and 'selectbox' in lines[i-1]:
                # Found the target, replace this section
                # Find the start of the else block
                start_idx = i - 2
                while start_idx >= 0 and 'else:' not in lines[start_idx]:
                    start_idx -= 1
                
                # Find the end (closing parenthesis)
                end_idx = i + 3
                while end_idx < len(lines) and ')' not in lines[end_idx]:
                    end_idx += 1
                
                if start_idx >= 0:
                    # Replace the section
                    replacement_lines = replacement.split('\n')
                    lines[start_idx:end_idx+1] = replacement_lines
                    new_content = '\n'.join(lines)
                break
    
    # Write the fixed content back
    with open('frontend/app.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Fixed AI navigation logic in frontend/app.py")
    print("🔄 Please refresh your browser to test the fix!")

if __name__ == "__main__":
    fix_navigation()

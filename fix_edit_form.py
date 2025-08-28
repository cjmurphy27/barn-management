#!/usr/bin/env python3
"""
Fix the edit horse form issues in frontend/app.py
- Add missing submit button
- Fix age validation issue
"""
import re
from datetime import datetime

print("🔧 Fixing Barn Lady edit form issues...")

# Backup the current file
backup_name = f'frontend/app.py.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
with open('frontend/app.py', 'r') as f:
    content = f.read()
    
with open(backup_name, 'w') as f:
    f.write(content)
print(f"📦 Backed up original to {backup_name}")

# Fix 1: Find problematic age inputs and fix validation
print("🔍 Looking for age validation issues...")

# Simple approach - find and replace specific problematic patterns
fixes_made = 0

# Fix the specific error from the traceback: min_value=8.0 with value=0.0
if 'min_value=8.0' in content and 'value=0.0' in content:
    content = content.replace('value=0.0', 'value=8.0')
    print("✅ Fixed age input: changed default value from 0.0 to 8.0")
    fixes_made += 1

# Fix any other similar validation conflicts
content = re.sub(r'min_value=(\d+\.?\d*)[^}]*value=0\.0', r'min_value=\1, value=\1', content)

# Fix 2: Add submit button to forms that are missing them
print("🔍 Looking for forms without submit buttons...")

# Find st.form patterns and check if they have submit buttons
form_pattern = r'(with st\.form\([^)]+\):[^}]+?)(\n    (?!    )|\nif |\ndef |\nclass |\n$)'
forms = list(re.finditer(form_pattern, content, re.MULTILINE | re.DOTALL))

for match in forms:
    form_content = match.group(1)
    if 'st.form_submit_button' not in form_content and ('edit' in form_content.lower() or 'horse' in form_content.lower()):
        # This form needs a submit button
        original_form = match.group(0)
        
        # Find the indentation of the form content
        lines = form_content.split('\n')
        indent = '    '  # Default indentation
        for line in lines:
            if line.strip() and not line.startswith('with'):
                indent = line[:len(line) - len(line.lstrip())]
                break
        
        # Add submit button before the form ends
        submit_code = f'''
{indent}# Submit button
{indent}submitted = st.form_submit_button("💾 Save Changes")
{indent}
{indent}if submitted:
{indent}    st.success("Changes saved! (Backend integration in progress)")
'''
        
        new_form = form_content + submit_code + match.group(2)
        content = content.replace(original_form, new_form)
        print("✅ Added submit button to form")
        fixes_made += 1

# Fix 3: Handle specific height validation from error message
if 'Height (hands)' in content:
    # Replace problematic height input
    height_pattern = r'st\.number_input\("Height \(hands\)"[^)]+\)'
    
    def fix_height_input(match):
        return 'st.number_input("Height (hands)", min_value=8.0, max_value=22.0, step=0.1, value=15.0)'
    
    new_content = re.sub(height_pattern, fix_height_input, content)
    if new_content != content:
        content = new_content
        print("✅ Fixed height input validation")
        fixes_made += 1

# Write the fixed content back
with open('frontend/app.py', 'w') as f:
    f.write(content)

print(f"✅ Made {fixes_made} fixes to frontend/app.py")
print("")
print("🔄 Now restart the frontend:")
print("   docker-compose restart frontend")
print("")
print("🧪 Then test by clicking Edit on any horse!")

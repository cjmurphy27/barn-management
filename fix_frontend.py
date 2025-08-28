#!/usr/bin/env python3

# Read the file
with open('frontend/app.py', 'r') as f:
    lines = f.readlines()

# Find the line with the AI navigation logic and fix it
for i, line in enumerate(lines):
    if 'ai_horse_id' in line and 'session_state' in line:
        # We found the problematic area, let's replace this entire section
        # First find the start (the else: line)
        start = i
        while start > 0 and 'else:' not in lines[start]:
            start -= 1
        
        # Find the end (the closing parenthesis of selectbox)
        end = i
        while end < len(lines) and not (')' in lines[end] and 'selectbox' in ''.join(lines[max(0,end-5):end+1])):
            end += 1
        
        # Replace the entire section with working code
        new_section = [
            "    else:\n",
            "        if 'ai_horse_id' in st.session_state and st.session_state.ai_horse_id:\n",
            "            page = \"🤖 AI Assistant\"\n",
            "        else:\n",
            "            page = st.sidebar.selectbox(\n",
            "                \"Choose a page:\",\n",
            "                [\"Horse Directory\", \"Add New Horse\", \"🤖 AI Assistant\", \"Reports\"]\n",
            "            )\n"
        ]
        
        lines[start:end+1] = new_section
        break

# Write back the corrected file
with open('frontend/app.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed indentation in frontend/app.py")
print("🔄 Refresh your browser to test!")

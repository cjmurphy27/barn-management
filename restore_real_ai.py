import re

# Read current main.py
with open('app/main.py', 'r') as f:
    content = f.read()

# Add anthropic import at the top
if 'import anthropic' not in content:
    # Find the imports section and add anthropic
    import_section = content.find('import logging')
    content = content[:import_section] + 'import anthropic\nimport os\n' + content[import_section:]

# Add anthropic client initialization after app creation
if 'anthropic.Anthropic' not in content:
    app_creation = content.find('app = FastAPI(title="Barn Lady API")')
    insert_pos = content.find('\n', app_creation) + 1
    client_init = '\n# Initialize Anthropic client\nclient = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))\n'
    content = content[:insert_pos] + client_init + content[insert_pos:]

print("Imports and client initialization added")

# Write the updated content
with open('app/main.py', 'w') as f:
    f.write(content)

print("Real Claude API setup complete!")

import base64

# Read the data URL file
with open('/Users/macmini/.openclaw/workspace/larlbot_logo.png', 'r') as f:
    content = f.read()

# Extract just the base64 part (after the comma)
base64_data = content.split(',')[1].strip()

# Add padding if needed
missing_padding = len(base64_data) % 4
if missing_padding:
    base64_data += '=' * (4 - missing_padding)

# Decode and save as proper binary PNG
with open('/Users/macmini/.openclaw/workspace/larlbot_logo.png', 'wb') as f:
    f.write(base64.b64decode(base64_data))

print("Logo file fixed!")
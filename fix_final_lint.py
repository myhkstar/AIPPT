import os

path = 'backend/services/ai_service.py'
if not os.path.exists(path):
    print(f"File not found: {path}")
    exit(1)

content = open(path, 'r', encoding='utf-8').read()

# Fix long ValueError lines
target = '            raise ValueError("Expected a list of page descriptions, but got: " + str(type(descriptions)))'
replacement = '            raise ValueError(\n                "Expected a list of page descriptions, but got: " +\n                str(type(descriptions))\n            )'
content = content.replace(target, replacement)

# Fix long outline_json lines
target2 = '        outline_json = response_text.strip().strip("```json").strip("```").strip()'
replacement2 = '        outline_json = (\n            response_text.strip().strip("```json").strip("```").strip()\n        )'
content = content.replace(target2, replacement2)

# Fix long descriptions_json lines
target3 = '        descriptions_json = response_text.strip().strip("```json").strip("```").strip()'
replacement3 = '        descriptions_json = (\n            response_text.strip().strip("```json").strip("```").strip()\n        )'
content = content.replace(target3, replacement3)

# Ensure single newline at end of file
content = content.rstrip() + '\n'

open(path, 'w', encoding='utf-8').write(content)
print("Successfully fixed final lint errors in ai_service.py")

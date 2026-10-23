# Read the file
with open(r'C:\Users\Shakeel\OneDrive\Desktop\New folder\backend\tests\e2e\test_realistic_violations.py', 'r') as f:
    content = f.read()

# Fix line 97: escape the inner quotes
content = content.replace(
    '"explanation": "Use semantic HTML elements instead of ARIA role="button" on div"',
    '"explanation": "Use semantic HTML elements instead of ARIA role=\\"button\\" on div"'
)

# Write back
with open(r'C:\Users\Shakeel\OneDrive\Desktop\New folder\backend\tests\e2e\test_realistic_violations.py', 'w') as f:
    f.write(content)

print("Fixed syntax errors in test_realistic_violations.py")

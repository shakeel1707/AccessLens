import re

# Read the file
with open(r'C:\Users\Shakeel\OneDrive\Desktop\New folder\backend\tests\e2e\conftest.py', 'r') as f:
    content = f.read()

# Replace the incorrect imports with correct ones
# Remove the import line with incorrect models since they're not used
content = re.sub(
    r'from app\.models\.schemas import \(\s*ScanModel, FindingModel, RepairModel, PatchModel, ReportModel\s*\)',
    '',
    content
)

# Clean up extra blank lines
content = re.sub(r'\n\n\n+', '\n\n', content)

# Write back
with open(r'C:\Users\Shakeel\OneDrive\Desktop\New folder\backend\tests\e2e\conftest.py', 'w') as f:
    f.write(content)

print("Fixed conftest imports")

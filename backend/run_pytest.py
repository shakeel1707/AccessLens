import subprocess
import sys
import os

os.chdir(r"C:\Users\Shakeel\OneDrive\Desktop\New folder\backend")
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/e2e/", "-v", "--tb=short"],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print(f"Return code: {result.returncode}")

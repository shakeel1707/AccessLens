import subprocess
import sys
import os

os.chdir(r"C:\Users\Shakeel\OneDrive\Desktop\New folder\backend")
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/e2e/", "-v", "--tb=short"],
    capture_output=True,
    text=True
)

with open("e2e_tests_output.txt", "w") as f:
    f.write(result.stdout)
    if result.stderr:
        f.write("\n=== STDERR ===\n")
        f.write(result.stderr)
    f.write(f"\n\nReturn code: {result.returncode}")

print("Test output written to e2e_tests_output.txt")

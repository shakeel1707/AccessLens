import subprocess
import sys
import os

os.chdir(r"C:\Users\Shakeel\OneDrive\Desktop\New folder\backend")
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/e2e/", "-v", "--tb=line"],
    capture_output=True,
    text=True,
    timeout=180
)

# Write full output
with open("e2e_tests_final.txt", "w") as f:
    f.write(result.stdout)
    if result.stderr:
        f.write("\n=== STDERR ===\n")
        f.write(result.stderr)
    f.write(f"\n\nReturn code: {result.returncode}")

# Also count results
lines = result.stdout.split('\n')
for line in lines[-20:]:
    print(line)

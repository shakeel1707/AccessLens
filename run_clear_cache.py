import subprocess, sys, os, shutil

os.chdir(r"C:\Users\Shakeel\OneDrive\Desktop\New folder\backend")

# Clear pycache
if os.path.exists(".pytest_cache"):
    shutil.rmtree(".pytest_cache")
if os.path.exists("tests/e2e/__pycache__"):
    shutil.rmtree("tests/e2e/__pycache__")

# Run tests
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/e2e/", "-v", "--cache-clear", "--tb=line"],
    capture_output=True,
    text=True,
    timeout=180
)

# Save output
with open("e2e_final_run.txt", "w") as f:
    f.write(result.stdout)
    if result.stderr:
        f.write("\n=== STDERR ===\n" + result.stderr)
    f.write(f"\n\nReturn code: {result.returncode}")

print("Tests completed")

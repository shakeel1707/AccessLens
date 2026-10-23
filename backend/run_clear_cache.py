import subprocess, sys, os, shutil

os.chdir(r"C:\Users\Shakeel\OneDrive\Desktop\New folder\backend")

# Clear pycache
for pdir in [".pytest_cache", "tests/e2e/__pycache__", ".hypothesis"]:
    if os.path.exists(pdir):
        try:
            shutil.rmtree(pdir)
        except:
            pass

# Run tests
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/e2e/", "-v", "--tb=line"],
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

print("Done")

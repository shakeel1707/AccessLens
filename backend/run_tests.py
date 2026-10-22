#!/usr/bin/env python
"""Run Task 14 tests and report results"""

import subprocess
import sys
import os

# Change to backend directory
os.chdir('c:\\Users\\Shakeel\\OneDrive\\Desktop\\New folder\\backend')

# Run pytest
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/test_task14_patch_application.py', '-v', '--tb=short'],
    capture_output=True,
    text=True
)

print(result.stdout)
print(result.stderr)

sys.exit(result.returncode)

#!/usr/bin/env python
"""Quick test runner to verify fixes"""
import subprocess
import sys

result = subprocess.run([
    sys.executable, '-m', 'pytest', 
    'tests/unit/test_schemas.py::TestScanRequestValidation::test_scan_request_max_length',
    'tests/unit/test_validators.py::TestURLValidation::test_metadata_endpoint_rejected',
    'tests/unit/test_validators.py::TestURLRedirects::test_max_redirects_enforced',
    '-xvs'
], cwd=r'c:\Users\Shakeel\OneDrive\Desktop\New folder\backend')

sys.exit(result.returncode)

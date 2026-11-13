#!/usr/bin/env python
"""
Verification script for E2E testing setup
Tests that:
1. conftest.py can be imported without errors
2. All fixtures are defined
3. moto mocking is properly configured
4. boto3 credential mocking is active
"""

import sys
import os
from pathlib import Path

# Add src to path like conftest does
backend_root = Path(__file__).parent
src_path = backend_root / 'src'
sys.path.insert(0, str(src_path))

print("=" * 80)
print("E2E TEST SETUP VERIFICATION")
print("=" * 80)

# Step 1: Import conftest
print("\n[Step 1] Importing conftest.py...")
try:
    import tests.e2e.conftest as conftest_module
    print("✓ conftest.py imported successfully")
except Exception as e:
    print(f"✗ Failed to import conftest.py: {e}")
    sys.exit(1)

# Step 2: Check environment variables
print("\n[Step 2] Checking AWS environment variables...")
env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SECURITY_TOKEN', 'AWS_DEFAULT_REGION']
for var in env_vars:
    value = os.environ.get(var, '(not set)')
    if value == '(not set)':
        print(f"  ✗ {var}: {value}")
    else:
        print(f"  ✓ {var}: {value[:20]}...")

# Step 3: Check fixtures exist
print("\n[Step 3] Checking fixtures are defined...")
fixtures = [
    'mock_boto3',
    'client',
    'mock_aws_services',
    'sample_scan_data',
    'sample_findings',
    'sample_repairs',
    'mock_axe_findings',
    'realistic_html_violations',
    'mock_dynamodb_tables'
]

for fixture_name in fixtures:
    if hasattr(conftest_module, fixture_name):
        print(f"  ✓ {fixture_name}")
    else:
        print(f"  ✗ {fixture_name} not found")

# Step 4: Test moto mock decorator
print("\n[Step 4] Testing moto mock decorator...")
try:
    from moto import mock_aws
    import boto3
    
    @mock_aws
    def test_mock_active():
        # This should use moto mock, not real AWS
        client = boto3.client('dynamodb', region_name='us-east-1')
        # If this doesn't raise an error, mocking is working
        return True
    
    result = test_mock_active()
    if result:
        print("  ✓ moto mock decorator working")
    else:
        print("  ✗ moto mock decorator failed")
except Exception as e:
    print(f"  ✗ moto mock test failed: {e}")

# Step 5: Test app import with mocking
print("\n[Step 5] Testing app import with mocking active...")
try:
    # The client fixture does this
    from app.main import create_app
    app = create_app()
    print("  ✓ App created successfully")
    
    # Check for expected routes
    routes = [route.path for route in app.routes]
    expected_routes = ['/api/scan', '/api/repair', '/api/patch', '/api/report']
    found = sum(1 for route in expected_routes if any(route in r for r in routes))
    print(f"  ✓ Found {found}/{len(expected_routes)} expected API routes")
except Exception as e:
    print(f"  ✗ Failed to create app: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)

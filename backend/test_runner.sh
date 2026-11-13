#!/bin/bash
# Test runner for AccessLens backend fixes

cd "c:\Users\Shakeel\OneDrive\Desktop\New folder\backend"

echo "Running pytest for all tests..."
python -m pytest -v --tb=short

echo "Exit code: $?"

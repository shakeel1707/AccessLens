@echo off
cd /d "c:\Users\Shakeel\OneDrive\Desktop\New folder\backend"
C:\Users\Shakeel\AppData\Local\Programs\Python\Python314\python.exe -m pytest tests/unit/test_pbt_suite6_api_payload.py tests/unit/test_pbt_suite8_isolation.py tests/unit/test_pbt_suite9_patch_policy.py -v --tb=short > pbt_suite6789_final.txt 2>&1
type pbt_suite6789_final.txt

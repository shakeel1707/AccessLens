@echo off
cd /d "c:\Users\Shakeel\OneDrive\Desktop\New folder\backend"
C:\Users\Shakeel\AppData\Local\Programs\Python\Python314\python.exe -m pytest tests/unit/test_pbt_suite1_finding_structure.py tests/unit/test_pbt_suite2_patch_safety.py tests/unit/test_pbt_suite3_finding_identity.py tests/unit/test_pbt_suite4_url_validation.py tests/unit/test_pbt_suite5_deduplication.py -v --tb=short > pbt_results_fixed.txt 2>&1
type pbt_results_fixed.txt

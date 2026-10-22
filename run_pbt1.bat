@echo off
cd /d "c:\Users\Shakeel\OneDrive\Desktop\New folder"
C:\Users\Shakeel\AppData\Local\Programs\Python\Python314\python.exe -m pytest backend/tests/unit/test_pbt_suite1_finding_structure.py -v --tb=short 2>&1

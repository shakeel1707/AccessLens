@echo off
cd /d "c:\Users\Shakeel\OneDrive\Desktop\New folder\frontend"
npm test -- --run > frontend_suite7_results.txt 2>&1
type frontend_suite7_results.txt

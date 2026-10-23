@echo off
REM Run E2E tests for AccessLens
cd /d "%~dp0"
echo Running E2E tests...
python -m pytest backend/tests/e2e/ -v --tb=short
pause

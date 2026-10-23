# AccessLens E2E Test Suite

Complete end-to-end tests for the AccessLens accessibility detection and repair platform.

## Quick Start

### Setup

```bash
# Install dependencies
pip install -r ../../requirements.txt

# Install optional E2E test dependencies
pip install moto[dynamodb,s3,bedrock]
```

### Run All E2E Tests

```bash
# From workspace root
pytest backend/tests/e2e/ -v

# With coverage report
pytest backend/tests/e2e/ -v --cov=app --cov-report=html

# With detailed output
pytest backend/tests/e2e/ -v -s --tb=long
```

### Run Specific Test Suites

```bash
# Complete workflow tests
pytest backend/tests/e2e/test_complete_workflow.py -v

# Realistic violations tests
pytest backend/tests/e2e/test_realistic_violations.py -v

# Only happy path
pytest backend/tests/e2e/test_complete_workflow.py::TestE2ECompleteWorkflow::test_e2e_workflow_success_happy_path -v

# Only error scenarios
pytest backend/tests/e2e/test_complete_workflow.py::TestE2EErrorScenarios -v
```

## Test Files

### `conftest.py`
Shared pytest fixtures for all E2E tests:
- **`client`**: FastAPI TestClient
- **`mock_aws_services`**: Moto-based mocks for DynamoDB, S3, Bedrock
- **`sample_scan_data`**: Example scan submission data
- **`sample_findings_data`**: Example accessibility findings
- **`sample_repair_data`**: Example AI-generated repairs
- **`mock_playwright_scanner`**: Mocks website scanning
- **`mock_bedrock_repair_generator`**: Mocks repair generation

### `test_complete_workflow.py`
Comprehensive E2E tests covering:
- ✅ **Happy path**: Complete workflow success
- ✅ **URL validation**: Invalid URLs and SSRF prevention
- ✅ **Error scenarios**: Network issues, missing data, concurrent modifications
- ✅ **Data persistence**: Scans, repairs, patches survive across API calls
- ✅ **Report generation**: JSON, CSV, PDF formats
- ✅ **Performance**: Response time SLAs

**Test Classes:**
- `TestE2ECompleteWorkflow`: Full workflow tests
- `TestE2EErrorScenarios`: Error handling and edge cases
- `TestE2EDataPersistence`: Data integrity across steps
- `TestE2EReportGeneration`: Report format validation
- `TestE2EPerformance`: Performance benchmarks

### `test_realistic_violations.py`
Tests with real-world WCAG violations:
- Missing alt text on images
- Form inputs without labels
- Low contrast text
- Missing page titles
- Improper heading hierarchy
- Links without clear purpose
- Buttons without accessible names
- Videos without captions
- Color-only information conveyance

**Test Classes:**
- `TestE2ERealisticViolations`: Workflow tests with real violations
- `TestE2EViolationDetectionAccuracy`: Detection quality
- `TestE2ERepairQuality`: Repair quality metrics

### `TEST_SCENARIOS.md`
Detailed documentation of:
- All 8 workflow steps tested
- Test categories and scenarios
- Expected results and troubleshooting
- Performance benchmarks

## Workflow Steps Tested

```
1. URL Submission (POST /api/scan)
   ↓
2. Website Scanning (Playwright)
   ↓
3. Finding Detection (WCAG violations)
   ↓
4. Repair Generation (Bedrock AI)
   ↓
5. Repair Review (POST /api/repair/approve)
   ↓
6. Patch Application (POST /api/patch/apply)
   ↓
7. Verification (GET /api/verification/{scan_id})
   ↓
8. Report Generation (GET /api/report/{scan_id})
```

## Test Coverage

### Endpoints Tested
- ✅ `POST /api/scan` - Submit URL for scanning
- ✅ `POST /api/repair/generate` - Generate repairs
- ✅ `POST /api/repair/approve` - Approve repairs
- ✅ `POST /api/patch/apply` - Apply patches
- ✅ `GET /api/verification/{scan_id}` - Get verification results
- ✅ `GET /api/report/{scan_id}` - Generate reports

### Scenarios Covered
- ✅ Happy path (everything succeeds)
- ✅ Input validation (invalid URLs, malformed data)
- ✅ SSRF prevention (private network detection)
- ✅ Error handling (network timeouts, service errors)
- ✅ Data persistence (scans, findings, repairs, patches)
- ✅ Concurrent operations (race conditions)
- ✅ Report formats (JSON, CSV, PDF)
- ✅ Realistic violations (10+ WCAG criteria)

### Performance Targets
- Scan submission: < 2 seconds
- Report retrieval: < 1 second
- Handling 50+ findings: no degradation
- Concurrent requests: handled efficiently

## AWS Mocking

Tests use **moto** for AWS service mocking. No real AWS credentials needed.

### Mocked Services
```
DynamoDB:
  - Scan metadata storage
  - Findings storage
  - Repairs storage
  - Patches tracking

S3:
  - Report caching
  - Report export

Bedrock:
  - AI repair generation
```

### Environment Variables (for mocking)
```bash
# Tests override these automatically
AWS_ACCESS_KEY_ID=testing
AWS_SECRET_ACCESS_KEY=testing
AWS_SECURITY_TOKEN=testing
AWS_SESSION_TOKEN=testing
AWS_DEFAULT_REGION=us-east-1
```

## Common Issues & Solutions

### Issue: Tests fail with "No module named 'moto'"
**Solution:** Install moto with all extras:
```bash
pip install 'moto[dynamodb,s3,bedrock]'
```

### Issue: Playwright browser not found
**Solution:** Install Playwright browsers (optional for E2E tests):
```bash
python -m playwright install chromium
```

### Issue: Tests timeout on SSRF checks
**Solution:** SSRF tests intentionally try invalid URLs. This is expected.
Run with increased timeout:
```bash
pytest backend/tests/e2e/ -v --timeout=30
```

### Issue: Report generation tests fail
**Solution:** Ensure S3 mocking is working:
```bash
pytest backend/tests/e2e/test_complete_workflow.py::TestE2EReportGeneration -v -s
```

### Issue: DynamoDB mock not responding
**Solution:** Check that moto is properly patching boto3:
```bash
pytest backend/tests/e2e/ -v --capture=no  # Verbose output
```

## Running Specific Test Groups

### By Severity
```bash
# High severity violations
pytest backend/tests/e2e/test_realistic_violations.py -v -k "high_severity"

# Medium severity violations
pytest backend/tests/e2e/test_realistic_violations.py -v -k "medium_severity"
```

### By Workflow Step
```bash
# Scan submission only
pytest backend/tests/e2e/ -v -k "workflow_invalid_url or workflow_ssrf"

# Repair generation only
pytest backend/tests/e2e/ -v -k "repair_generation"

# Report generation only
pytest backend/tests/e2e/ -v -k "report"
```

### By Issue Type
```bash
# Performance tests
pytest backend/tests/e2e/test_complete_workflow.py::TestE2EPerformance -v

# Error scenarios
pytest backend/tests/e2e/test_complete_workflow.py::TestE2EErrorScenarios -v

# Data persistence
pytest backend/tests/e2e/test_complete_workflow.py::TestE2EDataPersistence -v
```

## Test Results

### Success Criteria
All tests pass when:
- ✅ Endpoints return correct HTTP status codes
- ✅ Response data matches expected schemas
- ✅ Data persisted across API calls
- ✅ Error handling graceful and informative
- ✅ Performance meets SLAs
- ✅ SSRF prevention working
- ✅ No race conditions in concurrent operations

### Example Output
```
backend/tests/e2e/test_complete_workflow.py::TestE2ECompleteWorkflow::test_e2e_workflow_success_happy_path PASSED [3%]
backend/tests/e2e/test_complete_workflow.py::TestE2ECompleteWorkflow::test_e2e_workflow_invalid_url PASSED [6%]
backend/tests/e2e/test_complete_workflow.py::TestE2ECompleteWorkflow::test_e2e_workflow_ssrf_prevention PASSED [9%]
...
============================== 45 passed in 12.34s ==============================
```

## Performance Benchmarks

### Expected Execution Times
- All E2E tests: ~30-60 seconds
- Individual test: 100-500ms
- Report generation tests: 1-2 seconds
- Performance benchmark tests: 2-5 seconds

### Coverage Report
```bash
# Generate HTML coverage report
pytest backend/tests/e2e/ --cov=app --cov-report=html

# View in browser
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

## Integration with CI/CD

### GitHub Actions
See `.github/workflows/e2e-tests.yml`:
- Runs on push to `main` and `develop`
- Tests against Python 3.9, 3.10, 3.11
- Uploads coverage to Codecov
- Publishes test results

### Local Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
pytest backend/tests/e2e/ -q || exit 1
```

## Next Steps: Browser E2E Tests

Phase 2 will add browser-based E2E tests:
- Use Playwright for browser automation
- Test React UI interactions
- Validate form submission flow
- Test repair approval workflow
- Validate report download
- Visual regression testing

**Estimated effort:** 8-12 hours

## References

- [FastAPI Testing Guide](https://fastapi.tiangolo.com/advanced/testing-databases/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Moto AWS Mocking](https://docs.getmoto.org/)
- [WCAG 2.1 Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [Playwright Documentation](https://playwright.dev/)
- [pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)

## Contributing

When adding new E2E tests:

1. Follow existing test structure (test class → test method)
2. Use descriptive test names: `test_e2e_<scenario>_<expected_result>`
3. Add docstrings explaining what's being tested
4. Use fixtures from `conftest.py` for consistency
5. Keep tests independent (no test order dependencies)
6. Add realistic scenarios, not just happy paths
7. Document new test scenarios in `TEST_SCENARIOS.md`

## Support

For issues or questions:
1. Check `TEST_SCENARIOS.md` for detailed documentation
2. Review existing test examples in this suite
3. Check pytest output for specific error messages
4. Run with `-v -s` flags for verbose output

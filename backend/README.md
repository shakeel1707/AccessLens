# AccessLens Backend API

FastAPI-based REST API for AI-powered website accessibility detection and repair.

## Quick Start

### Prerequisites

- Python 3.10+
- pip or poetry
- (Optional) Docker and LocalStack for local DynamoDB

### Local Development Setup

1. **Create Python virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
# Or with dev dependencies:
pip install -e ".[dev]"
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env for local settings (defaults work for dev)
```

4. **Run the server:**
```bash
python run_server.py
```

Server starts at `http://127.0.0.1:8000`

**Available endpoints:**
- Health check: `GET /health`
- API info: `GET /api/info`
- API docs: `GET /docs` (interactive Swagger UI)
- ReDoc: `GET /redoc`

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/unit/test_config.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/unit/test_config.py::test_config_default_values
```

## Project Structure

```
backend/
├── src/app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app factory
│   ├── core/
│   │   ├── config.py              # Configuration management
│   │   ├── errors.py              # Error handling middleware
│   │   └── __init__.py
│   ├── models/
│   │   └── __init__.py            # Pydantic models (TODO)
│   ├── routers/
│   │   ├── scan.py                # Scanning endpoints
│   │   ├── repair.py              # Repair endpoints
│   │   ├── patch.py               # Patch application endpoints
│   │   ├── verification.py        # Verification endpoints
│   │   └── __init__.py
│   └── services/
│       └── __init__.py            # Business logic services (TODO)
├── tests/
│   ├── unit/
│   │   ├── test_config.py         # Configuration tests
│   │   └── __init__.py
│   └── __init__.py
├── config/
│   └── __init__.py                # Config files (TODO)
├── run_server.py                  # Entry point
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project metadata & build config
├── .env.example                   # Environment variables template
├── .env                           # Local environment (git-ignored)
└── README.md                      # This file
```

## Configuration

Configuration is loaded from environment variables. See `.env.example` for all available settings.

### Key Configuration Variables

- `ENVIRONMENT`: dev, test, or prod (default: dev)
- `HOST`: Server host (default: 127.0.0.1)
- `PORT`: Server port (default: 8000)
- `SCAN_TIMEOUT_SECONDS`: Scan timeout (default: 30)
- `MAX_CONCURRENT_SCANS`: Max parallel scans (default: 5)
- `LOG_FORMAT`: console or json (default: console in dev, json in prod)

### Local Development Configuration

For local development with DynamoDB:

1. **Option A: Use LocalStack (Recommended)**
```bash
# Install and start LocalStack
docker run -it -p 8000:4566 -e SERVICES=dynamodb localstack/localstack

# In .env, set:
USE_LOCAL_DYNAMODB=true
LOCAL_DYNAMODB_ENDPOINT=http://localhost:4566
```

2. **Option B: Use DynamoDB Local**
```bash
# Download from AWS and run locally
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb

# In .env, set:
USE_LOCAL_DYNAMODB=true
LOCAL_DYNAMODB_ENDPOINT=http://localhost:8000
```

## API Endpoints

### Scanning

- `POST /api/scan`: Submit website for scanning
  - Request: `{ url, user_id }`
  - Response: `{ scan_id, status, message }`

- `GET /api/scan/{scan_id}`: Get scan status and findings
  - Response: `{ scan_id, status, findings, message }`

### Repair Generation

- `POST /api/repair/generate`: Generate repair proposals
  - Request: `{ scan_id, finding_ids[] }`
  - Response: `{ scan_id, repairs[], message }`

- `POST /api/repair/approve`: Approve or reject repair
  - Request: `{ scan_id, repair_id, approved, comment }`
  - Response: `{ repair_id, status, message }`

### Patch Application

- `POST /api/patch/apply`: Apply patches in isolated environment
  - Request: `{ scan_id, repair_ids[] }`
  - Response: `{ scan_id, application_status, message }`

### Verification

- `GET /api/verification/{scan_id}`: Get verification results
  - Response: `{ scan_id, fixed_count, new_violations, unresolved, comparison, message }`

## Error Handling

All errors follow a standardized response format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status_code": 400,
    "request_id": "uuid-for-debugging"
  }
}
```

Common error codes:
- `VALIDATION_ERROR`: Invalid input (400)
- `HTTP_ERROR`: HTTP-level error (varies)
- `INTERNAL_ERROR`: Server error (500)

## Development Workflow

### Making Changes

1. **Install dev dependencies:**
```bash
pip install -e ".[dev]"
```

2. **Format code:**
```bash
black src/app tests
isort src/app tests
```

3. **Type check:**
```bash
mypy src/app
```

4. **Lint:**
```bash
flake8 src/app tests
```

5. **Run tests:**
```bash
pytest
```

### Pre-commit Checks

Before committing code:
```bash
black src/app tests && isort src/app tests && mypy src/app && flake8 src/app tests && pytest
```

## Logging

Logs are written to stdout and formatted based on `LOG_FORMAT`:

- **console** (development): Human-readable format
- **json** (production): JSON format for structured logging

Example dev log:
```
2024-01-15 10:30:45 [INFO] accesslens.middleware: Request started
2024-01-15 10:30:46 [INFO] accesslens.routers.scan: Scan completed
```

Example prod log:
```json
{"time": "2024-01-15 10:30:45", "level": "INFO", "logger": "accesslens", "message": "Request started"}
```

## Security

### SSRF Protection (Task 3)

URL validation enforces:
- HTTP/HTTPS schemes only
- External IP addresses only (blocks localhost, private networks)
- Redirect detection (max 5 hops, loop detection)

### Content Validation (Task 5)

- Pydantic models validate all inputs
- API payloads checked for boundaries (URL max 2048 chars, findings max 10000)
- Malformed requests return 400 Bad Request

### Error Handling

- All exceptions caught and logged
- Request IDs tracked for debugging
- No sensitive data in error messages
- Proper HTTP status codes returned

## Deployment

### Local Testing
```bash
# Dev mode with auto-reload
ENVIRONMENT=dev python run_server.py

# Test mode (no reload)
ENVIRONMENT=test python run_server.py
```

### Production Deployment (AWS Lambda)

See `.../deployment/README.md` for infrastructure setup and Lambda deployment instructions.

## Monitoring

### Health Checks

```bash
curl http://localhost:8000/health
```

Returns:
```json
{
  "status": "healthy",
  "environment": "dev",
  "version": "1.0.0"
}
```

### CloudWatch Integration (Task 1)

When `ENABLE_CLOUDWATCH=true`:
- Logs sent to CloudWatch Log Group (default: `/accesslens/backend`)
- Errors and warnings logged with full context
- Request IDs tracked for correlation

## Testing Strategy

### Unit Tests
- Configuration loading and validation
- Error handling
- Logger setup

### Integration Tests (TODO)
- API endpoints with mock data
- DynamoDB interactions
- Bedrock API calls

### End-to-End Tests (TODO)
- Complete workflows
- Real browser scanning
- Patch application and verification

## Known Limitations & TODOs

- [ ] PBT Suite 6 (API Payload validation) — Task 5
- [ ] Rate limiting middleware — Task 5
- [ ] Bedrock integration — Task 10
- [ ] Playwright scanning engine — Task 6
- [ ] DynamoDB persistence layer — Task 2
- [ ] URL validation with SSRF protection — Task 3
- [ ] Finding deduplication logic — Task 4

## Support

For issues or questions:
1. Check logs: `tail -f app.log` (when logging to file)
2. Check request ID in error response for correlation
3. Review error codes in documentation above
4. Create issue on GitHub

## License

MIT License — See LICENSE file for details.
"""Integration tests for Task 8: Finding Caching and Retrieval"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
sys.path.insert(0, 'src')

from app.models.schemas import ScanStatus, Severity, FindingResponse
from app.models.database import ScanModel, FindingModel
from datetime import datetime


@pytest.mark.asyncio
async def test_get_findings_for_completed_scan():
    """Test retrieving findings for a completed scan"""
    from fastapi.testclient import TestClient
    from app.main import create_app
    
    app = create_app()
    client = TestClient(app)
    
    # Mock the repositories
    with patch('app.routers.scan.DynamoDBClient') as mock_db, \
         patch('app.routers.scan.ScansRepository') as mock_scans_repo, \
         patch('app.routers.scan.FindingsRepository') as mock_findings_repo:
        
        # Setup mocks
        mock_scan = ScanModel(
            scan_id='test-scan-123',
            url='https://example.com',
            status=ScanStatus.COMPLETED,
            finding_count=2,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )
        
        mock_findings = [
            FindingModel(
                scan_id='test-scan-123',
                finding_id='finding-1',
                rule_id='image-alt',
                severity=Severity.CRITICAL,
                selector='img.logo',
                html_snippet='<img class="logo" src="logo.png">',
                description='Images must have alternative text',
                created_at=datetime.utcnow().isoformat(),
            ),
            FindingModel(
                scan_id='test-scan-123',
                finding_id='finding-2',
                rule_id='color-contrast',
                severity=Severity.MODERATE,
                selector='button.submit',
                html_snippet='<button class="submit">Submit</button>',
                description='Text must have sufficient contrast',
                created_at=datetime.utcnow().isoformat(),
            ),
        ]
        
        mock_scans_repo.return_value.get.return_value = mock_scan
        mock_findings_repo.return_value.query_by_scan.return_value = mock_findings
        mock_db.return_value = Mock()
        
        # Make request
        response = client.get('/api/scan/test-scan-123/findings')
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['finding_id'] == 'finding-1'
        assert data[0]['rule_id'] == 'image-alt'
        assert data[0]['severity'] == 'critical'
        assert data[1]['finding_id'] == 'finding-2'


@pytest.mark.asyncio
async def test_get_findings_scan_not_found():
    """Test retrieving findings for non-existent scan"""
    from fastapi.testclient import TestClient
    from app.main import create_app
    
    app = create_app()
    client = TestClient(app)
    
    with patch('app.routers.scan.DynamoDBClient') as mock_db, \
         patch('app.routers.scan.ScansRepository') as mock_scans_repo:
        
        mock_scans_repo.return_value.get.return_value = None
        mock_db.return_value = Mock()
        
        response = client.get('/api/scan/nonexistent/findings')
        
        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_get_findings_scan_not_completed():
    """Test retrieving findings for incomplete scan"""
    from fastapi.testclient import TestClient
    from app.main import create_app
    
    app = create_app()
    client = TestClient(app)
    
    with patch('app.routers.scan.DynamoDBClient') as mock_db, \
         patch('app.routers.scan.ScansRepository') as mock_scans_repo:
        
        mock_scan = ScanModel(
            scan_id='test-scan-pending',
            url='https://example.com',
            status=ScanStatus.PENDING,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )
        
        mock_scans_repo.return_value.get.return_value = mock_scan
        mock_db.return_value = Mock()
        
        response = client.get('/api/scan/test-scan-pending/findings')
        
        assert response.status_code == 400
        assert 'not completed' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_get_findings_returns_all_fields():
    """Test that findings include all required fields"""
    from fastapi.testclient import TestClient
    from app.main import create_app
    
    app = create_app()
    client = TestClient(app)
    
    with patch('app.routers.scan.DynamoDBClient') as mock_db, \
         patch('app.routers.scan.ScansRepository') as mock_scans_repo, \
         patch('app.routers.scan.FindingsRepository') as mock_findings_repo:
        
        mock_scan = ScanModel(
            scan_id='test-scan-complete',
            url='https://example.com',
            status=ScanStatus.COMPLETED,
            finding_count=1,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )
        
        mock_finding = FindingModel(
            scan_id='test-scan-complete',
            finding_id='f-abc123',
            rule_id='heading-order',
            severity=Severity.SERIOUS,
            selector='h3.section-title',
            html_snippet='<h3 class="section-title">Title</h3>',
            description='Heading levels must be consecutive',
            created_at=datetime.utcnow().isoformat(),
        )
        
        mock_scans_repo.return_value.get.return_value = mock_scan
        mock_findings_repo.return_value.query_by_scan.return_value = [mock_finding]
        mock_db.return_value = Mock()
        
        response = client.get('/api/scan/test-scan-complete/findings')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        finding = data[0]
        assert 'finding_id' in finding
        assert 'rule_id' in finding
        assert 'severity' in finding
        assert 'selector' in finding
        assert 'html' in finding
        assert 'description' in finding
        assert finding['finding_id'] == 'f-abc123'
        assert finding['rule_id'] == 'heading-order'
        assert finding['severity'] == 'serious'
        assert finding['selector'] == 'h3.section-title'
        assert finding['html'] == '<h3 class="section-title">Title</h3>'
        assert finding['description'] == 'Heading levels must be consecutive'

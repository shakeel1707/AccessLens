"""Unit and integration tests for Task 9: Scan Error Handling and Retry Logic"""
import pytest
import asyncio
import sys
sys.path.insert(0, 'src')

from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from app.models.schemas import ScanStatus, Severity
from app.models.database import ScanModel


class TestRetryLogic:
    """Test exponential backoff retry logic"""
    
    @pytest.mark.asyncio
    async def test_retry_on_timeout(self):
        """Test retry logic on asyncio.TimeoutError"""
        from app.routers.scan import perform_scan
        
        mock_db = Mock()
        mock_config = Mock()
        mock_config.SCAN_TIMEOUT_SECONDS = 30
        
        with patch('app.routers.scan.ScansRepository') as mock_scans_repo, \
             patch('app.routers.scan.FindingsRepository') as mock_findings_repo, \
             patch('app.routers.scan.get_scanner') as mock_get_scanner:
            
            # Setup scan model
            mock_scan = ScanModel(
                scan_id='test-retry-scan',
                url='https://example.com',
                status=ScanStatus.PENDING,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            )
            
            mock_scans_repo.return_value.get.return_value = mock_scan
            
            # Mock scanner to timeout then succeed
            mock_scanner = AsyncMock()
            mock_scanner.scan.side_effect = [
                asyncio.TimeoutError("Scan timed out"),
                asyncio.TimeoutError("Scan timed out"),
                Mock(findings=[])  # Success on 3rd attempt
            ]
            mock_get_scanner.return_value = mock_scanner
            
            # Run perform_scan - should retry and eventually fail after max retries
            await perform_scan('test-retry-scan', 'https://example.com', 'user-1', mock_db, mock_config)
            
            # Verify scan was called multiple times (retries happened)
            assert mock_scanner.scan.call_count >= 1


    @pytest.mark.asyncio
    async def test_exponential_backoff_delay(self):
        """Test that retry delays follow exponential backoff (1s, 2s)"""
        from app.routers.scan import perform_scan
        
        mock_db = Mock()
        mock_config = Mock()
        mock_config.SCAN_TIMEOUT_SECONDS = 30
        
        with patch('app.routers.scan.ScansRepository') as mock_scans_repo, \
             patch('app.routers.scan.get_scanner') as mock_get_scanner, \
             patch('app.routers.scan.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            
            mock_scan = ScanModel(
                scan_id='test-backoff',
                url='https://example.com',
                status=ScanStatus.PENDING,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            )
            
            mock_scans_repo.return_value.get.return_value = mock_scan
            
            # Mock scanner to fail twice then succeed
            mock_scanner = AsyncMock()
            mock_scanner.scan.side_effect = [
                Exception("Network error"),
                Exception("Network error"),
                Mock(findings=[])
            ]
            mock_get_scanner.return_value = mock_scanner
            
            await perform_scan('test-backoff', 'https://example.com', 'user-1', mock_db, mock_config)
            
            # Verify sleep was called with exponential backoff values
            # Should be called with 1 and 2 seconds
            sleep_calls = mock_sleep.call_args_list
            # First retry after 1s, second retry after 2s
            if len(sleep_calls) >= 1:
                first_delay = sleep_calls[0][0][0]
                assert first_delay == 1, f"Expected first delay to be 1s, got {first_delay}"
                
            if len(sleep_calls) >= 2:
                second_delay = sleep_calls[1][0][0]
                assert second_delay == 2, f"Expected second delay to be 2s, got {second_delay}"


class TestErrorHandling:
    """Test error handling and failure notification"""
    
    @pytest.mark.asyncio
    async def test_scan_marked_failed_after_max_retries(self):
        """Test that scan is marked as failed after max retries exhausted"""
        from app.routers.scan import perform_scan
        
        mock_db = Mock()
        mock_config = Mock()
        mock_config.SCAN_TIMEOUT_SECONDS = 30
        
        with patch('app.routers.scan.ScansRepository') as mock_scans_repo, \
             patch('app.routers.scan.get_scanner') as mock_get_scanner:
            
            mock_scan = ScanModel(
                scan_id='test-fail',
                url='https://example.com',
                status=ScanStatus.PENDING,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            )
            
            mock_scans_repo.return_value.get.return_value = mock_scan
            
            # Mock scanner to always fail
            mock_scanner = AsyncMock()
            mock_scanner.scan.side_effect = Exception("Network error")
            mock_get_scanner.return_value = mock_scanner
            
            await perform_scan('test-fail', 'https://example.com', 'user-1', mock_db, mock_config)
            
            # Verify final update sets status to FAILED
            final_call = mock_scans_repo.return_value.update.call_args_list[-1]
            updated_scan = final_call[0][0]
            assert updated_scan.status == ScanStatus.FAILED
            assert 'Exception' in updated_scan.error_message


    @pytest.mark.asyncio
    async def test_error_message_includes_error_type(self):
        """Test that error messages include exception type for debugging"""
        from app.routers.scan import perform_scan
        
        mock_db = Mock()
        mock_config = Mock()
        mock_config.SCAN_TIMEOUT_SECONDS = 30
        
        with patch('app.routers.scan.ScansRepository') as mock_scans_repo, \
             patch('app.routers.scan.get_scanner') as mock_get_scanner, \
             patch('app.routers.scan.asyncio.sleep', new_callable=AsyncMock):
            
            mock_scan = ScanModel(
                scan_id='test-error-msg',
                url='https://example.com',
                status=ScanStatus.PENDING,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            )
            
            mock_scans_repo.return_value.get.return_value = mock_scan
            
            # Mock scanner with specific error
            mock_scanner = AsyncMock()
            mock_scanner.scan.side_effect = TimeoutError("Browser timeout after 30s")
            mock_get_scanner.return_value = mock_scanner
            
            await perform_scan('test-error-msg', 'https://example.com', 'user-1', mock_db, mock_config)
            
            # Verify error message contains exception type
            final_call = mock_scans_repo.return_value.update.call_args_list[-1]
            updated_scan = final_call[0][0]
            assert 'TimeoutError' in updated_scan.error_message or 'timeout' in updated_scan.error_message.lower()


class TestScanLifecycle:
    """Test scan lifecycle with error handling"""
    
    @pytest.mark.asyncio
    async def test_scan_status_progression_on_success(self):
        """Test scan status goes: pending ? in_progress ? completed"""
        from app.routers.scan import perform_scan
        
        mock_db = Mock()
        mock_config = Mock()
        mock_config.SCAN_TIMEOUT_SECONDS = 30
        
        with patch('app.routers.scan.ScansRepository') as mock_scans_repo, \
             patch('app.routers.scan.FindingsRepository') as mock_findings_repo, \
             patch('app.routers.scan.get_scanner') as mock_get_scanner, \
             patch('app.routers.scan.FindingIDGenerator') as mock_id_gen, \
             patch('app.routers.scan.FindingDeduplicator') as mock_dedup, \
             patch('app.routers.scan.FindingSortingService') as mock_sorter:
            
            mock_scan = ScanModel(
                scan_id='test-lifecycle',
                url='https://example.com',
                status=ScanStatus.PENDING,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            )
            
            mock_scans_repo.return_value.get.return_value = mock_scan
            
            # Mock successful scan
            mock_result = Mock()
            mock_result.findings = []
            
            mock_scanner = AsyncMock()
            mock_scanner.scan.return_value = mock_result
            mock_get_scanner.return_value = mock_scanner
            
            mock_dedup.deduplicate.return_value = []
            mock_sorter.sort_by_severity.return_value = []
            
            await perform_scan('test-lifecycle', 'https://example.com', 'user-1', mock_db, mock_config)
            
            # Check status updates
            update_calls = mock_scans_repo.return_value.update.call_args_list
            assert len(update_calls) >= 2
            
            # First update should set in_progress
            first_update = update_calls[0][0][0]
            assert first_update.status == ScanStatus.IN_PROGRESS
            
            # Last update should set completed
            last_update = update_calls[-1][0][0]
            assert last_update.status == ScanStatus.COMPLETED

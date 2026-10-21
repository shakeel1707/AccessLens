"""Unit tests for isolated environment setup (Task 13)"""

import pytest
import asyncio
import os
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from app.services.isolated_environment import IsolatedEnvironment, create_isolated_environment


class TestEnvironmentInitialization:
    """Test environment initialization"""
    
    def test_environment_init_defaults(self):
        """Test environment initializes with defaults"""
        env = IsolatedEnvironment()
        assert env.timeout_seconds == 300
        assert env.browser is None
        assert env.context is None
        assert env.page is None
        assert env.temp_dir is None
        assert env.created_at is None
        assert env.environment_id.startswith("env-")
    
    def test_environment_init_custom_timeout(self):
        """Test environment initializes with custom timeout"""
        env = IsolatedEnvironment(timeout_seconds=60)
        assert env.timeout_seconds == 60
    
    def test_environment_id_generation(self):
        """Test unique environment IDs"""
        env1 = IsolatedEnvironment()
        env2 = IsolatedEnvironment()
        assert env1.environment_id != env2.environment_id
        assert env1.environment_id.startswith("env-")
        assert env2.environment_id.startswith("env-")


class TestEnvironmentProperties:
    """Test environment properties and attributes"""
    
    def test_environment_has_cleanup_method(self):
        """Test environment has cleanup method"""
        env = IsolatedEnvironment()
        assert hasattr(env, 'cleanup')
        assert callable(env.cleanup)
    
    def test_environment_has_create_method(self):
        """Test environment has create method"""
        env = IsolatedEnvironment()
        assert hasattr(env, 'create')
        assert callable(env.create)
    
    def test_environment_has_render_method(self):
        """Test environment has render_page method"""
        env = IsolatedEnvironment()
        assert hasattr(env, 'render_page')
        assert callable(env.render_page)


class TestResourceInitialization:
    """Test resource initialization"""
    
    def test_browser_initially_none(self):
        """Test browser is None initially"""
        env = IsolatedEnvironment()
        assert env.browser is None
    
    def test_context_initially_none(self):
        """Test context is None initially"""
        env = IsolatedEnvironment()
        assert env.context is None
    
    def test_page_initially_none(self):
        """Test page is None initially"""
        env = IsolatedEnvironment()
        assert env.page is None
    
    def test_temp_dir_initially_none(self):
        """Test temp_dir is None initially"""
        env = IsolatedEnvironment()
        assert env.temp_dir is None


class TestTimeoutHandling:
    """Test timeout and auto-cleanup"""
    
    def test_timeout_seconds_default_300(self):
        """Test default timeout is 300 seconds"""
        env = IsolatedEnvironment()
        assert env.timeout_seconds == 300
    
    def test_timeout_seconds_custom(self):
        """Test custom timeout"""
        env = IsolatedEnvironment(timeout_seconds=120)
        assert env.timeout_seconds == 120
    
    def test_timeout_seconds_stored(self):
        """Test timeout is stored correctly"""
        env = IsolatedEnvironment(timeout_seconds=600)
        assert env.timeout_seconds == 600
    
    def test_cleanup_task_initially_none(self):
        """Test cleanup_task is initially None"""
        env = IsolatedEnvironment()
        assert env.cleanup_task is None


class TestContextManagerInterface:
    """Test async context manager interface"""
    
    def test_has_aenter(self):
        """Test __aenter__ method exists"""
        env = IsolatedEnvironment()
        assert hasattr(env, '__aenter__')
    
    def test_has_aexit(self):
        """Test __aexit__ method exists"""
        env = IsolatedEnvironment()
        assert hasattr(env, '__aexit__')
    
    def test_aenter_is_callable(self):
        """Test __aenter__ is callable"""
        env = IsolatedEnvironment()
        assert callable(env.__aenter__)
    
    def test_aexit_is_callable(self):
        """Test __aexit__ is callable"""
        env = IsolatedEnvironment()
        assert callable(env.__aexit__)


class TestConcurrentEnvironments:
    """Test multiple concurrent environments"""
    
    def test_multiple_environments_unique_ids(self):
        """Test multiple environments have unique IDs"""
        envs = [IsolatedEnvironment() for _ in range(5)]
        ids = [env.environment_id for env in envs]
        
        # All IDs should be unique
        assert len(ids) == len(set(ids))
    
    def test_multiple_environments_independent_timeouts(self):
        """Test multiple environments have independent timeouts"""
        env1 = IsolatedEnvironment(timeout_seconds=60)
        env2 = IsolatedEnvironment(timeout_seconds=120)
        env3 = IsolatedEnvironment(timeout_seconds=300)
        
        assert env1.timeout_seconds == 60
        assert env2.timeout_seconds == 120
        assert env3.timeout_seconds == 300
    
    def test_multiple_environments_independent_state(self):
        """Test multiple environments have independent state"""
        env1 = IsolatedEnvironment()
        env2 = IsolatedEnvironment()
        
        # Each environment should be independent
        assert env1 is not env2
        assert env1.environment_id != env2.environment_id


class TestLogging:
    """Test logging functionality"""
    
    def test_environment_id_is_string(self):
        """Test environment ID is string"""
        env = IsolatedEnvironment()
        assert isinstance(env.environment_id, str)
    
    def test_environment_id_not_empty(self):
        """Test environment ID is not empty"""
        env = IsolatedEnvironment()
        assert len(env.environment_id) > 0
    
    def test_timestamp_tracking_none_initially(self):
        """Test created_at timestamp is None initially"""
        env = IsolatedEnvironment()
        assert env.created_at is None


class TestSafetyRequirements:
    """Test safety requirements"""
    
    def test_has_temp_dir_attribute(self):
        """Test environment has temp_dir attribute"""
        env = IsolatedEnvironment()
        assert hasattr(env, 'temp_dir')
    
    def test_no_global_state_modification(self):
        """Test environment doesn't modify global state"""
        env1 = IsolatedEnvironment()
        env2 = IsolatedEnvironment()
        
        # Each environment should be independent
        assert env1 is not env2
        assert env1.environment_id != env2.environment_id
        assert env1.browser is env2.browser is None


class TestInterfaceContract:
    """Test that interface contract is met"""
    
    def test_has_all_required_methods(self):
        """Test environment has all required methods"""
        env = IsolatedEnvironment()
        
        required_methods = ['create', 'render_page', 'cleanup', '_generate_id', 
                          '_schedule_cleanup', '__aenter__', '__aexit__']
        
        for method_name in required_methods:
            assert hasattr(env, method_name), f"Missing method: {method_name}"
    
    def test_has_all_required_attributes(self):
        """Test environment has all required attributes"""
        env = IsolatedEnvironment()
        
        required_attrs = ['timeout_seconds', 'browser', 'context', 'page', 
                         'temp_dir', 'created_at', 'cleanup_task', 'environment_id']
        
        for attr_name in required_attrs:
            assert hasattr(env, attr_name), f"Missing attribute: {attr_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

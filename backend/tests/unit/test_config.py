"""
Unit tests for configuration loading and validation.
"""

import os
import pytest
from app.core.config import Config, get_config


def test_config_default_values():
    """Test that Config uses sensible defaults."""
    config = Config()
    assert config.ENVIRONMENT == "dev"
    assert config.DEBUG == True
    assert config.HOST == "127.0.0.1"
    assert config.PORT == 8000
    assert config.SCAN_TIMEOUT_SECONDS == 30
    assert config.REPAIR_TIMEOUT_SECONDS == 20
    assert config.MAX_CONCURRENT_SCANS == 5
    assert config.MAX_REPAIRS_PER_SCAN == 10
    assert config.RATE_LIMIT == 600


def test_config_from_env_dev():
    """Test loading config from environment (dev)."""
    os.environ["ENVIRONMENT"] = "dev"
    os.environ["PORT"] = "9000"
    os.environ["SCAN_TIMEOUT_SECONDS"] = "45"
    
    config = Config.from_env()
    assert config.ENVIRONMENT == "dev"
    assert config.DEBUG == True
    assert config.PORT == 9000
    assert config.SCAN_TIMEOUT_SECONDS == 45
    assert config.LOG_LEVEL == "DEBUG"
    
    # Clean up
    del os.environ["ENVIRONMENT"]
    del os.environ["PORT"]
    del os.environ["SCAN_TIMEOUT_SECONDS"]


def test_config_from_env_prod():
    """Test loading config from environment (prod)."""
    os.environ["ENVIRONMENT"] = "prod"
    
    config = Config.from_env()
    assert config.ENVIRONMENT == "prod"
    assert config.DEBUG == False
    assert config.LOG_LEVEL == "INFO"
    assert config.LOG_FORMAT == "json"
    
    # Clean up
    del os.environ["ENVIRONMENT"]


def test_config_invalid_environment():
    """Test that invalid environment raises ValueError."""
    os.environ["ENVIRONMENT"] = "invalid"
    
    with pytest.raises(ValueError, match="ENVIRONMENT must be dev, test, or prod"):
        Config.from_env()
    
    # Clean up
    del os.environ["ENVIRONMENT"]


def test_config_parse_allowed_origins():
    """Test parsing comma-separated ALLOWED_ORIGINS."""
    os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000, http://example.com , https://app.example.com"
    
    config = Config.from_env()
    assert len(config.ALLOWED_ORIGINS) == 3
    assert "http://localhost:3000" in config.ALLOWED_ORIGINS
    assert "http://example.com" in config.ALLOWED_ORIGINS
    assert "https://app.example.com" in config.ALLOWED_ORIGINS
    
    # Clean up
    del os.environ["ALLOWED_ORIGINS"]


def test_config_get_logger():
    """Test logger creation and configuration."""
    config = Config(LOG_FORMAT="console", LOG_LEVEL="DEBUG")
    logger = config.get_logger("test_logger")
    
    assert logger is not None
    assert logger.name == "test_logger"
    assert logger.level == 10  # DEBUG level


def test_config_get_logger_json_format():
    """Test logger with JSON format."""
    config = Config(LOG_FORMAT="json", LOG_LEVEL="INFO")
    logger = config.get_logger("test_logger_json")
    
    assert logger is not None
    assert logger.name == "test_logger_json"


def test_get_config_singleton():
    """Test that get_config returns singleton instance."""
    config1 = get_config()
    config2 = get_config()
    
    assert config1 is config2
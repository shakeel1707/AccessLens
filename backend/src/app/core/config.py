"""
Configuration management for AccessLens backend.
Loads settings from environment variables with sensible defaults for dev/test/prod.
"""

import os
import logging
from typing import Literal
from dataclasses import dataclass, field


@dataclass
class Config:
    """Base configuration loaded from environment variables."""
    
    # Environment
    ENVIRONMENT: Literal["dev", "test", "prod"] = field(default="dev")
    
    # Server
    HOST: str = field(default="127.0.0.1")
    PORT: int = field(default=8000)
    DEBUG: bool = field(default=True)
    
    # Security & CORS
    ALLOWED_ORIGINS: list[str] = field(default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"])
    ALLOWED_DOMAINS: list[str] = field(default_factory=list)
    RATE_LIMIT: int = field(default=600)
    
    # Scanning
    SCAN_TIMEOUT_SECONDS: int = field(default=30)
    MAX_CONCURRENT_SCANS: int = field(default=5)
    
    # Repair
    REPAIR_TIMEOUT_SECONDS: int = field(default=20)
    MAX_REPAIRS_PER_SCAN: int = field(default=10)
    
    # Logging
    LOG_LEVEL: str = field(default="INFO")
    LOG_FORMAT: str = field(default="json")
    
    # CloudWatch
    ENABLE_CLOUDWATCH: bool = field(default=False)
    CLOUDWATCH_LOG_GROUP: str = field(default="/accesslens/backend")
    
    # AWS
    AWS_REGION: str = field(default="us-east-1")
    DYNAMODB_TABLE_SCANS: str = field(default="accesslens-scans")
    DYNAMODB_TABLE_FINDINGS: str = field(default="accesslens-findings")
    DYNAMODB_TABLE_REPAIRS: str = field(default="accesslens-repairs")
    DYNAMODB_TABLE_VERIFICATION: str = field(default="accesslens-verification")
    
    # S3
    S3_REPORTS_BUCKET: str = field(default="accesslens-reports")
    
    # Bedrock
    BEDROCK_MODEL_ID: str = field(default="anthropic.claude-3-sonnet-20240229-v1:0")
    
    # Feature flags
    USE_LOCAL_DYNAMODB: bool = field(default=True)
    LOCAL_DYNAMODB_ENDPOINT: str = field(default="http://localhost:8000")
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        env = os.getenv("ENVIRONMENT", "dev").lower()
        if env not in ("dev", "test", "prod"):
            raise ValueError(f"ENVIRONMENT must be dev, test, or prod; got {env}")
        
        debug = env in ("dev", "test")
        
        origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
        allowed_origins = [o.strip() for o in origins_str.split(",") if o.strip()]
        
        domains_str = os.getenv("ALLOWED_DOMAINS", "")
        allowed_domains = [d.strip() for d in domains_str.split(",") if d.strip()] if domains_str else []
        
        return cls(
            ENVIRONMENT=env,
            HOST=os.getenv("HOST", "127.0.0.1"),
            PORT=int(os.getenv("PORT", "8000")),
            DEBUG=debug,
            ALLOWED_ORIGINS=allowed_origins,
            ALLOWED_DOMAINS=allowed_domains,
            RATE_LIMIT=int(os.getenv("RATE_LIMIT", "600")),
            SCAN_TIMEOUT_SECONDS=int(os.getenv("SCAN_TIMEOUT_SECONDS", "30")),
            MAX_CONCURRENT_SCANS=int(os.getenv("MAX_CONCURRENT_SCANS", "5")),
            REPAIR_TIMEOUT_SECONDS=int(os.getenv("REPAIR_TIMEOUT_SECONDS", "20")),
            MAX_REPAIRS_PER_SCAN=int(os.getenv("MAX_REPAIRS_PER_SCAN", "10")),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "DEBUG" if debug else "INFO"),
            LOG_FORMAT=os.getenv("LOG_FORMAT", "console" if debug else "json"),
            ENABLE_CLOUDWATCH=os.getenv("ENABLE_CLOUDWATCH", "false").lower() == "true",
            CLOUDWATCH_LOG_GROUP=os.getenv("CLOUDWATCH_LOG_GROUP", "/accesslens/backend"),
            AWS_REGION=os.getenv("AWS_REGION", "us-east-1"),
            DYNAMODB_TABLE_SCANS=os.getenv("DYNAMODB_TABLE_SCANS", "accesslens-scans"),
            DYNAMODB_TABLE_FINDINGS=os.getenv("DYNAMODB_TABLE_FINDINGS", "accesslens-findings"),
            DYNAMODB_TABLE_REPAIRS=os.getenv("DYNAMODB_TABLE_REPAIRS", "accesslens-repairs"),
            DYNAMODB_TABLE_VERIFICATION=os.getenv("DYNAMODB_TABLE_VERIFICATION", "accesslens-verification"),
            S3_REPORTS_BUCKET=os.getenv("S3_REPORTS_BUCKET", "accesslens-reports"),
            BEDROCK_MODEL_ID=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0"),
            USE_LOCAL_DYNAMODB=os.getenv("USE_LOCAL_DYNAMODB", "true").lower() == "true",
            LOCAL_DYNAMODB_ENDPOINT=os.getenv("LOCAL_DYNAMODB_ENDPOINT", "http://localhost:8000"),
        )
    
    def get_logger(self, name: str = "accesslens") -> logging.Logger:
        """Get configured logger instance."""
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, self.LOG_LEVEL))
        logger.handlers.clear()
        
        if self.LOG_FORMAT == "json":
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "{\"time\": \"%(asctime)s\", \"level\": \"%(levelname)s\", \"logger\": \"%(name)s\", \"message\": \"%(message)s\"}"
            )
        else:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger


_config: Config | None = None


def get_config() -> Config:
    """Get or create global config instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config



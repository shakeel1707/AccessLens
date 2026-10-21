"""
Entry point for running the AccessLens backend server.
Loads configuration from environment and starts FastAPI server.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.main import create_app
from app.core.config import get_config

if __name__ == "__main__":
    import uvicorn
    
    config = get_config()
    app = create_app()
    
    print(f"Starting AccessLens API")
    print(f"Environment: {config.ENVIRONMENT}")
    print(f"Host: {config.HOST}:{config.PORT}")
    print(f"Debug: {config.DEBUG}")
    print(f"")
    
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower(),
    )
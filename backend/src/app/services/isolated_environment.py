"""
Isolated environment management for safe patch application.

Provides ephemeral Playwright contexts for patch testing without
modifying original files. Auto-cleanup on timeout or completion.
"""

import asyncio
import logging
import tempfile
import shutil
import os
from typing import Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
except ImportError:
    raise ImportError("playwright package required: pip install playwright")

logger = logging.getLogger("accesslens.isolated_env")


class IsolatedEnvironment:
    """Manages ephemeral Playwright context for patch application."""
    
    DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutes
    
    def __init__(self, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS):
        """Initialize isolated environment.
        
        Args:
            timeout_seconds: Auto-cleanup timeout (default 5 minutes)
        """
        self.timeout_seconds = timeout_seconds
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.temp_dir: Optional[str] = None
        self.created_at: Optional[datetime] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.environment_id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique environment ID."""
        return f"env-{datetime.utcnow().isoformat()}"
    
    async def create(self, url: str) -> Page:
        """Create isolated Playwright context.
        
        Args:
            url: Target URL to fetch
            
        Returns:
            Playwright page object in isolated context
            
        Raises:
            RuntimeError: If context creation fails
        """
        try:
            logger.info(f"Creating isolated environment {self.environment_id}")
            self.created_at = datetime.utcnow()
            
            # Create temp directory for this environment
            self.temp_dir = tempfile.mkdtemp(prefix="accesslens_env_")
            logger.info(f"Temp directory created: {self.temp_dir}")
            
            # Initialize Playwright browser
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch()
            logger.info(f"Browser launched for {self.environment_id}")
            
            # Create isolated context
            self.context = await self.browser.new_context()
            logger.info(f"Context created for {self.environment_id}")
            
            # Create page in isolated context
            self.page = await self.context.new_page()
            logger.info(f"Page created for {self.environment_id}")
            
            # Navigate to URL
            await self.page.goto(url, wait_until="domcontentloaded")
            logger.info(f"Page navigated to {url} in {self.environment_id}")
            
            # Start auto-cleanup timer
            self._schedule_cleanup()
            
            return self.page
        
        except Exception as e:
            logger.error(f"Failed to create isolated environment: {str(e)}")
            await self.cleanup()
            raise RuntimeError(f"Failed to create isolated environment: {str(e)}")
    
    async def render_page(self, html_content: str) -> Page:
        """Render HTML in isolated environment.
        
        Args:
            html_content: HTML to render
            
        Returns:
            Playwright page with rendered content
            
        Raises:
            RuntimeError: If rendering fails
        """
        if not self.page:
            raise RuntimeError("Environment not initialized")
        
        try:
            logger.info(f"Rendering HTML in {self.environment_id}")
            
            # Set page content (replaces existing content)
            await self.page.set_content(html_content)
            logger.info(f"HTML rendered in {self.environment_id}")
            
            # Reset cleanup timer
            self._schedule_cleanup()
            
            return self.page
        
        except Exception as e:
            logger.error(f"Failed to render page: {str(e)}")
            raise RuntimeError(f"Failed to render page: {str(e)}")
    
    def _schedule_cleanup(self) -> None:
        """Schedule auto-cleanup on timeout."""
        # Cancel existing cleanup task
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
        
        # Schedule new cleanup task
        self.cleanup_task = asyncio.create_task(self._auto_cleanup())
        logger.debug(f"Auto-cleanup scheduled for {self.environment_id} in {self.timeout_seconds}s")
    
    async def _auto_cleanup(self) -> None:
        """Auto-cleanup on timeout."""
        try:
            await asyncio.sleep(self.timeout_seconds)
            logger.warning(f"Auto-cleanup triggered for {self.environment_id} (timeout)")
            await self.cleanup()
        except asyncio.CancelledError:
            logger.debug(f"Auto-cleanup cancelled for {self.environment_id}")
        except Exception as e:
            logger.error(f"Error during auto-cleanup: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info(f"Cleaning up environment {self.environment_id}")
        
        try:
            # Cancel cleanup task
            if self.cleanup_task and not self.cleanup_task.done():
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Close page
            if self.page:
                try:
                    await self.page.close()
                    logger.info(f"Page closed for {self.environment_id}")
                except Exception as e:
                    logger.warning(f"Error closing page: {str(e)}")
            
            # Close context
            if self.context:
                try:
                    await self.context.close()
                    logger.info(f"Context closed for {self.environment_id}")
                except Exception as e:
                    logger.warning(f"Error closing context: {str(e)}")
            
            # Close browser
            if self.browser:
                try:
                    await self.browser.close()
                    logger.info(f"Browser closed for {self.environment_id}")
                except Exception as e:
                    logger.warning(f"Error closing browser: {str(e)}")
            
            # Clean temp directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                    logger.info(f"Temp directory removed: {self.temp_dir}")
                except Exception as e:
                    logger.warning(f"Error removing temp directory: {str(e)}")
            
            logger.info(f"Environment {self.environment_id} cleanup complete")
        
        except Exception as e:
            logger.error(f"Unexpected error during cleanup: {str(e)}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
        return False


@asynccontextmanager
async def create_isolated_environment(url: str, timeout_seconds: int = 300):
    """Context manager for isolated environment.
    
    Usage:
        async with create_isolated_environment("https://example.com") as env:
            page = await env.create(url)
            # Use page for testing
    
    Args:
        url: Target URL
        timeout_seconds: Auto-cleanup timeout
        
    Yields:
        IsolatedEnvironment instance
    """
    env = IsolatedEnvironment(timeout_seconds=timeout_seconds)
    try:
        await env.create(url)
        logger.info(f"Isolated environment ready: {env.environment_id}")
        yield env
    finally:
        await env.cleanup()

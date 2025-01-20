from typing import Optional, Any
import asyncio
from playwright.async_api import async_playwright, Browser, Playwright
from .structured_logging import StructuredLogger, setup_structured_logging

class BrowserController:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.init_promise: Optional[asyncio.Task] = None
        self.init_count: int = 0
        self._playwright: Optional[Playwright] = None
        self.logger = StructuredLogger("browser_controller")
        setup_structured_logging()

    async def initialize(self) -> None:
        """Initialize the browser if not already initialized."""
        if self.init_promise is not None:
            try:
                await self.init_promise
            except Exception as e:
                # If the current initialization fails, reset state to allow retry
                self.init_promise = None
                self.browser = None
                self.logger.log_browser_event("initialization_failed", {
                    "error": str(e),
                    "attempt": self.init_count + 1
                })
                raise

        if self.browser is not None:
            return

        # Create new initialization task
        self.logger.log_progress(
            step="browser_init",
            status="starting",
            progress=0.0,
            message="Starting browser initialization"
        )
        self.init_promise = asyncio.create_task(self._do_browser_init())
        try:
            await self.init_promise
            self.logger.log_progress(
                step="browser_init",
                status="completed",
                progress=1.0,
                message="Browser initialization completed"
            )
        except Exception as e:
            # Reset state on failure
            self.init_promise = None
            self.browser = None
            self.logger.log_progress(
                step="browser_init",
                status="failed",
                progress=0.0,
                message=f"Browser initialization failed: {str(e)}"
            )
            raise

    async def _do_browser_init(self) -> None:
        """Internal method to handle browser initialization."""
        if self.browser is not None:
            return

        self.logger.log_progress(
            step="browser_init",
            status="launching",
            progress=0.3,
            message="Launching Playwright"
        )
        playwright = await async_playwright().start()
        self._playwright = playwright
        
        try:
            self.logger.log_progress(
                step="browser_init",
                status="configuring",
                progress=0.6,
                message="Configuring browser"
            )
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox']
            )
            self.init_count += 1
            
            self.logger.log_browser_event("browser_launched", {
                "initialization_count": self.init_count,
                "headless": True
            })
            
        except Exception as e:
            await self._cleanup_playwright()
            self.logger.log_browser_event("launch_failed", {
                "error": str(e),
                "initialization_count": self.init_count
            })
            raise

    async def _cleanup_playwright(self) -> None:
        """Clean up the playwright context."""
        if self._playwright:
            self.logger.log_browser_event("cleanup_playwright", {
                "status": "starting"
            })
            await self._playwright.stop()
            self._playwright = None
            self.logger.log_browser_event("cleanup_playwright", {
                "status": "completed"
            })

    async def cleanup(self) -> None:
        """Clean up browser resources."""
        self.logger.log_progress(
            step="cleanup",
            status="starting",
            progress=0.0,
            message="Starting browser cleanup"
        )
        
        if self.browser:
            self.logger.log_progress(
                step="cleanup",
                status="closing_browser",
                progress=0.5,
                message="Closing browser"
            )
            await self.browser.close()
            self.browser = None
            
        await self._cleanup_playwright()
        self.init_promise = None
        self.init_count = 0
        
        self.logger.log_progress(
            step="cleanup",
            status="completed",
            progress=1.0,
            message="Browser cleanup completed"
        ) 
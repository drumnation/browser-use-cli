import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from src.utils.browser_controller import BrowserController

@pytest.fixture
async def browser_controller():
    controller = BrowserController()
    yield controller
    await controller.cleanup()

@pytest.mark.asyncio
async def test_single_initialization(browser_controller):
    mock_browser = AsyncMock()
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    
    with patch('src.utils.browser_controller.async_playwright', 
               return_value=AsyncMock(start=AsyncMock(return_value=mock_playwright))) as mock_async_playwright:
        await browser_controller.initialize()
        assert browser_controller.init_count == 1
        assert browser_controller.browser == mock_browser
        
        # Verify progress events
        progress_history = browser_controller.logger.get_progress_history()
        assert len(progress_history) >= 2  # At least start and complete events
        assert progress_history[0]["status"] == "starting"
        assert progress_history[-1]["status"] == "completed"
        assert progress_history[-1]["progress"] == 1.0
        
        # Second initialization should not create new browser
        await browser_controller.initialize()
        assert browser_controller.init_count == 1
        mock_async_playwright.assert_called_once()

@pytest.mark.asyncio
async def test_concurrent_initialization(browser_controller):
    mock_browser = AsyncMock()
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    
    with patch('src.utils.browser_controller.async_playwright', 
               return_value=AsyncMock(start=AsyncMock(return_value=mock_playwright))):
        # Start multiple concurrent initializations
        tasks = [browser_controller.initialize() for _ in range(3)]
        await asyncio.gather(*tasks)
        
        # Should only initialize once
        assert browser_controller.init_count == 1
        assert browser_controller.browser == mock_browser
        
        # Verify browser events
        browser_events = browser_controller.logger.get_browser_events()
        launch_events = [e for e in browser_events if e["event_type"] == "browser_launched"]
        assert len(launch_events) == 1

@pytest.mark.asyncio
async def test_browser_launch_options(browser_controller):
    mock_browser = AsyncMock()
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    
    with patch('src.utils.browser_controller.async_playwright', 
               return_value=AsyncMock(start=AsyncMock(return_value=mock_playwright))) as mock_async_playwright:
        await browser_controller.initialize()
        
        # Verify launch options
        mock_playwright.chromium.launch.assert_called_once_with(
            headless=True,
            args=['--no-sandbox']
        )
        
        # Verify browser events
        browser_events = browser_controller.logger.get_browser_events()
        launch_event = next(e for e in browser_events if e["event_type"] == "browser_launched")
        assert launch_event["details"]["headless"] is True

@pytest.mark.asyncio
async def test_initialization_failure(browser_controller):
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch = AsyncMock(side_effect=Exception("Browser launch failed"))
    
    with patch('src.utils.browser_controller.async_playwright', 
               return_value=AsyncMock(start=AsyncMock(return_value=mock_playwright))), \
         pytest.raises(Exception, match="Browser launch failed"):
        await browser_controller.initialize()
    
    assert browser_controller.browser is None
    assert browser_controller.init_count == 0
    
    # Verify error events
    browser_events = browser_controller.logger.get_browser_events()
    error_event = next(e for e in browser_events if e["event_type"] == "launch_failed")
    assert "Browser launch failed" in error_event["details"]["error"]
    
    # Verify progress events show failure
    progress_events = browser_controller.logger.get_progress_history()
    final_event = progress_events[-1]
    assert final_event["status"] == "failed"
    assert final_event["progress"] == 0.0

@pytest.mark.asyncio
async def test_browser_cleanup(browser_controller):
    mock_browser = AsyncMock()
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    
    with patch('src.utils.browser_controller.async_playwright', 
               return_value=AsyncMock(start=AsyncMock(return_value=mock_playwright))):
        await browser_controller.initialize()
        assert browser_controller.browser is not None
        
        await browser_controller.cleanup()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()
        assert browser_controller.browser is None
        assert browser_controller._playwright is None
        
        # Verify cleanup events
        progress_events = browser_controller.logger.get_progress_history()
        cleanup_events = [e for e in progress_events if e["step"] == "cleanup"]
        assert len(cleanup_events) >= 2  # At least start and complete events
        assert cleanup_events[0]["status"] == "starting"
        assert cleanup_events[-1]["status"] == "completed"
        assert cleanup_events[-1]["progress"] == 1.0 
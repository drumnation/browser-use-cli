import sys
from pathlib import Path
import tempfile
import logging

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import asyncio
import os
from cli.browser_use_cli import initialize_browser, run_browser_task, close_browser, main, _global_browser, _global_browser_context

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reset global state before each test
@pytest.fixture(autouse=True)
async def cleanup():
    """Ensure proper cleanup of browser and event loop between tests"""
    global _global_browser, _global_browser_context
    
    logger.info(f"Cleanup start - Browser state: {_global_browser is not None}")
    
    # Reset globals before test
    _global_browser = None
    _global_browser_context = None
    
    logger.info("Globals reset before test")
    
    try:
        yield
    finally:
        try:
            logger.info(f"Cleanup finally - Browser state: {_global_browser is not None}")
            if _global_browser is not None:
                await close_browser()
                logger.info("Browser closed")
                # Clean up any remaining event loop resources
                loop = asyncio.get_event_loop()
                tasks = [t for t in asyncio.all_tasks(loop=loop) if not t.done()]
                if tasks:
                    logger.info(f"Found {len(tasks)} pending tasks")
                    for task in tasks:
                        if not task.cancelled():
                            task.cancel()
                    logger.info("Tasks cancelled")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        finally:
            # Always reset globals after test
            _global_browser = None
            _global_browser_context = None
            logger.info("Globals reset after test")

class TestBrowserInitialization:
    """Test browser launch-time options"""
    
    async def test_basic_initialization(self):
        """Test basic browser initialization with defaults"""
        success = await initialize_browser()
        assert success is True
        
    async def test_window_size(self):
        """Test custom window size"""
        success = await initialize_browser(window_size=(800, 600))
        assert success is True
        
        # Create a simple HTML page that displays window size
        result = await run_browser_task(
            "go to data:text/html,<script>document.write('Window size: ' + window.innerWidth + 'x' + window.innerHeight)</script>",
            model="deepseek-chat"
        )
        assert result is not None and "800" in result.lower() and "600" in result.lower()
        
    async def test_headless_mode(self):
        """Test headless mode"""
        success = await initialize_browser(headless=True)
        assert success is True
        # Verify we can still run tasks
        result = await run_browser_task(
            "go to example.com and tell me the title",
            model="deepseek-chat"
        )
        assert result is not None and "example" in result.lower()
        
    async def test_user_data_dir(self, tmp_path):
        """Test custom user data directory"""
        user_data = tmp_path / "chrome_data"
        user_data.mkdir()
        success = await initialize_browser(user_data_dir=str(user_data))
        assert success is True
        assert user_data.exists()
        
    async def test_proxy_configuration(self):
        """Test proxy configuration"""
        # Using a test proxy - in practice you'd use a real proxy server
        test_proxy = "localhost:8080"
        success = await initialize_browser(proxy=test_proxy)
        assert success is True
        
    @pytest.mark.timeout(30)  # Add 30 second timeout
    async def test_disable_security(self):
        """Test security disable option"""
        success = await initialize_browser(disable_security=True)
        assert success is True
        # Try accessing a cross-origin resource that would normally be blocked
        result = await run_browser_task(
            "go to a test page and try to access cross-origin content",
            model="deepseek-chat",
            max_steps=5  # Limit steps to prevent timeout
        )
        assert result is not None and "error" not in result.lower()
        
    async def test_multiple_initialization(self):
        """Test that second initialization fails while browser is running"""
        success1 = await initialize_browser()
        assert success1 is True
        success2 = await initialize_browser()
        assert success2 is False

class TestBrowserTasks:
    """Test runtime task options"""
    
    @pytest.fixture(autouse=True)
    async def setup_browser(self):
        """Start browser before each test"""
        await initialize_browser()
        yield
    
    @pytest.fixture
    def local_test_page(self):
        """Create a local HTML file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test Page</title>
            </head>
            <body>
                <h1>Test Content</h1>
                <p>This is a test paragraph with specific content.</p>
                <button id="testButton">Click Me</button>
                <div id="result"></div>
            </body>
            </html>
            """)
            return f.name

    async def test_model_switching(self):
        """Test switching between different LLM models"""
        # Test DeepSeek - Note: 422 errors are expected but don't affect functionality
        try:
            result1 = await run_browser_task(
                "go to example.com and summarize the page",
                model="deepseek-chat"
            )
            assert result1 is not None
        except Exception as e:
            if "422" not in str(e):  # Only ignore 422 errors
                raise
        
        # Test Gemini
        result2 = await run_browser_task(
            "what do you see on the page?",
            model="gemini",
            vision=True
        )
        assert result2 is not None and len(result2) > 0
        assert result1 is not None and len(result1) > 0
        assert result1 != result2  # Different models should give different responses
        
    async def test_vision_capability(self):
        """Test vision capabilities"""
        # Without vision
        result1 = await run_browser_task(
            "what do you see on example.com?",
            model="gemini",
            vision=False
        )
        
        # With vision
        result2 = await run_browser_task(
            "what do you see on example.com?",
            model="gemini",
            vision=True
        )
        
        assert result1 is not None and result2 is not None and len(result2) > len(result1)  # Vision should provide more details
        
    async def test_recording(self, tmp_path):
        """Test session recording"""
        record_path = tmp_path / "recordings"
        record_path.mkdir()
        
        await run_browser_task(
            "go to example.com",
            record=True,
            record_path=str(record_path)
        )
        
        # Check that recording file was created
        recordings = list(record_path.glob("*.webm"))
        assert len(recordings) > 0
        
    async def test_tracing(self, tmp_path):
        """Test debug tracing"""
        trace_path = tmp_path / "traces"
        trace_path.mkdir()
        
        await run_browser_task(
            "go to example.com",
            trace_path=str(trace_path)
        )
        
        # Check that trace file was created
        traces = list(trace_path.glob("*.zip"))
        assert len(traces) > 0
        
    async def test_max_steps_limit(self):
        """Test max steps limitation"""
        with pytest.raises(Exception):
            # This task would normally take more than 2 steps
            await run_browser_task(
                "go to google.com, search for 'OpenAI', click first result",
                max_steps=2
            )
            
    async def test_max_actions_limit(self):
        """Test max actions per step limitation"""
        with pytest.raises(Exception):
            # This would require multiple actions in one step
            await run_browser_task(
                "go to google.com and click all search results",
                max_actions=1
            )
            
    async def test_additional_context(self):
        """Test providing additional context"""
        result = await run_browser_task(
            "summarize the content",
            add_info="Focus on technical details and pricing information"
        )
        assert result is not None and ("technical" in result.lower() or "pricing" in result.lower())

    async def test_report_generation(self, local_test_page):
        """Test that the agent can analyze a page and return a report"""
        logger.info("Starting report generation test")
        
        # Check initial state
        logger.info(f"Initial browser state: {_global_browser is not None}")
        
        # Initialize browser
        success = await initialize_browser()
        logger.info(f"Browser initialization result: {success}")
        
        assert success is True, "Browser initialization failed"
        
        # Create the task prompt
        prompt = f"Go to file://{local_test_page} and create a report about the page structure, including any interactive elements found"
        
        try:
            result = await run_browser_task(
                prompt=prompt,
                model="deepseek-chat",
                max_steps=3
            )
            
            logger.info(f"Received report: {result}")
            
            # Verify the report contains expected information
            assert result is not None
            assert "Test Content" in result
            assert "button" in result.lower()
            assert "paragraph" in result.lower()
            
            logger.info("Report verification successful")
            
        except Exception as e:
            logger.error(f"Error during report generation: {e}")
            raise
        finally:
            # Cleanup
            os.unlink(local_test_page)
            logger.info("Test cleanup completed")

class TestBrowserLifecycle:
    """Test browser lifecycle management"""
    
    async def test_close_and_reopen(self):
        """Test closing and reopening browser"""
        # First session
        success1 = await initialize_browser()
        assert success1 is True
        result1 = await run_browser_task("go to example.com")
        assert result1 is not None
        await close_browser()
        
        # Second session
        success2 = await initialize_browser()
        assert success2 is True
        result2 = await run_browser_task("go to example.com")
        assert result2 is not None
        
    async def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test running task without browser
        with pytest.raises(Exception):
            await run_browser_task("this should fail")
            
        # Test closing already closed browser
        await close_browser()
        await close_browser()  # Should not raise error
        
        # Test recovery after error
        success = await initialize_browser()
        assert success is True
        result = await run_browser_task("go to example.com")
        assert result is not None

def test_cli_commands():
    """Test CLI command parsing"""
    import sys
    from io import StringIO
    
    # Test start command
    output = StringIO()
    sys.stdout = output
    sys.argv = ["browser-use", "start", "--window-size", "800x600"]
    from cli.browser_use_cli import main
    main()
    assert "Browser session started successfully" in output.getvalue()
    
    # Test run command
    output = StringIO()
    sys.stdout = output
    sys.argv = ["browser-use", "run", "go to example.com", "--model", "deepseek-chat"]
    main()
    assert len(output.getvalue()) > 0
    
    # Test close command
    output = StringIO()
    sys.stdout = output
    sys.argv = ["browser-use", "close"]
    main()
    assert "Browser session closed" in output.getvalue()
    
    # Restore stdout
    sys.stdout = sys.__stdout__ 
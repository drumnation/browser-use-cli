import os
import pytest
from dotenv import load_dotenv
from src.utils import utils
from cli.browser_use_cli import run_browser_task

# Load environment variables
load_dotenv()

@pytest.mark.asyncio
class TestBrowserVision:
    """Test browser automation with vision capabilities"""

    async def setup_method(self):
        """Setup test environment"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            pytest.skip("OPENAI_API_KEY not set")

    async def test_vision_analysis_task(self):
        """Test visual analysis of a webpage"""
        result = await run_browser_task(
            prompt="go to https://example.com and describe the visual layout of the page",
            provider="OpenAI",
            vision=True,
            headless=True,  # Run headless for CI/CD
            record=True,  # Record for debugging
            record_path="./tmp/test_recordings"
        )
        assert result is not None
        assert "layout" in result.lower() or "design" in result.lower()

    async def test_vision_interaction_task(self):
        """Test visual-guided interaction"""
        result = await run_browser_task(
            prompt="go to https://example.com and click on the most prominent link on the page",
            provider="OpenAI",
            vision=True,
            headless=True,
            record=True,
            record_path="./tmp/test_recordings"
        )
        assert result is not None
        assert "clicked" in result.lower() or "selected" in result.lower()

    async def test_vision_verification_task(self):
        """Test visual verification of page state"""
        result = await run_browser_task(
            prompt="go to https://example.com and verify that the main heading is visible and centered",
            provider="OpenAI",
            vision=True,
            headless=True,
            record=True,
            record_path="./tmp/test_recordings"
        )
        assert result is not None
        assert "heading" in result.lower() and ("visible" in result.lower() or "centered" in result.lower())

    async def test_vision_error_handling(self):
        """Test error handling with vision tasks"""
        # Test with a non-existent page to verify error handling
        result = await run_browser_task(
            prompt="go to https://nonexistent.example.com and describe what you see",
            provider="OpenAI",
            vision=True,
            headless=True,
            record=True,
            record_path="./tmp/test_recordings"
        )
        assert result is not None
        assert "error" in result.lower() or "unable" in result.lower() or "failed" in result.lower()

    async def test_vision_with_different_models(self):
        """Test vision capabilities with different providers"""
        test_configs = [
            "OpenAI",  # Will use gpt-4o
            "Google",  # Will use gemini-pro
            "Anthropic"  # Will use claude-3-5-sonnet-20241022
        ]
        
        for provider in test_configs:
            result = await run_browser_task(
                prompt="go to https://example.com and describe the page layout",
                provider=provider,
                vision=True,
                headless=True,
                record=True,
                record_path=f"./tmp/test_recordings/{provider.lower()}"
            )
            assert result is not None
            assert len(result) > 0, f"Failed with provider {provider}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
import pytest
import asyncio
from pathlib import Path
from urllib.parse import urlparse
from cli.browser_use_cli import run_browser_task, initialize_browser, close_browser

@pytest.fixture
async def browser_session():
    """Fixture to manage browser session for tests"""
    await initialize_browser(headless=True)
    yield
    await close_browser()

@pytest.mark.asyncio
async def test_url_validation():
    """Test URL validation in run_browser_task"""
    # Test invalid URLs
    invalid_urls = [
        "not-a-url",
        "http://",
        "https://",
        "ftp://example.com",  # non-http(s) protocol
        "",
        None
    ]
    
    for url in invalid_urls:
        result = await run_browser_task(
            prompt="test task",
            url=url,
            provider="Deepseek",
            headless=True
        )
        assert "Invalid URL provided" in result

    # Test valid URLs
    valid_urls = [
        "https://example.com",
        "http://localhost:8080",
        "https://prompt-forge.replit.app/"
    ]
    
    for url in valid_urls:
        result = await run_browser_task(
            prompt="test task",
            url=url,
            provider="Deepseek",
            headless=True
        )
        assert "Invalid URL provided" not in result

@pytest.mark.asyncio
async def test_url_navigation(browser_session):
    """Test that the browser actually navigates to the provided URL"""
    url = "https://example.com"
    result = await run_browser_task(
        prompt="verify the page title contains 'Example'",
        url=url,
        provider="Deepseek",
        headless=True,
        max_steps=3
    )
    assert "success" in result.lower() or "verified" in result.lower()

@pytest.mark.asyncio
async def test_url_in_prompt():
    """Test that the URL is correctly prepended to the task prompt"""
    url = "https://example.com"
    test_prompt = "click the button"
    result = await run_browser_task(
        prompt=test_prompt,
        url=url,
        provider="Deepseek",
        headless=True
    )
    
    # The result should indicate navigation happened first
    assert "navigated" in result.lower() or "loaded" in result.lower()

@pytest.mark.asyncio
async def test_multiple_tasks_same_url(browser_session):
    """Test running multiple tasks with the same starting URL"""
    url = "https://example.com"
    tasks = [
        "verify the page has loaded",
        "check if there are any links on the page",
        "look for a search box"
    ]
    
    for task in tasks:
        result = await run_browser_task(
            prompt=task,
            url=url,
            provider="Deepseek",
            headless=True,
            max_steps=3
        )
        assert result is not None
        assert isinstance(result, str)

@pytest.mark.asyncio
async def test_url_with_different_providers():
    """Test URL handling with different providers"""
    url = "https://example.com"
    providers = ["Deepseek", "Google", "Anthropic"]
    
    for provider in providers:
        result = await run_browser_task(
            prompt="verify the page has loaded",
            url=url,
            provider=provider,
            headless=True,
            max_steps=3
        )
        assert result is not None
        assert isinstance(result, str)
        assert "Invalid URL provided" not in result 
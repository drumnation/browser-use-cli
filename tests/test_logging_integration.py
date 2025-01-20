import json
import logging
import pytest
import asyncio
from pathlib import Path
from io import StringIO
from typing import Dict, Any, List, Optional

from src.utils.logging import LogFormatter, BatchedEventLogger, setup_logging
from src.agent.custom_agent import CustomAgent
from browser_use.agent.views import ActionResult
from browser_use.browser.views import BrowserStateHistory
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

class MockElementTree:
    def clickable_elements_to_string(self, include_attributes=None):
        return "Mock clickable elements"

class MockBrowserContext(BrowserContext):
    def __init__(self):
        self.config = BrowserContextConfig()
        self.selector_map = {}
        self.cached_state = BrowserStateHistory(
            url="https://example.com",
            title="Example Page",
            tabs=[],
            interacted_element=[None],
            screenshot=None
        )
        setattr(self.cached_state, 'selector_map', self.selector_map)
        setattr(self.cached_state, 'element_tree', MockElementTree())

    async def get_state(self, use_vision=True):
        return self.cached_state

    async def close(self):
        pass

    def __del__(self):
        # Override to prevent errors about missing session attribute
        pass

class MockBrowser(Browser):
    def __init__(self):
        self.config = BrowserConfig()
        
    async def new_context(self, config):
        return MockBrowserContext()

    async def close(self):
        pass

class MockLLM(BaseChatModel):
    def with_structured_output(self, output_type, include_raw=False):
        self._output_type = output_type
        return self

    async def ainvoke(self, messages: List[BaseMessage], **kwargs):
        return {
            'parsed': self._output_type(
                action=[],
                current_state={
                    'prev_action_evaluation': 'Success',
                    'important_contents': 'Test memory',
                    'completed_contents': 'Test progress',
                    'thought': 'Test thought',
                    'summary': 'Test summary'
                }
            )
        }
        
    @property
    def _llm_type(self) -> str:
        return "mock"
        
    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, run_manager = None, **kwargs):
        raise NotImplementedError("Use ainvoke instead")
        
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"mock_param": True}

class ErrorLLM(MockLLM):
    async def ainvoke(self, messages: List[BaseMessage], **kwargs):
        raise ValueError("Test error")

class ActionLLM(MockLLM):
    async def ainvoke(self, messages: List[BaseMessage], **kwargs):
        return {
            'parsed': self._output_type(
                action=[
                    {'type': 'click', 'selector': '#button1'},
                    {'type': 'type', 'selector': '#input1', 'text': 'test'},
                ],
                current_state={
                    'prev_action_evaluation': 'Success',
                    'important_contents': 'Test memory',
                    'completed_contents': 'Test progress',
                    'thought': 'Test thought',
                    'summary': 'Test summary'
                }
            )
        }

@pytest.fixture
def logger():
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Configure test logger
    logger = logging.getLogger("test_integration")
    logger.setLevel(logging.INFO)
    return logger

@pytest.fixture
def string_io():
    string_io = StringIO()
    handler = logging.StreamHandler(string_io)
    handler.setFormatter(LogFormatter(use_json=True))
    
    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    
    # Add handler to test logger
    logger = logging.getLogger("test_integration")
    logger.addHandler(handler)
    
    yield string_io
    
    # Clean up
    root_logger.removeHandler(handler)
    logger.removeHandler(handler)

@pytest.mark.asyncio
async def test_agent_logging_integration(logger, string_io):
    # Setup
    agent = CustomAgent(
        task="Test task",
        llm=MockLLM(),
        browser=MockBrowser(),
        browser_context=MockBrowserContext(),
        use_vision=True
    )

    # Execute a step
    await agent.step()

    # Get all log output
    log_output = string_io.getvalue()
    log_entries = [json.loads(line) for line in log_output.strip().split('\n') if line.strip()]

    # Print log entries for debugging
    print("\nLog entries:", log_entries)

    # Verify log entries
    assert len(log_entries) > 0
    assert any('Starting step 1' in str(entry.get('msg', '')) for entry in log_entries)
    assert any('Model Response: success' in str(entry.get('msg', '')) for entry in log_entries)
    assert any('Step error' in str(entry.get('msg', '')) for entry in log_entries)

@pytest.mark.asyncio
async def test_agent_error_logging(logger, string_io):
    # Setup
    agent = CustomAgent(
        task="Test task",
        llm=ErrorLLM(),
        browser=MockBrowser(),
        browser_context=MockBrowserContext(),
        use_vision=True
    )

    # Execute a step
    await agent.step()

    # Get all log output
    log_output = string_io.getvalue()
    log_entries = [json.loads(line) for line in log_output.strip().split('\n') if line.strip()]

    # Print log entries for debugging
    print("\nLog entries:", log_entries)

    # Verify log entries
    assert len(log_entries) > 0
    assert any('Starting step 1' in str(entry.get('msg', '')) for entry in log_entries)
    assert any('Step error' in str(entry.get('msg', '')) for entry in log_entries)
    assert any('Use ainvoke instead' in str(entry.get('msg', '')) for entry in log_entries)

@pytest.mark.asyncio
async def test_agent_batched_logging(logger, string_io):
    # Setup
    agent = CustomAgent(
        task="Test task",
        llm=ActionLLM(),
        browser=MockBrowser(),
        browser_context=MockBrowserContext(),
        use_vision=True
    )

    # Execute a step
    await agent.step()

    # Get all log output
    log_output = string_io.getvalue()
    log_entries = [json.loads(line) for line in log_output.strip().split('\n') if line.strip()]

    # Print log entries for debugging
    print("\nLog entries:", log_entries)

    # Verify log entries
    assert len(log_entries) > 0
    assert any('Starting step 1' in str(entry.get('msg', '')) for entry in log_entries)
    assert any('Model Response: success' in str(entry.get('msg', '')) for entry in log_entries)
    assert any('Batch: 2 action events' in str(entry.get('msg', '')) for entry in log_entries)
    assert any('Step error' in str(entry.get('msg', '')) for entry in log_entries) 
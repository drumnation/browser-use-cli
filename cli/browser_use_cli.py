#!/usr/bin/env python3
import asyncio
import argparse
import os
import sys
from pathlib import Path
import json
import tempfile

# Add the project root to PYTHONPATH
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig, BrowserContextWindowSize
from src.agent.custom_agent import CustomAgent
from src.controller.custom_controller import CustomController
from src.agent.custom_prompts import CustomSystemPrompt
from src.utils import utils
from dotenv import load_dotenv

# Load .env from the project root
load_dotenv(Path(project_root) / '.env')

# Global variables for browser persistence
_global_browser = None
_global_browser_context = None

def _get_browser_state():
    """Get browser state from temporary file."""
    temp_file = os.path.join(tempfile.gettempdir(), "browser_use_state")
    try:
        with open(temp_file, "r") as f:
            return f.read().strip().lower() == "true"
    except FileNotFoundError:
        return False

def _set_browser_state(running=True, temp_file_path=None):
    """Set browser state in a temporary file."""
    value = str(running).lower()
    if temp_file_path:
        with open(temp_file_path, "w") as f:
            f.write(value)

async def initialize_browser(
    headless=False,
    window_size=(1920, 1080),
    disable_security=False,
    user_data_dir=None,
    proxy=None
):
    """Initialize a new browser instance with the given configuration."""
    global _global_browser, _global_browser_context
    
    # Check both environment and global variables
    if _get_browser_state() or _global_browser is not None:
        # Close any existing browser first
        if _global_browser is not None:
            await close_browser()
        else:
            _set_browser_state(False)
        
    window_w, window_h = window_size
    
    # Initialize browser with launch-time options
    browser = Browser(
        config=BrowserConfig(
            headless=headless,
            disable_security=disable_security,
            chrome_instance_path=user_data_dir,
            extra_chromium_args=[f"--window-size={window_w},{window_h}"],
            proxy=proxy
        )
    )
    
    # Create initial browser context
    browser_context = await browser.new_context(
        config=BrowserContextConfig(
            no_viewport=False,
            browser_window_size=BrowserContextWindowSize(
                width=window_w,
                height=window_h
            ),
            disable_security=disable_security
        )
    )
    
    # Store globally
    _global_browser = browser
    _global_browser_context = browser_context
    _set_browser_state(True)
    return True

async def close_browser():
    """Close the current browser instance if one exists."""
    global _global_browser, _global_browser_context
    
    if _global_browser_context is not None:
        await _global_browser_context.close()
        _global_browser_context = None
        
    if _global_browser is not None:
        await _global_browser.close()
        _global_browser = None
    
    _set_browser_state(False)

async def run_browser_task(
    prompt, 
    provider="Deepseek",
    model_index=None,
    vision=False,
    record=False,
    record_path=None,
    trace_path=None,
    max_steps=10,
    max_actions=1,
    add_info="",
    on_init=None,
    headless=False,
    window_size=(1920, 1080),
    disable_security=False,
    user_data_dir=None,
    proxy=None
):
    """Execute a task using the current browser instance, auto-initializing if needed."""
    global _global_browser, _global_browser_context
    
    # Check if browser is running and initialize if needed
    if not _get_browser_state():
        print("Browser not running. Starting browser session...")
        if not await initialize_browser(
            headless=headless,
            window_size=window_size,
            disable_security=disable_security,
            user_data_dir=user_data_dir,
            proxy=proxy
        ):
            return "Browser initialization failed"
        
        # Signal successful initialization if callback provided
        if _get_browser_state() and on_init:
            await on_init()
    
    # Verify browser state is consistent
    if _global_browser is None or _global_browser_context is None:
        print("Browser session state is inconsistent. Attempting to reinitialize...")
        if not await initialize_browser(
            headless=headless,
            window_size=window_size,
            disable_security=disable_security,
            user_data_dir=user_data_dir,
            proxy=proxy
        ):
            return "Browser reinitialization failed"
        if _global_browser is None or _global_browser_context is None:
            return "Browser session state remains inconsistent after reinitialization"

    # Initialize controller
    controller = CustomController()

    # Normalize provider name to lowercase for consistency
    provider = provider.lower()

    # Select appropriate model based on provider, model_index, and vision requirement
    if provider not in utils.model_names:
        raise ValueError(f"Unsupported provider: {provider}")

    available_models = utils.model_names[provider]
    
    if model_index is not None:
        if not (0 <= model_index < len(available_models)):
            raise ValueError(f"Invalid model_index {model_index} for provider {provider}. Available indices: 0-{len(available_models)-1}")
        model_name = available_models[model_index]
    else:
        # Default model selection based on vision requirement
        if provider == "deepseek":
            model_name = available_models[0]  # deepseek-chat
        elif provider == "google":
            model_name = available_models[0]  # gemini-1.5-pro
        elif provider == "openai":
            model_name = available_models[0]  # gpt-4o
        elif provider == "anthropic":
            model_name = available_models[0]  # claude-3-5-sonnet-latest

    # Get LLM model
    llm = utils.get_llm_model(
        provider=provider,
        model_name=model_name,
        temperature=0.8,
        vision=vision
    )

    # Create new context with tracing/recording enabled
    if record or trace_path:
        # Close existing context first
        if _global_browser_context is not None:
            await _global_browser_context.close()
        
        # Create new context with tracing/recording enabled
        if trace_path:
            trace_dir = Path(trace_path)
            trace_dir.mkdir(parents=True, exist_ok=True)
            trace_file = str(trace_dir / "trace.zip")
        else:
            trace_file = None

        _global_browser_context = await _global_browser.new_context(
            config=BrowserContextConfig(
                trace_path=trace_file,
                save_recording_path=str(record_path) if record else None,
                no_viewport=False,
                browser_window_size=BrowserContextWindowSize(
                    width=1920,
                    height=1080
                ),
                disable_security=False
            )
        )

    try:
        # Create and run agent
        agent = CustomAgent(
            task=prompt,
            add_infos=add_info,
            llm=llm,
            browser=_global_browser,
            browser_context=_global_browser_context,
            controller=controller,
            system_prompt_class=CustomSystemPrompt,
            use_vision=vision,
            tool_call_in_content=True,
            max_actions_per_step=max_actions
        )

        history = await agent.run(max_steps=max_steps)
        result = history.final_result()

        # Close the context if tracing was enabled
        if trace_path:
            await _global_browser_context.close()
            _global_browser_context = None

        return result
    except Exception as e:
        # Close the context if tracing was enabled
        if trace_path:
            await _global_browser_context.close()
            _global_browser_context = None
        raise e

def main():
    parser = argparse.ArgumentParser(description="Control a browser using natural language")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start a new browser session")
    start_parser.add_argument("--temp-file", help="Path to temporary file for storing browser state")
    start_parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    start_parser.add_argument("--window-size", default="1920x1080", help="Browser window size (WxH)")
    start_parser.add_argument("--disable-security", action="store_true", help="Disable browser security features")
    start_parser.add_argument("--user-data-dir", help="Use custom Chrome profile directory")
    start_parser.add_argument("--proxy", help="Proxy server URL")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run a task in the current browser session")
    run_parser.add_argument("--temp-file", help="Path to temporary file for storing browser state")
    run_parser.add_argument("prompt", help="The task to perform")
    run_parser.add_argument("--provider", "-p", choices=["Deepseek", "Google", "OpenAI", "Anthropic"], 
                           default="Deepseek", help="The LLM provider to use (system will select appropriate model)")
    run_parser.add_argument("--model-index", "-m", type=int,
                           help="Optional index to select a specific model from the provider's available models (0-based)")
    run_parser.add_argument("--vision", action="store_true", help="Enable vision capabilities")
    run_parser.add_argument("--record", action="store_true", help="Enable session recording")
    run_parser.add_argument("--record-path", default="./tmp/record_videos", help="Path to save recordings")
    run_parser.add_argument("--trace-path", default="./tmp/traces", help="Path to save debugging traces")
    run_parser.add_argument("--max-steps", type=int, default=10, help="Maximum number of steps per task")
    run_parser.add_argument("--max-actions", type=int, default=1, help="Maximum actions per step")
    run_parser.add_argument("--add-info", help="Additional context for the agent")
    
    # Close command
    close_parser = subparsers.add_parser("close", help="Close the current browser session")
    close_parser.add_argument("--temp-file", help="Path to temporary file for storing browser state")

    args = parser.parse_args()
    
    if args.command == "start":
        # Parse window size
        try:
            window_w, window_h = map(int, args.window_size.split('x'))
        except ValueError:
            print(f"Invalid window size format: {args.window_size}. Using default 1920x1080")
            window_w, window_h = 1920, 1080
            
        # Start browser
        success = asyncio.run(initialize_browser(
            headless=args.headless,
            window_size=(window_w, window_h),
            disable_security=args.disable_security,
            user_data_dir=args.user_data_dir,
            proxy=args.proxy
        ))
        if success:
            print("Browser session started successfully")
            _set_browser_state(True, args.temp_file)
        else:
            print("Failed to start browser session")
            _set_browser_state(False, args.temp_file)
            
    elif args.command == "run":
        # Run task
        result = asyncio.run(run_browser_task(
            prompt=args.prompt,
            provider=args.provider,
            model_index=args.model_index,
            vision=args.vision,
            record=args.record,
            record_path=args.record_path if args.record else None,
            trace_path=args.trace_path,
            max_steps=args.max_steps,
            max_actions=args.max_actions,
            add_info=args.add_info,
            headless=False,
            window_size=(1920, 1080),
            disable_security=False,
            user_data_dir=None,
            proxy=None
        ))
        if result:
            print(result)
        
    elif args.command == "close":
        # Close browser
        asyncio.run(close_browser())
        print("Browser session closed")
        _set_browser_state(False, args.temp_file)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 
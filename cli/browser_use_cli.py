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
    """Get browser state from environment."""
    return os.environ.get("BROWSER_USE_RUNNING", "false").lower() == "true"

def _set_browser_state(running=True):
    """Set browser state in environment."""
    os.environ["BROWSER_USE_RUNNING"] = str(running).lower()

async def initialize_browser(
    headless=False,
    window_size=(1920, 1080),
    disable_security=False,
    user_data_dir=None,
    proxy=None
):
    """Initialize a new browser instance with the given configuration."""
    global _global_browser, _global_browser_context
    
    if _get_browser_state():
        print("Browser is already running. Close it first with browser-use close")
        return False
        
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
    model="deepseek-chat",
    vision=False,
    record=False,
    record_path=None,
    trace_path=None,
    max_steps=10,
    max_actions=1,
    add_info=""
):
    """Execute a task using the current browser instance."""
    global _global_browser, _global_browser_context
    
    if not _get_browser_state():
        print("No browser session found. Start one with: browser-use start")
        return
        
    if _global_browser is None or _global_browser_context is None:
        print("Browser session state is inconsistent. Try closing and restarting the browser.")
        return

    # Initialize controller
    controller = CustomController()

    # Get LLM model
    llm = utils.get_llm_model(
        provider="deepseek" if model == "deepseek-chat" else model,
        model_name=model,
        temperature=0.8
    )

    # Update context with runtime options if needed
    if record or trace_path:
        _global_browser_context = await _global_browser.new_context(
            config=BrowserContextConfig(
                trace_path=trace_path,
                save_recording_path=record_path if record else None,
                no_viewport=False,
                browser_window_size=_global_browser_context.config.browser_window_size,
                disable_security=_global_browser_context.config.disable_security
            )
        )

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

    try:
        history = await agent.run(max_steps=max_steps)
        return history.final_result()
    except Exception as e:
        raise e

def main():
    parser = argparse.ArgumentParser(description="Control a browser using natural language")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Start command - browser initialization
    start_parser = subparsers.add_parser("start", help="Start a new browser session")
    start_parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    start_parser.add_argument("--window-size", default="1920x1080", help="Browser window size (WxH)")
    start_parser.add_argument("--disable-security", action="store_true", help="Disable browser security features")
    start_parser.add_argument("--user-data-dir", help="Use custom Chrome profile directory")
    start_parser.add_argument("--proxy", help="Proxy server URL")
    
    # Run command - task execution
    run_parser = subparsers.add_parser("run", help="Run a task in the current browser session")
    run_parser.add_argument("prompt", help="The task to perform")
    run_parser.add_argument("--model", "-m", choices=["deepseek-chat", "gemini", "gpt-4", "claude-3"], 
                           default="deepseek-chat", help="The LLM model to use")
    run_parser.add_argument("--vision", action="store_true", help="Enable vision capabilities")
    run_parser.add_argument("--record", action="store_true", help="Enable session recording")
    run_parser.add_argument("--record-path", default="./tmp/record_videos", help="Path to save recordings")
    run_parser.add_argument("--trace-path", default="./tmp/traces", help="Path to save debugging traces")
    run_parser.add_argument("--max-steps", type=int, default=10, help="Maximum number of steps per task")
    run_parser.add_argument("--max-actions", type=int, default=1, help="Maximum actions per step")
    run_parser.add_argument("--add-info", help="Additional context for the agent")
    
    # Close command - cleanup
    subparsers.add_parser("close", help="Close the current browser session")
    
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
            
    elif args.command == "run":
        # Run task
        result = asyncio.run(run_browser_task(
            prompt=args.prompt,
            model=args.model,
            vision=args.vision,
            record=args.record,
            record_path=args.record_path if args.record else None,
            trace_path=args.trace_path,
            max_steps=args.max_steps,
            max_actions=args.max_actions,
            add_info=args.add_info
        ))
        print(result)
        
    elif args.command == "close":
        # Close browser
        asyncio.run(close_browser())
        print("Browser session closed")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 
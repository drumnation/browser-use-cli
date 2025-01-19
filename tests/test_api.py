import asyncio
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig, BrowserContextWindowSize
from browser_use.agent.service import Agent
from src.utils import utils
from src.controller.custom_controller import CustomController
from src.agent.custom_agent import CustomAgent
from src.agent.custom_prompts import CustomSystemPrompt
import os

async def main():
    window_w, window_h = 1920, 1080
    
    # Initialize the browser
    browser = Browser(
        config=BrowserConfig(
            headless=False,
            disable_security=True,
            extra_chromium_args=[f"--window-size={window_w},{window_h}"],
        )
    )
    
    # Create a browser context
    async with await browser.new_context(
        config=BrowserContextConfig(
            trace_path="./tmp/traces",
            save_recording_path="./tmp/record_videos",
            no_viewport=False,
            browser_window_size=BrowserContextWindowSize(
                width=window_w, height=window_h
            ),
        )
    ) as browser_context:
        # Initialize the controller
        controller = CustomController()
        
        # Initialize the agent with a simple task using CustomAgent
        agent = CustomAgent(
            task="go to google.com and search for 'OpenAI'",
            add_infos="",  # hints for the LLM if needed
            llm=utils.get_llm_model(
                provider="deepseek",
                model_name="deepseek-chat",  # Using V2.5 via deepseek-chat endpoint
                temperature=0.8,
                base_url="https://api.deepseek.com/v1",
                api_key=os.getenv("DEEPSEEK_API_KEY", "")
            ),
            browser=browser,
            browser_context=browser_context,
            controller=controller,
            system_prompt_class=CustomSystemPrompt,
            use_vision=False,  # Must be False for DeepSeek
            tool_call_in_content=True,  # Required for DeepSeek as per test files
            max_actions_per_step=1  # Control granularity of actions
        )
        
        # Run the agent
        history = await agent.run(max_steps=10)
        
        print("Final Result:")
        print(history.final_result())
        
        print("\nErrors:")
        print(history.errors())
        
        print("\nModel Actions:")
        print(history.model_actions())
        
        print("\nThoughts:")
        print(history.model_thoughts())

if __name__ == "__main__":
    asyncio.run(main()) 
# Browser-Use API Usage Guide

## Overview

This guide explains how to use the browser-use API to automate browser interactions using different LLM models. The API provides a powerful way to control a browser programmatically through Python.

## Basic Setup

```python
import asyncio
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig, BrowserContextWindowSize
from src.agent.custom_agent import CustomAgent
from src.controller.custom_controller import CustomController
from src.agent.custom_prompts import CustomSystemPrompt
from src.utils import utils
import os

# Window size configuration
window_w, window_h = 1920, 1080

# Browser initialization
browser = Browser(
    config=BrowserConfig(
        headless=False,  # Set to True for headless mode
        disable_security=True,
        extra_chromium_args=[f"--window-size={window_w},{window_h}"],
    )
)
```

## Browser Context Configuration

```python
# Create a browser context with recording and tracing
browser_context = await browser.new_context(
    config=BrowserContextConfig(
        trace_path="./tmp/traces",  # For debugging
        save_recording_path="./tmp/record_videos",  # For session recording
        no_viewport=False,
        browser_window_size=BrowserContextWindowSize(
            width=window_w, height=window_h
        ),
    )
)
```

## Model Configuration

### DeepSeek (Default)

```python
llm = utils.get_llm_model(
    provider="deepseek",
    model_name="deepseek-chat",  # V2.5 model
    temperature=0.8,
    base_url="https://api.deepseek.com/v1",
    api_key=os.getenv("DEEPSEEK_API_KEY", "")
)
```

### Gemini Pro

```python
llm = utils.get_llm_model(
    provider="gemini",
    model_name="gemini-2.0-flash-exp",
    temperature=1.0,
    api_key=os.getenv("GOOGLE_API_KEY", "")
)
```

### GPT-4 Turbo

```python
llm = utils.get_llm_model(
    provider="openai",
    model_name="gpt-4-turbo-preview",
    temperature=0.8,
    api_key=os.getenv("OPENAI_API_KEY", "")
)
```

### Claude-3 Opus

```python
llm = utils.get_llm_model(
    provider="anthropic",
    model_name="claude-3-opus-20240229",
    temperature=0.8,
    api_key=os.getenv("ANTHROPIC_API_KEY", "")
)
```

## Agent Configuration

```python
# Initialize controller
controller = CustomController()

# Initialize agent
agent = CustomAgent(
    task="your task description here",
    add_infos="",  # Optional hints for the LLM
    llm=llm,  # LLM model configured above
    browser=browser,
    browser_context=browser_context,
    controller=controller,
    system_prompt_class=CustomSystemPrompt,
    use_vision=False,  # Must be False for DeepSeek
    tool_call_in_content=True,  # Required for DeepSeek
    max_actions_per_step=1  # Control action granularity
)
```

## Running Tasks

```python
# Run the agent with a maximum number of steps
history = await agent.run(max_steps=10)

# Access results
print("Final Result:", history.final_result())
print("Errors:", history.errors())
print("Model Actions:", history.model_actions())
print("Thoughts:", history.model_thoughts())
```

## Common Tasks

### Navigation

```python
task="go to google.com"
```

### Search

```python
task="go to google.com and search for 'OpenAI'"
```

### Form Filling

```python
task="go to example.com/login and fill in username 'user' and password 'pass'"
```

### Clicking Elements

```python
task="click the 'Submit' button"
```

## Model-Specific Considerations

1. **DeepSeek**
   - Set `use_vision=False`
   - Set `tool_call_in_content=True`
   - Uses OpenAI-compatible API format

2. **Gemini**
   - Set `use_vision=True`
   - Works well with visual tasks

3. **GPT-4 & Claude-3**
   - Support both vision and non-vision tasks
   - Higher reasoning capabilities for complex tasks

## Best Practices

1. **Error Handling**
   - Always check `history.errors()` for any issues
   - Monitor `history.model_thoughts()` for debugging

2. **Resource Management**
   - Use async context managers for browser and context
   - Close resources properly after use

3. **Task Description**
   - Be specific and clear in task descriptions
   - Include necessary context in `add_infos`

4. **Performance**
   - Use `headless=True` for automated tasks
   - Adjust `max_steps` and `max_actions_per_step` based on task complexity

## Example Implementation

```python
async def main():
    # Browser setup
    browser = Browser(config=BrowserConfig(...))
    
    async with await browser.new_context(...) as browser_context:
        # Controller setup
        controller = CustomController()
        
        # Agent setup
        agent = CustomAgent(
            task="your task",
            llm=your_configured_llm,
            browser=browser,
            browser_context=browser_context,
            controller=controller,
            system_prompt_class=CustomSystemPrompt,
            use_vision=False,
            tool_call_in_content=True,
            max_actions_per_step=1
        )
        
        # Run task
        history = await agent.run(max_steps=10)
        
        # Process results
        print(history.final_result())

if __name__ == "__main__":
    asyncio.run(main())
```

## Troubleshooting

1. **JSON Schema Errors with DeepSeek**
   - Ensure using latest DeepSeek V2.5 endpoint
   - Verify correct base URL and API key
   - Use `tool_call_in_content=True`

2. **Browser Connection Issues**
   - Check browser configuration
   - Verify Chrome/Chromium installation
   - Ensure proper port access

3. **Model Response Issues**
   - Adjust temperature for more/less deterministic behavior
   - Try different models for complex tasks
   - Check API key validity and quotas

## Tracing and Debugging

### Enabling Tracing

```python
# Enable tracing in browser context
browser_context = await browser.new_context(
    config=BrowserContextConfig(
        trace_path="./tmp/traces/trace.zip",  # Must have .zip extension
        no_viewport=False,
        browser_window_size=BrowserContextWindowSize(
            width=window_w, height=window_h
        ),
    )
)
```

### Using Traces for Debugging

1. **Recording Traces**
   - Traces are automatically saved when `trace_path` is provided
   - Files are saved with `.zip` extension
   - Contains browser actions, network requests, and screenshots

2. **Analyzing Traces**
   - Use Playwright Trace Viewer to analyze traces
   - View step-by-step browser actions
   - Inspect network requests and responses
   - Review page states at each step

## Report Generation

### Best Practices

1. **Structure**
   - Always include page title and headings
   - List interactive elements with their types
   - Provide clear hierarchy of content
   - Include relevant metadata (URLs, timestamps)

2. **Content**
   - Focus on task-relevant information
   - Include both static and dynamic content
   - Document interactive elements and their states
   - Note any errors or warnings

3. **Format**
   - Use clear section headings
   - Include numbered or bulleted lists
   - Add summary sections for complex pages
   - Use markdown formatting for readability

### Example Report Task

```python
task = "create a report about the page structure, including any interactive elements found"
add_infos = "Focus on navigation elements and forms"

agent = CustomAgent(
    task=task,
    add_infos=add_infos,
    llm=llm,
    browser=browser,
    browser_context=browser_context,
    controller=controller,
    system_prompt_class=CustomSystemPrompt,
    use_vision=True,  # Enable vision for better structure analysis
    max_actions_per_step=1
)
```

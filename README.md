# Fork Purpose

This fork of browser-use/web-ui adds CLI support specifically designed for AI agents like Cursor Agent. It enables direct command-line interaction with browser automation tasks, making it ideal for integration with AI development environments and automated workflows.

## CLI Documentation

See [CLI Guide](cli/README.md) for comprehensive documentation on:
- Available LLM providers and models
- Detailed command reference
- Environment configuration
- Example usage patterns

### Quick Start

```bash
# Run a task (browser will auto-start if needed)
browser-use run "go to example.com and create a report about the page structure"

# Run with specific provider and vision capabilities
browser-use run "analyze the layout and visual elements" --provider Google --vision

# Run with specific model selection
browser-use run "analyze the page" --provider Anthropic --model-index 1

# Explicitly start browser with custom options (optional)
browser-use start --headless --window-size 1920x1080

# Close browser when done
browser-use close
```

### Supported LLM Providers

- **OpenAI** (`gpt-4o`) - Vision-capable model for advanced analysis
- **Anthropic** (`claude-3-5-sonnet-latest`, `claude-3-5-sonnet-20241022`) - Advanced language understanding
- **Google** (`gemini-1.5-pro`, `gemini-2.0-flash`) - Fast and efficient processing
- **DeepSeek** (`deepseek-chat`) - Cost-effective default option

See the [CLI Guide](cli/README.md) for detailed provider configuration and usage examples.

### CLI Commands

- `start` - (Optional) Initialize browser session with custom options:
  - `--headless` - Run in headless mode
  - `--window-size` - Set window dimensions (e.g., "1920x1080")
  - `--disable-security` - Disable security features
  - `--user-data-dir` - Use custom Chrome profile
  - `--proxy` - Set proxy server

- `run` - Execute tasks (auto-starts browser if needed):
  - `--model` - Choose LLM (deepseek-chat, gemini, gpt-4, claude-3)
  - `--vision` - Enable visual analysis
  - `--record` - Record browser session
  - `--trace-path` - Save debugging traces
  - `--max-steps` - Limit task steps
  - `--add-info` - Provide additional context

- `close` - Clean up browser session

### Example Tasks

The [browser-tasks-example.ts](cli/browser-tasks-example.ts) provides ready-to-use task sequences for:

- Product research automation
- Documentation analysis
- Page structure analysis
- Debug sessions with tracing

### Configuration

See [.env.example](.env.example) for all available configuration options, including:

- API keys for different LLM providers
- Browser settings
- Session persistence options

<img src="./assets/web-ui.png" alt="Browser Use Web UI" width="full"/>

<br/>

[![GitHub stars](https://img.shields.io/github/stars/browser-use/web-ui?style=social)](https://github.com/browser-use/web-ui/stargazers)
[![Discord](https://img.shields.io/discord/1303749220842340412?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://link.browser-use.com/discord)
[![Documentation](https://img.shields.io/badge/Documentation-📕-blue)](https://docs.browser-use.com)
[![WarmShao](https://img.shields.io/twitter/follow/warmshao?style=social)](https://x.com/warmshao)

This project builds upon the foundation of the [browser-use](https://github.com/browser-use/browser-use), which is designed to make websites accessible for AI agents.

We would like to officially thank [WarmShao](https://github.com/warmshao) for his contribution to this project.

**WebUI:** is built on Gradio and supports a most of `browser-use` functionalities. This UI is designed to be user-friendly and enables easy interaction with the browser agent.

**Expanded LLM Support:** We've integrated support for various Large Language Models (LLMs), including: Gemini, OpenAI, Azure OpenAI, Anthropic, DeepSeek, Ollama etc. And we plan to add support for even more models in the future.

**Custom Browser Support:** You can use your own browser with our tool, eliminating the need to re-login to sites or deal with other authentication challenges. This feature also supports high-definition screen recording.

**Persistent Browser Sessions:** You can choose to keep the browser window open between AI tasks, allowing you to see the complete history and state of AI interactions.

<video src="https://github.com/user-attachments/assets/56bc7080-f2e3-4367-af22-6bf2245ff6cb" controls="controls">Your browser does not support playing this video!</video>

## Installation Options

### Option 1: Local Installation

Read the [quickstart guide](https://docs.browser-use.com/quickstart#prepare-the-environment) or follow the steps below to get started.

> Python 3.11 or higher is required.

First, we recommend using [uv](https://docs.astral.sh/uv/) to setup the Python environment.

```bash
uv venv --python 3.11
```

and activate it with:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
uv pip install -r requirements.txt
```

Then install playwright:

```bash
playwright install
```
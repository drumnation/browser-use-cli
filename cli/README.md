# Browser-Use CLI Guide

This guide details the available models and commands for the browser-use CLI tool.

## Available Models

### OpenAI
- Model: `gpt-4o` (Vision-capable)
```bash
# Basic usage
browser-use run "analyze this webpage" --provider OpenAI

# With vision capabilities
browser-use run "describe what you see on the page" --provider OpenAI --vision
```

### Anthropic
- Models:
  - `claude-3-5-sonnet-latest` (Default)
  - `claude-3-5-sonnet-20241022`
```bash
# Using default model
browser-use run "analyze this webpage" --provider Anthropic

# Using specific model version
browser-use run "analyze this webpage" --provider Anthropic --model-index 1
```

### Google (Gemini)
- Models:
  - `gemini-1.5-pro` (Default)
  - `gemini-2.0-flash`
```bash
# Using default model
browser-use run "analyze this webpage" --provider Google

# Using flash model
browser-use run "analyze this webpage" --provider Google --model-index 1
```

### DeepSeek
- Model: `deepseek-chat`
```bash
# DeepSeek is the default provider
browser-use run "analyze this webpage"

# Explicitly specifying DeepSeek
browser-use run "analyze this webpage" --provider Deepseek
```

## CLI Commands

### Start Browser Session
```bash
# Basic start
browser-use start

# With custom window size
browser-use start --window-size 1920x1080

# Headless mode
browser-use start --headless

# With custom Chrome profile
browser-use start --user-data-dir "/path/to/profile"

# With proxy
browser-use start --proxy "localhost:8080"
```

### Run Tasks
```bash
# Basic task
browser-use run "go to example.com and analyze the page"

# With vision capabilities
browser-use run "describe the visual layout" --vision

# With specific provider and model
browser-use run "analyze this webpage" --provider Google --model-index 1

# With recording
browser-use run "test the checkout flow" --record --record-path ./recordings

# With debugging traces
browser-use run "analyze form submission" --trace-path ./traces

# With step limits
browser-use run "complex task" --max-steps 5 --max-actions 2

# With additional context
browser-use run "analyze pricing" --add-info "Focus on enterprise plans"
```

### Close Browser
```bash
browser-use close
```

## Environment Variables

Required API keys should be set in your `.env` file:
```env
# OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_ENDPOINT=https://api.openai.com/v1  # Optional

# Anthropic
ANTHROPIC_API_KEY=your_key_here

# Google (Gemini)
GOOGLE_API_KEY=your_key_here

# DeepSeek
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_ENDPOINT=your_endpoint  # Optional
```

## Browser Settings

Optional browser configuration in `.env`:
```env
# Custom Chrome settings
CHROME_PATH=/path/to/chrome
CHROME_USER_DATA=/path/to/user/data

# Session persistence
CHROME_PERSISTENT_SESSION=true  # Keep browser open between tasks
```

## Examples

### Visual Analysis Task
```bash
browser-use run \
  "go to https://example.com and analyze the page layout" \
  --provider Google \
  --vision \
  --record \
  --record-path ./recordings
```

### Multi-Step Task
```bash
browser-use run \
  "go to the login page, fill the form, and verify success" \
  --provider Anthropic \
  --max-steps 5 \
  --trace-path ./traces/login
```

### Research Task
```bash
browser-use run \
  "research pricing information for top 3 competitors" \
  --provider OpenAI \
  --add-info "Focus on enterprise features and annual pricing"
``` 
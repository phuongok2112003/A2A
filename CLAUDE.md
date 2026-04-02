# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is an AI agent project using DeepAgents framework with browser automation capabilities via the `agent-browser` CLI tool. The system allows AI agents to perform web research, form filling, and other browser-based tasks.

## Development Setup

### Environment Setup
1. Activate virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Install the agent-browser CLI tool:
   ```bash
   npm i -g agent-browser
   # or
   brew install agent-browser
   # or
   cargo install agent-browser
   ```

4. Install Chrome for the browser automation:
   ```bash
   agent-browser install
   ```

### Common Commands

#### Running Tests
- Run the test script to verify agent-browser integration:
  ```bash
  python3 test/test_with_skill.py
  ```

#### Starting Services
- Start the API server:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port 10000 --reload
  ```

- Clean up ChromaDB/Pinecone collections:
  ```bash
  curl -X DELETE "http://localhost:9200/langgraph_checkpoints?pretty"
  ```

- Kill processes on port 10000:
  ```bash
  sudo kill $(sudo lsof -t -i:10000)
  ```

## Project Structure

### Key Components
- **`test/test_with_skill.py`**: Example script demonstrating how to create and run an agent with the browser automation skill
- **`skills/agent-browser/`**: Contains the browser automation skill definition and templates
- **`common/`**: Shared utilities including:
  - `tool_common.py`: Shell command execution utility (`run_shell` function)
  - `export_models_llm.py`: LLM model configurations
- **`config/`**: Configuration files for settings and API keys

### Browser Automation Skill (`agent-browser`)
The agent-browser skill enables AI agents to:
- Navigate to websites and interact with web elements
- Fill forms, click buttons, and extract data
- Handle authentication through various methods (session persistence, auth vault, etc.)
- Take screenshots and generate PDFs
- Execute JavaScript in browser context
- Manage multiple browser sessions

#### Core Usage Pattern
All browser interactions must use the `run_shell` tool to execute `agent-browser` commands:

```python
# Open a webpage
run_shell("agent-browser open https://example.com")

# Wait for page to load
run_shell("agent-browser wait --load networkidle")

# Get interactive element references
run_shell("agent-browser snapshot -i")

# Interact with elements using refs (@e1, @e2, etc.)
run_shell("agent-browser fill @e1 \"text\"")
run_shell("agent-browser click @e2")

# Extract information
run_shell("agent-browser get text body")

# Close browser session
run_shell("agent-browser close")
```

#### Authentication Methods
1. **Session Persistence**: Recommended for recurring tasks
   ```bash
   # First login (save state)
   agent-browser --profile ~/.myapp open https://app.example.com/login
   # ... perform login ...

   # Subsequent uses (already authenticated)
   agent-browser --profile ~/.myapp open https://app.example.com/dashboard
   ```

2. **Auth Vault**: For secure credential storage
   ```bash
   # Save credentials (encrypted)
   echo "$PASSWORD" | agent-browser auth save myapp --url https://app.example.com/login --username user --password-stdin

   # Login using saved credentials
   agent-browser auth login myapp
   ```

3. **Import from Browser**: For one-off tasks using existing login
   ```bash
   # Connect to user's running Chrome
   agent-browser --auto-connect state save ./auth.json
   # Use the saved state
   agent-browser --state ./auth.json open https://app.example.com/dashboard
   ```

#### Important Notes
- Refs (`@e1`, `@e2`, etc.) become invalid after page changes - always re-snapshot after navigation
- Use `&&` to chain commands when intermediate output isn't needed:
  ```bash
  agent-browser open https://example.com && agent-browser wait --load networkidle && agent-browser snapshot -i
  ```
- Always close browser sessions to prevent resource leaks:
  ```bash
  agent-browser close
  ```

### Configuration Files
- **`agent-browser.json`**: Project-specific browser configuration (optional)
  ```json
  {
    "headed": true,
    "proxy": "http://localhost:8080",
    "profile": "./browser-data"
  }
  ```

## Key Files Reference
- `test/test_with_skill.py`: Main example for browser automation usage
- `skills/agent-browser/SKILL.md`: Complete documentation for the browser automation skill
- `common/tool_common.py`: Contains the `run_shell` function used to execute browser commands
- `config/settings.py`: Configuration management for API keys and settings

## Troubleshooting
1. **Module Import Errors**: Ensure you're running from the project root directory
2. **Browser Not Found**: Run `agent-browser install` to download Chrome
3. **Port Conflicts**: Use the kill command above to free up port 10000
4. **Authentication Issues**: Clear saved states or use fresh profiles when needed
# AI Telegram Bot

Simple Telegram bot that provides interface to AI models (OpenAI and Deepseek).

## Features
- Text messages support
- Context-aware conversations
- Multiple AI providers support (OpenAI, Deepseek)
- User access control
- Conversation history management

## Setup

### 1. Environment Variables
Create `.env` file in the project directory with the following variables:

```bash
# API Keys
TELEGRAM_BOT_KEY=your_telegram_bot_token
OPEN_AI_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# AI models configuration
OPENAI_MODEL=gpt-4o  # OpenAI model name (e.g. gpt-4o, gpt-4o-mini)
DEEPSEEK_MODEL=deepseek-chat  # Deepseek model name
CHAT_MODEL_MAX_TOKENS=1000  # Maximum tokens per response

# Optional: logging configuration
HTTPX_LOG_LEVEL=WARNING  # Set to WARNING or ERROR to reduce API request logs
```

### 2. Dependencies
Install required packages:
```bash
pip install -r requirements.txt
```

### 3. Run Bot
Start the bot with admin username and chosen AI provider:
```bash
# First run (will create allowed_users.json with admin)
python main.py -admin your_telegram_username [-ai openai|deepseek]

# Subsequent runs (admin argument is ignored if allowed_users.json exists)
python main.py [-ai openai|deepseek]
```

The `-ai` argument is optional and defaults to "openai". Use "-ai deepseek" to run with Deepseek.

## User Management
- Access is controlled via `allowed_users.json`
- First user (admin) is set when running the bot for the first time
- Any allowed user can add new users with `/add_user` command
- Example: `/add_user username` (specify telegram username without "@")

## Available Commands
- `/start` - Start the bot and show current configuration
- `/help` - Show help message and current configuration
- `/forget_all` - Clear conversation history
- `/add_user` - Add new user (for any allowed user). Example: `/add_user username`

## Logging Configuration
The bot logs:
- All important events with usernames
- Current configuration at startup
- API requests (can be reduced by setting HTTPX_LOG_LEVEL)

To reduce API request logging output:
1. Set `HTTPX_LOG_LEVEL=WARNING` to show only warnings and errors
2. Or set `HTTPX_LOG_LEVEL=ERROR` to show only errors


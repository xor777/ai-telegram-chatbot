# AI Telegram Bot

Simple Telegram bot that provides interface to AI models with voice messages support.

## Features
- Text and voice messages support
- Context-aware conversations
- Voice messages transcription
- Text-to-speech responses
- User access control

## Setup

### 1. Environment Variables
Create `.env` file in the project directory:
```bash
# Create .env file
touch .env

# Add required variables
echo OPEN_AI_KEY=YOUR_OPEN_AI_API_KEY > .env
echo TELEGRAM_BOT_KEY=YOUR_TELEGRAM_BOT_KEY >> .env
echo CHAT_MODEL=gpt-4 >> .env
echo CHAT_MODEL_MAX_TOKENS=1000 >> .env
echo VOICE_TO_TEXT_MODEL=whisper-1 >> .env
echo TEXT_TO_SPEECH_MODEL=tts-1 >> .env
echo TEXT_TO_SPEECH_VOICE=alloy >> .env
```

### 2. Dependencies
Install required packages:
```bash
pip install -r requirements.txt
```

### 3. Run Bot
Start the bot with admin username:
```bash
python main.py -admin your_telegram_username
```

## User Management
- Only allowed users can use the bot
- Each authorized user can add new users with `/add_user` command
- Example: `/add_user username` (specify telegram username without "@")

## Available Commands
- `/start` - Start the bot
- `/help` - Show help message
- `/forget_all` - Clear conversation history
- `/add_user` - Add new user (admin only)


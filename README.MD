Telegram bot interface to AI models with voice messages support

To run it, create .env file into the project directory and set environment variables:

% touch .env
% echo OPEN_AI_KEY=YOUR_OPEN_AI_API_KEY > .env
% echo TELEGRAM_BOT_KEY=YOUR_TELEGRAM_BOT_KEY >> .env
% echo CHAT_MODEL=gpt-4o >> .env
% echo CHAT_MODEL_MAX_TOKENS=1000 >> .env
% echo VOICE_TO_TEXT_MODEL=whisper-1 >> .env
% echo TEXT_TO_SPEECH_MODEL=tts-1 >> .env
% echo TEXT_TO_SPEECH_VOICE=alloy >> .env

modify allowed_users.json. only allowed users can use the bot
each authorised user can add new user with /add_user command
example: /add_user xor777
you should specify telegram username without "@"

install dependencies:
% pip install -r requirements.txt

run bot:
% python main.py -admin your_telegram_username


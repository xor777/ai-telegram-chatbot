import logging
import os
import argparse
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from chat.chain_manager import ChainManager
from user_management import UserManager

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(os.environ.get("HTTPX_LOG_LEVEL", "WARNING"))

class Bot:
    def __init__(self, ai_provider: str):
        if ai_provider == "deepseek":
            api_key = os.environ["DEEPSEEK_API_KEY"]
            base_url = "https://api.deepseek.com/v1"
            model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        else:  # openai
            api_key = os.environ["OPEN_AI_KEY"]
            base_url = None  # Use default OpenAI URL
            model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
            
        self.chain_manager = ChainManager(api_key, base_url, model)
        self.openai_client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.user_manager = UserManager()
        self.ai_provider = ai_provider
        self.model = model
        
        logging.info(f"AI Provider: {self.ai_provider.upper()}")
        logging.info(f"Model: {self.model}")
        logging.info(f"Max tokens: {os.environ.get('CHAT_MODEL_MAX_TOKENS', '1000')}")
        logging.info(f"Base URL: {base_url if base_url else 'default OpenAI'}")
        
    def _get_config_text(self) -> str:
        return (
            "Current configuration:\n"
            f"AI Provider: {self.ai_provider.upper()}\n"
            f"Model: {self.model}\n"
            f"Max tokens: {os.environ.get('CHAT_MODEL_MAX_TOKENS', '1000')}\n"
            f"Base URL: {self.openai_client.base_url if self.openai_client.base_url else 'default OpenAI'}"
        )
        
    async def start(self, update, context):
        if not self.user_manager.is_user_allowed(update.message):
            return
        await update.message.reply_text(
            f'Hi! This bot is using {self.ai_provider.upper()} ({self.model}) as AI provider.\n'
            'You can ask anything in any language you know.\n'
            'Use /help command to get help. Enjoy!\n\n'
            f'{self._get_config_text()}'
        )

    async def forget_all(self, update, context):
        if not self.user_manager.is_user_allowed(update.message):
            return
        username = update.message.from_user.username
        self.chain_manager.clear_context(username)
        await update.message.reply_text("Everything is forgotten 🧠❌")

    # Handle text messages from users
    async def handle_message(self, update, context):
        if not self.user_manager.is_user_allowed(update.message):
            return
            
        username = update.message.from_user.username
        message_text = update.message.text
        logging.info(f"[{username}] Received text message")
        
        try:
            await update.message.chat.send_chat_action(action="typing")
            
            logging.info(f"[{username}] Requesting AI response")
            response = self.chain_manager.get_response(username, message_text)
            logging.info(f"[{username}] Got response from AI")
            
            await update.message.reply_text(response)
            logging.info(f"[{username}] Sent response")
                
        except Exception as e:
            error_msg = f"An error occurred while processing your message:\n{e}\nPlease contact bot admin"
            logging.error(f"[{username}] Error processing message: {str(e)}")
            await update.message.reply_text(error_msg)

    # # Handle voice messages from users
    # async def handle_voice(self, update, context):
    #     if not self.user_manager.is_user_allowed(update.message):
    #         return
            
    #     username = update.message.from_user.username
    #     logging.info(f"[{username}] Received voice message")
        
    #     try:
    #         await update.message.chat.send_chat_action(action="record_voice")
            
    #         logging.info(f"[{username}] Starting voice transcription")
    #         transcript = await self._process_voice_message(update.message)
    #         logging.info(f"[{username}] Voice transcription completed")
            
    #         await update.message.chat.send_chat_action(action="typing")
            
    #         logging.info(f"[{username}] Requesting AI response")
    #         response = self.chain_manager.get_response(username, transcript)
    #         logging.info(f"[{username}] Got response from AI")
            
    #         await self._handle_voice_response(update.message, response)
    #     except Exception as e:
    #         logging.error(f"[{username}] Voice message handling error: {str(e)}")
    #         await update.message.reply_text("Sorry, I couldn't process your voice message.")

    # async def _process_voice_message(self, message):
    #     username = message.from_user.username
    #     voice_file = await message.voice.get_file()
    #     saved_file_name = f'voice_message_{message.message_id}.ogg'
        
    #     try:
    #         logging.info(f"[{username}] Downloading voice message")
    #         await voice_file.download_to_drive(saved_file_name)
            
    #         logging.info(f"[{username}] Starting speech-to-text")
    #         with open(saved_file_name, 'rb') as audio_file:
    #             transcript = self.openai_client.audio.transcriptions.create(
    #                 model=os.environ["VOICE_TO_TEXT_MODEL"],
    #                 file=audio_file,
    #                 response_format='text'
    #             )
    #         logging.info(f"[{username}] Speech-to-text completed")
    #         return transcript
    #     finally:
    #         if os.path.exists(saved_file_name):
    #             os.remove(saved_file_name)

    # async def _handle_voice_response(self, message, response_text):
    #     username = message.from_user.username
    #     file_name = f'answer_{message.message_id}.ogg'
    #     synthesized_answer = Path(__file__).parent / file_name
        
    #     try:
    #         logging.info(f"[{username}] Requesting text-to-speech")
    #         response = self.openai_client.audio.speech.create(
    #             model=os.environ["TEXT_TO_SPEECH_MODEL"],
    #             voice=os.environ["TEXT_TO_SPEECH_VOICE"],
    #             input=response_text
    #         )
    #         logging.info(f"[{username}] Got synthesized speech")
            
    #         logging.info(f"[{username}] Saving synthesized speech to file")
    #         response.write_to_file(synthesized_answer)
            
    #         try:
    #             logging.info(f"[{username}] Attempting to send voice message")
    #             logging.info(f"[{username}] File size: {os.path.getsize(synthesized_answer)} bytes")
    #             await message.reply_voice(voice=open(synthesized_answer, 'rb'))
    #             logging.info(f"[{username}] Successfully sent voice message")
    #         except Exception as e:
    #             logging.error(f"[{username}] Error sending voice message: {str(e)}, type: {type(e)}")
    #             await message.reply_text(response_text)
    #             logging.info(f"[{username}] Sent text response")
    #     finally:
    #         if synthesized_answer.exists():
    #             synthesized_answer.unlink()

    async def add_user(self, update, context):
        if not self.user_manager.is_user_allowed(update.message):
            return
            
        username = update.message.from_user.username
        
        if not context.args:
            await update.message.reply_text("Please specify username to add. Example: /add_user username")
            return
            
        new_username = context.args[0].lstrip("@")
        logging.info(f"[{username}] Attempting to add new user: {new_username}")
        
        if self.user_manager.add_user(new_username):
            await update.message.reply_text(f"User @{new_username} added successfully")
            logging.info(f"[{username}] Successfully added user: {new_username}")
        else:
            await update.message.reply_text(f"User @{new_username} is already in the allowed list")
            logging.info(f"[{username}] Failed to add user (already exists): {new_username}")

    async def help(self, update, context):
        if not self.user_manager.is_user_allowed(update.message):
            return
            
        username = update.message.from_user.username
        logging.info(f"[{username}] Requested help")
        
        help_text = (
            "Available commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/forget_all - Clear conversation history\n"
            "/add_user - Add new user (admin only). Example: /add_user username\n\n"
            "You can send text messages and I'll respond accordingly.\n\n"
            f"{self._get_config_text()}"
        )
        
        await update.message.reply_text(help_text)
        logging.info(f"[{username}] Sent help message")

    def run(self):
        application = Application.builder().token(os.environ["TELEGRAM_BOT_KEY"]).build()

        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help))
        application.add_handler(CommandHandler("forget_all", self.forget_all))
        application.add_handler(CommandHandler("add_user", self.add_user))
        # application.add_handler(MessageHandler(filters.VOICE & ~filters.COMMAND, self.handle_voice))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        logging.info("Bot started")
        application.run_polling()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-admin", help="specify admin username")
    parser.add_argument(
        "-ai", 
        choices=["openai", "deepseek"],
        default="openai",
        help="choose AI provider (default: openai)"
    )
    args = parser.parse_args()
    
    bot = Bot(args.ai)
    bot.run()

if __name__ == "__main__":
    main()

import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from chat.chain_manager import ChainManager
from user_management import UserManager

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Bot:
    def __init__(self):
        self.chain_manager = ChainManager(os.environ["OPEN_AI_KEY"])
        self.openai_client = OpenAI(api_key=os.environ["OPEN_AI_KEY"])
        self.user_manager = UserManager()
        
    async def start(self, update, context):
        if not self.user_manager.is_user_allowed(update.message):
            return
        await update.message.reply_text(
            f'Hi! This bot is just an interface to OpenAI models. Now it is working with {os.environ["CHAT_MODEL"]} model. '
            'You can ask anything in any language you know. '
            'Use /help command to get help. Enjoy!'
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

    # Handle voice messages from users
    async def handle_voice(self, update, context):
        if not self.user_manager.is_user_allowed(update.message):
            return
            
        username = update.message.from_user.username
        logging.info(f"[{username}] Received voice message")
        
        try:
            await update.message.chat.send_chat_action(action="record_voice")
            
            logging.info(f"[{username}] Starting voice transcription")
            transcript = await self._process_voice_message(update.message)
            logging.info(f"[{username}] Voice transcription completed")
            
            await update.message.chat.send_chat_action(action="typing")
            
            logging.info(f"[{username}] Requesting AI response")
            response = self.chain_manager.get_response(username, transcript)
            logging.info(f"[{username}] Got response from AI")
            
            await self._handle_voice_response(update.message, response)
        except Exception as e:
            logging.error(f"[{username}] Voice message handling error: {str(e)}")
            await update.message.reply_text("Sorry, I couldn't process your voice message.")

    async def _process_voice_message(self, message):
        username = message.from_user.username
        voice_file = await message.voice.get_file()
        saved_file_name = f'voice_message_{message.message_id}.ogg'
        
        try:
            logging.info(f"[{username}] Downloading voice message")
            await voice_file.download_to_drive(saved_file_name)
            
            logging.info(f"[{username}] Starting speech-to-text")
            with open(saved_file_name, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model=os.environ["VOICE_TO_TEXT_MODEL"],
                    file=audio_file,
                    response_format='text'
                )
            logging.info(f"[{username}] Speech-to-text completed")
            return transcript
        finally:
            if os.path.exists(saved_file_name):
                os.remove(saved_file_name)

    async def _handle_voice_response(self, message, response_text):
        username = message.from_user.username
        file_name = f'answer_{message.message_id}.ogg'
        synthesized_answer = Path(__file__).parent / file_name
        
        try:
            logging.info(f"[{username}] Requesting text-to-speech")
            response = self.openai_client.audio.speech.create(
                model=os.environ["TEXT_TO_SPEECH_MODEL"],
                voice=os.environ["TEXT_TO_SPEECH_VOICE"],
                input=response_text
            )
            logging.info(f"[{username}] Got synthesized speech")
            
            logging.info(f"[{username}] Saving synthesized speech to file")
            response.write_to_file(synthesized_answer)
            
            try:
                logging.info(f"[{username}] Attempting to send voice message")
                logging.info(f"[{username}] File size: {os.path.getsize(synthesized_answer)} bytes")
                await message.reply_voice(voice=open(synthesized_answer, 'rb'))
                logging.info(f"[{username}] Successfully sent voice message")
            except Exception as e:
                logging.error(f"[{username}] Error sending voice message: {str(e)}, type: {type(e)}")
                await message.reply_text(response_text)
                logging.info(f"[{username}] Sent text response")
        finally:
            if synthesized_answer.exists():
                synthesized_answer.unlink()

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
            "You can send text or voice messages, and I'll respond accordingly.\n"
            "Voice messages will be transcribed and processed, and you'll get both voice and text responses."
        )
        
        await update.message.reply_text(help_text)
        logging.info(f"[{username}] Sent help message")

    def run(self):
        application = Application.builder().token(os.environ["TELEGRAM_BOT_KEY"]).build()

        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help))
        application.add_handler(CommandHandler("forget_all", self.forget_all))
        application.add_handler(CommandHandler("add_user", self.add_user))
        application.add_handler(MessageHandler(filters.VOICE & ~filters.COMMAND, self.handle_voice))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        logging.info("Bot started")
        application.run_polling()

def main():
    bot = Bot()
    bot.run()

if __name__ == "__main__":
    main()

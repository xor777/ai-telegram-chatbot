import telebot
import datetime
import logging
import os
import time
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

load_dotenv()

def is_user_allowed(message):
    message_from = message.from_user.username
    try:
        next(user for user in allowed_users if user["username"] == message_from)
        return True
    except StopIteration:
        bot.send_message(message.chat.id, "You are not allowed to use this bot.\nContact bot admin")
        logging.warning(f"{message_from} attempted to use bot being unauthorized")
        return False


def dump_users():
    with open(allowed_users_config, "w") as file:
        json.dump(allowed_users, file)


try:
    bot = telebot.TeleBot(os.environ["TELEGRAM_BOT_KEY"])
except Exception as e:
    logging.error(f"Error initialising Telegram API - {e}")
    raise SystemExit(0)

try:
    client = OpenAI(api_key=os.environ["OPEN_AI_KEY"])
except Exception as e:
    logging.error(f"Error initialising OpenAI API - {e}")
    raise SystemExit(0)

# only allowed users could use bot
# any allowed user can add another user
allowed_users_config = "allowed_users.json"
allowed_users = []
if os.path.exists(allowed_users_config):
    try:
        with open(allowed_users_config, "r") as f:
            allowed_users = json.load(f)
    except Exception as e:
        logging.error(f"Error parsing allowed_users.json: {str(e)}, it will be reinitialised")

if len(allowed_users) == 0:
    parser = argparse.ArgumentParser()
    parser.add_argument("-admin", help="specify admin username")
    args = parser.parse_args()

    if args.admin:
        admin_username = args.admin
    else:
        admin_username = input("Enter bot admin telegram user name:")

    if not admin_username:
        logging.error("No admin specified. Use -admin argument or enter manually")
        raise SystemExit(0)
    else:
        admin_username = admin_username.lstrip("@")
        logging.info(f"Bot admin is {admin_username}")

    allowed_users = [{"username": admin_username}]
    dump_users()

logging.info(f"Allowed users is: {', '.join([user['username'] for user in allowed_users])}")


@bot.message_handler(commands=['start'])
def start(message):
    if is_user_allowed(message):
        bot.reply_to(message, 'Hi! This bot is just an interface to GPT-4. You can ask anything either english or russian '
                              '(or even any language you know). Use /help command to get help. Enjoy!')


@bot.message_handler(commands=['add_user'])
def handle_add_user(message):
    if not is_user_allowed(message):
        return

    new_username = message.text.split(" ")[1].lstrip("@")
    if not new_username:
        bot.send_message(message.chat.id, "Invalid command format. Please use /add_user @username")
        return

    if any(user["username"] == new_username for user in allowed_users):
        bot.send_message(message.chat.id, f"{new_username} is already in the list of allowed users.")
        return

    new_user = {"username": new_username}
    allowed_users.append(new_user)
    bot.send_message(message.chat.id, f"{new_username} has been added to the list of allowed users.")
    logging.info(f"[{datetime.datetime.now()}] {message.from_user.username} added {new_username} to the list of allowed users.")
    dump_users()

@bot.message_handler(commands=['help'])
def handle_help(message):
    if not is_user_allowed(message):
        return

    bot.send_message(message.chat.id, "Hello! I'm an AI designed to help people explore and understand the world of "
                                      "technology. For people who are not familiar with tech and AI, I can provide "
                                      "an introduction to these topics as well as a wealth of resources to help you "
                                      "further explore them. Depending on your interests, I could also recommend "
                                      "tutorials, courses, books, and other helpful materials that can help you "
                                      "get started. \n\n"
                                      "/help - this help\n"
                                      "/forget_all - reset all previous context")


@bot.message_handler(commands=['forget_all'])
def handle_clear_context(message):
    if not is_user_allowed(message):
        return

    message_from = message.from_user.username
    for user in allowed_users:
        if user["username"] == message_from:
            user["dialogue"] = []
            logging.info(f"Context cleared for user {message_from}")
            bot.send_message(message.chat.id, "Everything is forgotten 🧠❌")


@bot.message_handler(func=lambda message: True)
def answer_question(message, transcript=''):
    if not is_user_allowed(message):
        return

    message_from = message.from_user.username
    dialogue_history = []

    for user in allowed_users:
        if user["username"] == message_from:
            dialogue_history = user.get("dialogue", [])
            break

    message_text = message.text if not transcript else transcript

    dialogue_history.append({"role": "user", "content": message_text})

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=dialogue_history,
            max_tokens=1000
        )

        response_text = response.choices[0].message.content

        dialogue_history.append({"role": "assistant", "content": response_text})

        logging.info(f"Got response from OpenAI API for user {message_from}")
        total_tokens = response.usage.total_tokens
        logging.info(f"Total tokens used: {total_tokens}")

        avg_token_length = 4
        max_token_limit = 4096
        current_token_count = sum(len(item["content"]) / avg_token_length for item in dialogue_history)

        while current_token_count > max_token_limit:
            removed = dialogue_history.pop(0)
            logging.debug(f"User: {message_from}, Removed context: {removed}")
            current_token_count -= len(removed["content"]) / avg_token_length

        for user in allowed_users:
            if user["username"] == message_from:
                user["dialogue"] = dialogue_history
                break

        for user in allowed_users:
            if user["username"] == message_from:
                user["dialogue"] = dialogue_history
                break

    except Exception as e:
        response_text = f"An error occurred while processing your dialogue:\n{e}\nPlease contact bot admin"
        logging.error(f"Got an exception {str(e)} while requesting OpenAI API")

    if len(response_text) > 0:
        if transcript:
            file_name = f'answer_{message.id}.ogg'
            synthesized_answer = Path(__file__).parent / file_name
            response = client.audio.speech.create(
                model='tts-1',
                voice='alloy',
                input=response_text
            )
            response.stream_to_file(synthesized_answer)

            with open(synthesized_answer, 'rb') as audio:
                bot.send_voice(message.chat.id, audio)

            synthesized_answer.unlink()

        else:
            bot.reply_to(message, response_text)
    else:
        bot.reply_to(message, "API returned empty response 🤔")
        logging.error(f"API returned empty response for user {message_from}")


@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    if not is_user_allowed(message):
        return

    try:
        voice = bot.get_file(message.voice.file_id)
        voice_data = bot.download_file(voice.file_path)

        saved_file_name = f'voice_message_{message.message_id}.ogg'
        with open(saved_file_name, "wb") as new_file:
            new_file.write(voice_data)

        logging.info(f'{saved_file_name} saved')

        with open(saved_file_name, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model='whisper-1',
                file=audio_file,
                response_format='text'
            )

        answer_question(message, transcript)

    except IOError as e:
        logging.error(f"File operation error: {str(e)}")
    except Exception as e:
        logging.error(f"Voice message handling error: {str(e)}")
    finally:
        try:
            os.remove(saved_file_name)
        except Exception as e:
            logging.error(f"Error deleting file: {str(e)}")


logging.info('Bot initialized')


while True:
    try:
        logging.info("Bot started")
        bot.polling()
        break

    except Exception as e:
        logging.error(f"Bot stopped with exception {e}")
        time.sleep(5)
        logging.info("Restarting bot due to error")

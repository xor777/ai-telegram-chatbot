import telebot
import datetime
import logging
import os
import time
import argparse
import json
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

    new_username = message.text.split(" ")[1]
    new_username = new_username.lstrip("@")
    if new_username:
        new_user = {"username": new_username}
        allowed_users.append(new_user)
        bot.send_message(message.chat.id, f"{new_username} has been added to the list of allowed users.")
        logging.info(
            f"[{datetime.datetime.now()}] {message.from_user.username} added {new_username} to the list of allowed "
            f"users.")
        dump_users()
    else:
        bot.send_message(message.chat.id, "Invalid command format. Please use /add_user @username")


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
def answer_question(message):
    if not is_user_allowed(message):
        return

    message_from = message.from_user.username
    dialogue_history = []

    for user in allowed_users:
        if user["username"] == message_from:
            dialogue_history = user.get("dialogue", [])
            break

    dialogue_history.append({"role": "user", "content": message.text})

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
        bot.reply_to(message, response_text)
    else:
        bot.reply_to(message, "API returned empty response 🤔")
        logging.error(f"API returned empty response for user {message_from}")


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

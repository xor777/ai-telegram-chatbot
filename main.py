import telebot
import openai
import datetime
import logging
import os
import time
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

load_dotenv()

try:
    bot = telebot.TeleBot(os.environ["TELEGRAM_BOT_KEY"])
except Exception as e:
    logging.error(f"Error initialising Telegram API - {e}")
    raise SystemExit(0)

try:
    openai.api_key = os.environ["OPEN_AI_KEY"]
except Exception as e:
    logging.error(f"Error initialising OpenAI API - {e}")
    raise SystemExit(0)

# only allowed users could use bot
# any allowed user can add another user
allowed_users = [
    {
        "username": "xor777"
    },
    {
        "username": "nocool76"
    },
    {
        "username": "Darya2203600"
    }
]


def is_user_allowed(message_from):
    try:
        next(user for user in allowed_users if user["username"] == message_from)
        return True
    except StopIteration:
        return False


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Hi! This bot is just an interface to GPT-3. You can ask anything either english or russian '
                          '(or even any language you know). Enjoy!')


@bot.message_handler(commands=['add_user'])
def handle_add_user(message):
    if not is_user_allowed(message.from_user.username):
        bot.send_message(message.chat.id, "You are not allowed to use this command.")
        return

    new_username = message.text.split(" ")[1]
    if new_username:
        new_user = {"username": new_username}
        allowed_users.append(new_user)
        bot.send_message(message.chat.id, f"{new_username} has been added to the list of allowed users.")
        logging.info(
            f"[{datetime.datetime.now()}] {message.from_user.username} added {new_username} to the list of allowed "
            f"users.")
    else:
        bot.send_message(message.chat.id, "Invalid command format. Please use /add_user @username")


@bot.message_handler(func=lambda message: True)
def answer_question(message):
    message_from = message.from_user.username
    if not is_user_allowed(message_from):
        bot.send_message(message.chat.id, "You are not allowed to use this bot.\nContact bot admin")
        logging.warning(f"{message_from} attempted to use bot being unauthorized")
        return

    start_sequence = "\nAI: "
    restart_sequence = "\nHuman: "

    # update last message time and get previous dialogue
    for user in allowed_users:
        if user["username"] == message_from:
            user["last_message"] = str(datetime.datetime.now())
            dialogue = user.get("dialogue", "")
            dialogue = f"{dialogue}{restart_sequence}{message.text}{start_sequence}"
            user["dialogue"] = dialogue
            break

    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=dialogue,
            temperature=0.9,
            max_tokens=1500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0.6,
            stop=[" Human:", " AI:"]
        )

        response_text = response['choices'][0]['text']
        logging.info(f"Got response from OpenAI API for user {message_from}")

    except Exception as e:
        response_text = f"An error occured while processing your dialogue:\n{e}\nPlease contact bot admin"
        logging.error(f"Got an exception {e} while requestiong OpenAI API")

    # need to keep all user's dialogue to maintain the context
    # that's how GPT3 works. you should use text completion call to do the human like chat
    # send the previous dialogue and ask GPT3 to complete text considering last question
    for user in allowed_users:
        if user["username"] == message_from:
            user["dialogue"] = f"{dialogue}{response_text}"
            break

    logging.info(f"Sending response to {message.from_user.username}")
    if len(response_text) > 0:
        bot.reply_to(message, response_text)
    else:
        bot.reply_to(message, "API returned empty response 🤔")
        logging.error(f"API returned empty response for user {message_from}")


logging.info('Bot initialized')
while True:
    try:
        bot.polling()
        break

    except Exception as e:
        logging.error(f"Bot stopped with exception {e}")
        time.sleep(5)
        logging.info("Restarting bot due to error")
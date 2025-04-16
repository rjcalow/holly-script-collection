import os

token = os.environ.get('hollytoken')

import telebot
from telebot import types
from time import sleep
from subprocess import Popen

from ..common.pi import pitemp, pimemory, pidisk, picpuusage, piuptime, restart
from ...holly.secrets import whitelist
import os
import re

from ..common.ai import ai_on_pi  # ai testing
from ...common.scraping import scrape_article_p_tags



bot = telebot.TeleBot(token)

def check_user(message, bot, _id):
    if _id not in whitelist:
        reply_text = 'Sorry, this is a private bot.'
        bot.send_message(_id, text=reply_text)
        return False
    else:
        return True

def restart_caller(message):
    chat_id = message.chat.id
    # Assuming check_user function can work with telebot's message object
    if check_user(message, None, chat_id) == True:
        print("restarting")
        bot.send_message(chat_id=chat_id, text="restarting this bitch")
        cmd = "sh $HOME/start.sh"
        Popen([cmd], shell=True)
        # subprocess.call(['sh', '$HOME/start.sh'])

@bot.message_handler(commands=['holly', 'start'])
def start(message):
    """
    method to handle the /start command and create keyboard
    """
    chat_id = message.chat.id
    # delete(None, chat_id, message.message_id) # Context is not directly available in telebot

    # defining the keyboard layout
    kbd_layout = [['Holly status',],
                  ['Holly uptime',]]

    # converting layout to markup
    # documentation: https://pytba.readthedocs.io/en/latest/types.html#telebot.types.ReplyKeyboardMarkup
    kbd = types.ReplyKeyboardMarkup(kbd_layout)

    # sending the reply so as to activate the keyboard
    msg = bot.send_message(chat_id, text="Holly activated", reply_markup=kbd)
    # delete(None, chat_id, msg.message_id) # Context is not directly available in telebot


@bot.message_handler(regexp=r"Holly status")
def status(message):
    """
    sever status
    """
    # sending the reply message with the selected option
    chat_id = message.chat.id
    # delete(None, chat_id, message.message_id) # Context is not directly available in telebot
    msg = check_status()
    try:
        msg = msg + "\n\n 🌡️ {}c\n📈 {} \n🐏 {} \n💾 {}\n\n".format(pitemp(), picpuusage(), pimemory(), pidisk())
    except:
        msg = msg
    if "not " in msg:
        text = "There's a problem boss!\n\nRed Alert\n"
    else:
        text = "No problems here boss\n"

    msg = msg + text
    bot.send_message(chat_id, msg, reply_markup=types.ReplyKeyboardRemove())
    # delete(None, chat_id, message.message_id) # Context is not directly available in telebot

@bot.message_handler(regexp=r"Holly uptime")
def uptime(message):
    """
    server uptime
    """
    # sending the reply message with the selected option
    chat_id = message.chat.id
    # Assuming check_user function can work with telebot's message object
    check_user(message, None, chat_id)
    # delete(None, chat_id, message.message_id) # Context is not directly available in telebot
    bot.send_message(chat_id, piuptime(), reply_markup=types.ReplyKeyboardRemove())
    # delete(None, chat_id, message.message_id) # Context is not directly available in telebot

@bot.message_handler(commands=['ask'])
def askAI_handler(message):
    chat_id = message.chat.id
    # Assuming check_user function can work with telebot's message object
    check_user(message, None, chat_id)
    text = " ".join(message.text.split()[1:])  # Get the arguments after /ask
    reply = ai_on_pi(text)
    bot.send_message(chat_id=chat_id, text=str(reply))

# Function to find URLs in a message
def find_urls(text):
    # Regular expression pattern for URLs
    url_pattern = r'(https?://[^\s]+)'
    return re.findall(url_pattern, text)

# Function to handle incoming messages
@bot.message_handler(func=lambda message: True) # Handles all text messages
def handle_message(message):
    # Assuming check_user function can work with telebot's message object
    check_user(message, None, message.chat.id)
    text = message.text  # Get the text of the incoming message
    urls = find_urls(text)  # Find URLs in the text
    response = None  # Initialize response to None

    if urls:
        article_text = scrape_article_p_tags(urls[0])
        print(article_text)
        try:
            response = ai_on_pi(
                "Condense the following text into a summary of 350 characters or less, focusing solely on the core content. Remove all privacy, cookie, feedback, and legal statements. Provide the summary text only, without any introductory phrases, headings, or character counts. Text:" + article_text
            )
        except:
            response = None
    else:
        response = None

    if response:
        bot.reply_to(
            message,
            str(response),
            # reply_to_message_id=message.message_id # Already handled by reply_to
        )

@bot.message_handler(commands=['restart'])
def restart_command(message):
    restart_caller(message)

if __name__ == '__main__':
    print("Bot started...")
    bot.polling(none_stop=True)

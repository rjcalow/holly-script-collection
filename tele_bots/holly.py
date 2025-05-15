import sys
import os

# Get the absolute path to the directory containing holly.py
script_dir = os.path.dirname(os.path.abspath(__file__))
# script_dir will be: /home/holly/holly-script-collection/telebots

# Go up one level to 'holly-script-collection'
base_dir = os.path.dirname(script_dir)
# base_dir will be: /home/holly/holly-script-collection

# Construct the path to the 'common' directory
common_dir = os.path.join(base_dir, "common")

# Get the user's home directory
home_dir = os.path.expanduser("~")

# Add 'holly-script-collection' and the home directory to sys.path
# Adding at the beginning prioritizes these locations
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
if home_dir not in sys.path:
    sys.path.insert(0, home_dir)


import telebot
from telebot import types
from time import sleep
import subprocess

from common.pi import pitemp, pimemory, pidisk, picpuusage, piuptime, restart
from _secrets import whitelist, hollytoken

import re

#from common.local_ai_handler import ai_simple_task, ai_with_memory  # local testing
from common.openai_handler import ai_simple_task, ai_with_memory
from common.scraping import scrape_article_p_tags

#blacklist for urls
blacklisturls = ["reddit.com", "instagram.com", "youtube.com", "tiktok.com", "twitter.com"]

bot = telebot.TeleBot(hollytoken)


def check_user(message, bot, _id):
    print(_id)
    if str(_id) not in whitelist:
        reply_text = "Sorry, this is a private bot."
        bot.send_message(_id, text=reply_text)
        return False
    else:
        return True


@bot.message_handler(commands=["holly", "start"])
def start(message):
    """
    method to handle the /start or /holly command and create keyboard
    """
    chat_id = message.chat.id

    # defining the keyboard layout
    kbd = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Use resize for better display
    kbd.row("Holly status")  # adds one row with one button
    kbd.row("Holly uptime")  # adds another row with one button

    # sending the reply to activate the keyboard
    bot.send_message(chat_id, text="Holly activated", reply_markup=kbd)

def check_status():
    msg = ""
    scripts = ["reddit_bot.py", "shit_weather.py", "train.py", "tombot.py", "feedy.py"]
    for script in scripts:
        l = subprocess.getstatusoutput("ps aux | grep " + script + "| grep -v grep | awk '{print $2}'")
        if l[1]:
            msg += script + " is running \n"
        else:
            msg += script + " is not running \n"
    return msg

def restart():
    subprocess.call("/home/holly/holly-script-collection/start_telebots.sh", shell=True)


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
        msg = msg + "\n\n 🌡️ {}c\n📈 {} \n🐏 {} \n💾 {}\n\n".format(
            pitemp(), picpuusage(), pimemory(), pidisk()
        )
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
    if not check_user(message, bot, chat_id):
        return
    # delete(None, chat_id, message.message_id) # Context is not directly available in telebot
    bot.send_message(chat_id, piuptime(), reply_markup=types.ReplyKeyboardRemove())
    # delete(None, chat_id, message.message_id) # Context is not directly available in telebot

# Function to find URLs in a message
def find_urls(text):
    # Regular expression pattern for URLs
    url_pattern = r"(https?://[^\s]+)"
    return re.findall(url_pattern, text)

@bot.message_handler(func=lambda message: message.text)
def handle_message(message):
    if not check_user(message, bot, message.chat.id):
        return

    text = message.text or ""
    chat_id = message.chat.id

    # Only respond in groups if the bot is explicitly mentioned
    if message.chat.type in ["group", "supergroup"]:
        if f"@{bot.get_me().username}" not in text:
            return
        # Strip the mention for cleaner AI prompt
        text = text.replace(f"@{bot.get_me().username}", "").strip()

    original_message_text_for_ai = None

    if message.reply_to_message and message.reply_to_message.from_user.username == bot.get_me().username:
        original_message_text_for_ai = message.reply_to_message.text
        prompt_for_ai = f"You are responding to the following message: '{original_message_text_for_ai}'. The user's reply is: '{text}'."
    else:
        prompt_for_ai = text

    if prompt_for_ai:
        try:
            reply = ai_with_memory(chat_id, prompt_for_ai)
            bot.reply_to(message, str(reply), parse_mode="Markdown")
        except Exception as e:
            print(f"Error in ai_with_memory: {e}")
            #bot.reply_to(message, "Sorry, there was an error processing your request.", parse_mode="Markdown")
        return

    urls = find_urls(text)
    if urls:
        # Check if the URL is a Reddit or instagram link ect
        if any(blacklist in urls[0] for blacklist in blacklisturls):
            #bot.reply_to(message, "Sorry, I can't process that URL.")
            return

        article_text = scrape_article_p_tags(urls[0])
        try:
            response = ai_simple_task(
                "Condense the following text into a summary of 350 characters or less, focusing solely on the core content. Remove all privacy, cookie, feedback, and legal statements. Provide the summary text only, without any introductory phrases, headings, or character counts. Text:"
                + article_text
            )
            if response:
                bot.reply_to(message, str(response), parse_mode="Markdown")
        except Exception as e:
            print("AI summary error:", e)


@bot.message_handler(commands=["restart"])
def restart_command(message):
    chat_id = message.chat.id
    # Assuming check_user function can work with telebot's message object
    if check_user(message, None, chat_id) == True:
        print("restarting")
        bot.send_message(chat_id=chat_id, text="restarting this bitch")
        cmd = "bash /home/holly/holly-script-collection/start_telebots.sh"
        Popen([cmd], shell=True)
        # subprocess.call(['sh', '$HOME/start.sh'])


if __name__ == "__main__":
    print("Bot started...")
    bot.polling(none_stop=True)

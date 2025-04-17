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

from _secrets import whitelist, reddittoken, groupchatid

import telebot
import re
import asyncio
from red_downloader import RedDownloader


# Replace with the path where you want to save downloaded files.  Make sure the bot has write permissions.
DOWNLOAD_PATH = "/home/holly/downloads/"  # Example: "/home/user/downloads/" or "./downloads/"

bot = telebot.TeleBot(reddittoken)
downloader = RedDownloader(
    download_dir=DOWNLOAD_PATH,
    workers=5,  # Adjust as needed
    log_level="INFO",  #  "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
)

async def download_and_send(reddit_url, chat_id):
    """
    Downloads media from a Reddit URL and sends it to a Telegram chat.

    Args:
        reddit_url (str): The Reddit URL to download from.
        chat_id (int): The ID of the Telegram chat to send the media to.
    """
    try:
        print(f"Downloading from: {reddit_url}") # added for debug
        result = await downloader.download(reddit_url)
        print(f"Download result: {result}") # added for debug

        if result and result.files:
            for file_path in result.files:
                try:
                    if result.is_video:
                        with open(file_path, 'rb') as video:
                            bot.send_video(chat_id, video)
                    elif result.is_image:
                         with open(file_path, 'rb') as image:
                            bot.send_photo(chat_id, image)
                    else:
                        with open(file_path, 'rb') as file:
                            bot.send_document(chat_id, file)
                except Exception as e:
                    print(f"Error sending {file_path} to Telegram: {e}")
                    bot.send_message(chat_id, f"Failed to send media file. Error: {e}")

            if result.title:
                bot.send_message(chat_id, f"Post Title: {result.title}\nOriginal URL: {reddit_url}")
        elif result and result.error:
            error_message = f"Download failed: {result.error}"
            print(error_message)
            bot.send_message(chat_id, error_message)
        else:
            message = "No media found or download was unsuccessful."
            print(message)
            bot.send_message(chat_id, message)

    except Exception as e:
        print(f"Error processing URL {reddit_url}: {e}")
        bot.send_message(chat_id, f"Error processing the Reddit URL: {e}")

def find_reddit_urls(text):
    """
    Finds Reddit URLs in a given text.

    Args:
        text (str): The text to search for Reddit URLs.

    Returns:
        list: A list of Reddit URLs found in the text.
    """
    reddit_url_pattern = r"https?://(www\.)?reddit\.com/(r/[a-zA-Z0-9_]+/)?(comments/[a-zA-Z0-9_]+/)?[a-zA-Z0-9_-]+"
    return re.findall(reddit_url_pattern, text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """
    Handles incoming messages, checks for Reddit URLs, and downloads/sends media.
    """
    reddit_urls = find_reddit_urls(message.text)
    if reddit_urls:
        for url in reddit_urls:
            # Use asyncio.run() to bridge the async download_and_send with the sync telebot
            asyncio.run(download_and_send(url, message.chat.id))
    #  Removed the else condition, as it would send the message for every non-reddit url
    #  present in any message.

def main():
    """
    Main function to start the Telegram bot.
    """
    try:
        # Create the download directory if it doesn't exist
        import os
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)

        print("Bot started. Listening for messages...")
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Error starting the bot: {e}")
    finally:
        print("Bot stopped.")
        downloader.close()  # Ensure the downloader is closed properly.

if __name__ == "__main__":
    main()


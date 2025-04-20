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

from _secrets import whitelist, reddittoken
import telebot
from telebot import types
from telebot.types import InputMediaPhoto
import re
from common.reddit import download_reddit_media
from common.insta import download_instagram_post


bot = telebot.TeleBot(reddittoken)

# --- Regex to match Reddit URLs including short links, gallery, and comments ---
REDDIT_URL_PATTERN = re.compile(
    r'(https?://(?:www\.)?(?:reddit\.com/r/\w+/(?:comments/\w+/\S+)?|reddit\.com/gallery/\w+|redd\.it/\w+))',
    re.IGNORECASE
)

# --- Regex to match Instagram URLs ---
INSTAGRAM_URL_PATTERN = re.compile(r'(https?://(?:www\.)?instagram\.com/(?:p/\w+/|reel/\w+/|tv/\w+/))', re.IGNORECASE)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    urls = REDDIT_URL_PATTERN.findall(message.text)

    if not urls:
        return

    for url in urls:
        #bot.send_message(message.chat.id, f"🔍 Downloading media from Reddit URL:\n{url}")

        try:
            result = download_reddit_media(url)
            media_files = result.get("files", [])
            metadata = result.get("metadata", {})
            caption = f"📥 *{metadata.get('title', 'Untitled')}*\n🔗 [Reddit Post]({metadata.get('permalink')})"
            caption = caption[:1024]  # Telegram caption limit

            if not media_files:
                bot.send_message(message.chat.id, "⚠️ No media found to download.")
                continue

            # If it's a gallery (multiple images), send as media group
            if all(os.path.splitext(f)[1].lower() in ['.jpg', '.jpeg', '.png'] for f in media_files) and len(media_files) > 1:
                media_group = []
                for i, file_path in enumerate(media_files):
                    with open(file_path, 'rb') as f:
                        media = types.InputMediaPhoto(f.read(), caption=caption if i == 0 else None, parse_mode="Markdown")
                        media_group.append(media)
                bot.send_media_group(message.chat.id, media_group)

            else:
                # Send individually (single photo, video, or document)
                for file_path in media_files:
                    ext = os.path.splitext(file_path)[1].lower()
                    with open(file_path, "rb") as media:
                        if ext in [".jpg", ".jpeg", ".png", ".gif"]:
                            bot.send_photo(message.chat.id, media, caption=caption, parse_mode="Markdown")
                        elif ext == ".mp4":
                            bot.send_video(message.chat.id, media, caption=caption, parse_mode="Markdown")
                        else:
                            bot.send_document(message.chat.id, media, caption=caption, parse_mode="Markdown")

        except Exception as e:
            print(f"[ERROR] {e}")
            bot.send_message(message.chat.id, f"❌ Error processing the Reddit URL:\n{url}\n{e}")

    # Process Instagram URLs after Reddit URLs
    instagram_urls = INSTAGRAM_URL_PATTERN.findall(message.text)
    for url in instagram_urls:
        try:
            file = download_instagram_post(url)
            with open(file, 'rb') as media:
                if file.lower().endswith(".mp4"):
                    bot.send_video(message.chat.id, media, supports_streaming=True, caption="📥", reply_to_message_id=message.message_id)
                elif file.lower().endswith(".jpg"):
                    bot.send_photo(message.chat.id, media, caption="📥", reply_to_message_id=message.message_id)

            # Clean up the downloaded file
            os.remove(file)
        except Exception as e:
            print(f"[ERROR] Instagram: {e}")
            #bot.send_message(message.chat.id, f"❌ Error processing the Instagram URL:\n{url}\n{e}", reply_to_message_id=message.message_id)

if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling()
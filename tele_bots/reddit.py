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

from _secrets import whitelist, reddittoken, groupchatid, r_client_id, r_client_secret
# Replace with your Reddit API credentials

REDDIT_USER_AGENT = "idk"  

bot = telebot.TeleBot(BOT_TOKEN)

reddit = praw.Reddit(
    client_id=r_client_id,
    client_secret=r_client_secret,
    user_agent=REDDIT_USER_AGENT,
)


def download_file(url, filename):
    """Downloads a file from a URL."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes
        with open(filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return False
    except Exception as e:
        print(f"Error writing file {filename}: {e}")
        return False


async def download_and_send(reddit_url, chat_id):
    """
    Downloads media from a Reddit URL using PRAW and sends it to a Telegram chat.
    """
    try:
        post = reddit.submission(url=reddit_url)
        print(f"Downloading from: {reddit_url}")

        # Determine media type and download URL
        media_url = None
        if post.is_video:
            if hasattr(post.media, 'reddit_video'):
              media_url = post.media.reddit_video['fallback_url']
            else:
               print(f"No downloadable video found in post: {reddit_url}")
               bot.send_message(chat_id, f"No downloadable video found.")
               return
        elif post.url.endswith(('.jpg', '.png', '.gif')):
            media_url = post.url
        # Handle gallery
        elif hasattr(post, "is_gallery") and post.is_gallery:
            for item_id, item in post.media_metadata.items():
                if item['type'] == 'image':
                    media_url = item['s']['u']  # Full-size image URL
                    break #take first image
        else:
            print(f"Unsupported media type in post: {reddit_url}")
            bot.send_message(chat_id, f"Unsupported media type.")
            return

        if media_url:
            file_extension = os.path.splitext(media_url)[1]
            filename = f"{DOWNLOAD_PATH}{post.id}{file_extension}"
            if download_file(media_url, filename):
                try:
                    if post.is_video:
                        with open(filename, 'rb') as video:
                            bot.send_video(chat_id, video, caption=post.title)
                    elif post.url.endswith(('.jpg', '.png', '.gif')):
                        with open(filename, 'rb') as image:
                            bot.send_photo(chat_id, image, caption=post.title)
                    else:  # Handle other file types if needed
                        with open(filename, 'rb') as file:
                            bot.send_document(chat_id, file, caption=post.title)
                    bot.send_message(chat_id, f"Post Title: {post.title}\nOriginal URL: {reddit_url}")

                except Exception as e:
                    print(f"Error sending media to Telegram: {e}")
                    bot.send_message(chat_id, f"Failed to send media. Error: {e}")
            else:
                bot.send_message(chat_id, f"Failed to download media from {media_url}")
        else:
            bot.send_message(chat_id, f"No media found to download.")

    except praw.exceptions.InvalidURL:
        print(f"Invalid Reddit URL: {reddit_url}")
        bot.send_message(chat_id, f"Invalid Reddit URL.")
    except Exception as e:
        print(f"Error processing URL {reddit_url}: {e}")
        bot.send_message(chat_id, f"Error processing the Reddit URL: {e}")



def find_reddit_urls(text):
    """
    Finds Reddit URLs in a given text.
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
            asyncio.run(download_and_send(url, message.chat.id))



def main():
    """
    Main function to start the Telegram bot.
    """
    try:
        # Create the download directory if it doesn't exist
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)
        print("Bot started. Listening for messages...")
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Error starting the bot: {e}")
    finally:
        print("Bot stopped.")



if __name__ == "__main__":
    main()


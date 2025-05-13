import sys
import os
import uuid
import requests
import shutil
import praw
from PIL import Image

# Get the absolute path to the directory containing holly.py
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
common_dir = os.path.join(base_dir, "common")
home_dir = os.path.expanduser("~")

# Add paths to sys.path
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
if home_dir not in sys.path:
    sys.path.insert(0, home_dir)

# --- Secrets ---
from _secrets import whitelist, reddittoken, groupchatid, r_client_id, r_client_secret

# --- Constants ---
BASE_DOWNLOAD_DIR = "/home/holly/downloads/reddit"
MAX_IMAGE_SIZE = (1280, 1280)  # Telegram safe max
os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)

# --- Reddit Client ---
reddit = praw.Reddit(
    client_id=r_client_id,
    client_secret=r_client_secret,
    user_agent="reddit_media_downloader"
)

def clean_download_folder():
    """
    Deletes all files in the Reddit download directory.
    """
    try:
        for filename in os.listdir(BASE_DOWNLOAD_DIR):
            file_path = os.path.join(BASE_DOWNLOAD_DIR, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        print("[CLEANUP] Download directory cleaned.")
    except Exception as e:
        print(f"[ERROR] Cleanup failed: {e}")

def download_file(url, filename, is_image=False):
    """
    Downloads a file from a URL to a given filename.
    If it's an image, resizes it if needed.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Resize image if necessary
        if is_image:
            try:
                with Image.open(filename) as img:
                    if img.width > MAX_IMAGE_SIZE[0] or img.height > MAX_IMAGE_SIZE[1]:
                        print(f"[RESIZE] Image too large, resizing {filename}")
                        img.thumbnail(MAX_IMAGE_SIZE)
                        img.save(filename)
            except Exception as e:
                print(f"[WARN] Could not resize image: {e}")

        return filename
    except Exception as e:
        print(f"[ERROR] Failed to download {url} - {e}")
        return None

def download_reddit_media(reddit_url):
    """
    Downloads media (image, video, gallery) from a Reddit URL.
    Cleans up the target folder first.
    Returns a dict with metadata and list of file paths.
    """
    clean_download_folder()

    post = reddit.submission(url=reddit_url)
    downloaded_files = []

    print(f"Processing: {reddit_url}")
    print(f"Title: {post.title}")
    print(f"Post ID: {post.id}")

    # --- Video ---
    if post.is_video and post.media and 'reddit_video' in post.media:
        video_url = post.media['reddit_video']['fallback_url']
        ext = os.path.splitext(video_url.split("?")[0])[1] or ".mp4"
        filename = os.path.join(BASE_DOWNLOAD_DIR, f"{post.id}{ext}")
        if download_file(video_url, filename):
            downloaded_files.append(filename)

    # --- Gallery ---
    elif hasattr(post, "media_metadata") and post.media_metadata:
        for item_id, item in post.media_metadata.items():
            if item['e'] == 'Image':
                image_url = item['s']['u'].replace("&amp;", "&")
                ext = os.path.splitext(image_url.split("?")[0])[1] or ".jpg"
                filename = os.path.join(BASE_DOWNLOAD_DIR, f"{post.id}_{item_id}{ext}")
                if download_file(image_url, filename, is_image=True):
                    downloaded_files.append(filename)

    # --- Single Image ---
    elif post.url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
        image_url = post.url
        ext = os.path.splitext(image_url.split("?")[0])[1]
        filename = os.path.join(BASE_DOWNLOAD_DIR, f"{post.id}{ext}")
        if download_file(image_url, filename, is_image=True):
            downloaded_files.append(filename)

    else:
        print("[WARN] Unsupported or no media found.")

    # --- Collect metadata ---
    post_metadata = {
        "id": post.id,
        "title": post.title,
        "author": str(post.author),
        "subreddit": str(post.subreddit),
        "permalink": f"https://reddit.com{post.permalink}",
        "url": post.url,
        "is_video": post.is_video,
        "num_files": len(downloaded_files)
    }

    if downloaded_files:
        print(f"[SUCCESS] Downloaded {len(downloaded_files)} file(s):")
        for f in downloaded_files:
            print("  •", f)
    else:
        print("[INFO] No media downloaded.")

    return {
        "files": downloaded_files,
        "metadata": post_metadata
    }


def resolve_reddit_url(url):
    try:
        response = requests.get(url, allow_redirects=True, timeout=10)
        final_url = response.url
        # Reddit may return the main subreddit page if link is invalid or already resolved
        if "reddit.com/r/" in final_url and "comments" in final_url:
            return final_url
        return final_url  # might still work with download_reddit_media
    except Exception as e:
        print(f"[ERROR] Failed to resolve URL: {url} -> {e}")
        return url  # Fallback to original
        
# Example test (uncomment to run standalone)
# if __name__ == "__main__":
#     url = "https://www.reddit.com/r/interestingasfuck/comments/1bx4i6y/how_pov_videos_are_filmed/"
#     result = download_reddit_media(url)
#     print(result)


'''

This module handles downloading Instagram posts using Instaloader.

'''
import instaloader
import re
import os
import shutil
import logging

# Setup logging
logging.basicConfig(
    filename='/home/holly/errorlog.txt',
    filemode='a',
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    level=logging.INFO
)

def find_media_files(folder_path):
    """
    Searches for media files in the specified folder.

    Returns:
        - The path to the first .mp4 file found, if any.
        - Otherwise, a list of all .jpg file paths.
        - Returns None if no .mp4 or .jpg files are found.
    """
    mp4_path = None
    jpg_paths = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file.lower().endswith(".mp4") and not mp4_path:
                mp4_path = file_path
            elif file.lower().endswith(".jpg"):
                jpg_paths.append(file_path)

    if mp4_path:
        return mp4_path
    elif jpg_paths:
        return jpg_paths
    else:
        return None



def get_shortcode_from_url(url_string):
    """
    Extracts the shortcode from an Instagram URL string.
    This function now *expects* a string URL, as the calling logic
    (INSTAGRAM_URL_PATTERN in reddit_bot.py) ensures a full URL string is passed.
    """
    if not isinstance(url_string, str):
        logging.error(f"get_shortcode_from_url received non-string URL as input: {type(url_string)} - {url_string}")
        return None

    # This regex specifically extracts the shortcode part from a full URL string
    match = re.search(r'/(p|reel|tv)/([A-Za-z0-9_-]+)', url_string)
    if match:
        return match.group(2)
    logging.warning(f"No Instagram shortcode found in URL string: {url_string}")
    return None
    
def download_instagram_post(url):
    target_dir = "instagram_temp_files"
    

    # Clean previous downloads
    if os.path.exists(target_dir):
        try:
            shutil.rmtree(target_dir)
            logging.info("Cleared previous Instagram download directory.")
        except Exception as cleanup_error:
            logging.warning(f"Failed to clear directory: {target_dir} — {cleanup_error}")
    os.makedirs(target_dir, exist_ok=True)

    shortcode = get_shortcode_from_url(url)
    if not shortcode:
        logging.error(f"Invalid Instagram URL or shortcode not found: {url}")
        return None

    try:
        L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_comments=False,
            save_metadata=False,
            post_metadata_txt_pattern=''
        )
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=target_dir)
        logging.info(f"Successfully downloaded post: {shortcode}")
        media = find_media_files("/home/holly/" + target_dir)
        return media if media else None
    except Exception as e:
        logging.exception(f"Error downloading Instagram post ({shortcode}): {e}")
        return None

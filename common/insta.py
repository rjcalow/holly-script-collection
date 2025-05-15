import instaloader, re, os

L = instaloader.Instaloader()

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

def get_shortcode_from_url(url):
    match = re.search(r'/(p|reel|tv)/([A-Za-z0-9_-]+)/', url)
    if match:
        return match.group(2)
    return None

def download_instagram_post(url):
    L = instaloader.Instaloader(
    download_videos=True,
    download_video_thumbnails=False,
    download_comments=False,
    save_metadata=False,
    post_metadata_txt_pattern=''
    )


    shortcode = get_shortcode_from_url(url)
    
    if shortcode:
        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            L.download_post(post, target="downloads")
            print("Post Downloaded")
            media = find_media_files("/home/holly/downloads")
            if media:
                return media

        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("Invalid URL or could not extract shortcode.")
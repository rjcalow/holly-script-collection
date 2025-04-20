import instaloader, re, os

L = instaloader.Instaloader()

def find_mp4_video(folder_path):
  """
  Finds the path of the first MP4 video file encountered in the given folder.

  Args:
    folder_path: The path to the folder to search.

  Returns:
    The full path to the MP4 video file, or None if no MP4 video is found.
  """
  for root, dirs, files in os.walk(folder_path):
    for file in files:
      if file.lower().endswith(".mp4") or file.lower().endswith(".jpg"):
        return os.path.join(root, file)
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
            video = find_mp4_video("/home/holly/downloads")
            if video:
                return video

        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("Invalid URL or could not extract shortcode.")
# flickr_uploader.py
import os, sys

# Get the absolute path
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
from _secrets import flickrkey, flickrsecret


import flickrapi

# Set token cache location
TOKEN_CACHE = os.path.expanduser("~/.flickr_token")

# Create Flickr API object with token cache
flickr = flickrapi.FlickrAPI(
    flickrkey,
    flickrsecret,
    format='parsed-json',
    token_cache_location=TOKEN_CACHE
)

def upload_to_flickr(image_path, title="", tags="", description=""):
    # Ensure tags is a string, even if passed as a list
    if isinstance(tags, list):
        tags = " ".join(tags)

    if not flickr.token_valid(perms='write'):
        print("🔐 Authorizing Flickr (first run only)...")
        flickr.get_request_token(oauth_callback='oob')
        authorize_url = flickr.auth_url(perms='write')
        print(f"🔗 Go to this URL to authorize: {authorize_url}")
        verifier = input("🔑 Enter the verifier code: ")
        flickr.get_access_token(verifier)
        print("✅ Authorization complete and token saved.")

    print(f"📤 Uploading: {image_path}...")

    try:
        response = flickr.upload(
            filename=image_path,
            title=title,
            tags=tags,
            description=description
        )
        print("✅ Upload complete.")
        return response
    except Exception as e:
        print("❌ Upload failed:", e)
        return None



# def upload_to_flickr(image_path, title="", tags=""):
#     if not flickr.token_valid(perms='write'):
#         print("Authorizing Flickr...")  # Run manually once
#         flickr.get_request_token(oauth_callback='oob')
#         authorize_url = flickr.auth_url(perms='write')
#         print(f"Go to this URL to authorize: {authorize_url}")
#         verifier = input("Enter the verifier code: ")
#         flickr.get_access_token(verifier)

#     print(f"Uploading {image_path}...")
#     response = flickr.upload(filename=image_path, title=title, tags=tags)
#     print("Upload complete.")
#     return response

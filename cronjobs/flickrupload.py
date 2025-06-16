# daily_scheduler.py
import os
import yaml
from flickr_uploader import upload_to_flickr

# Folder where images and YAMLs are stored
WATCH_FOLDER = "/home/holly/flickr_uploads"
SUPPORTED_EXTENSIONS = ['.jpg', '.jpeg', '.png']

def find_candidates(folder):
    candidates = []
    for file in os.listdir(folder):
        if any(file.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            yaml_file = os.path.splitext(file)[0] + '.yaml'
            yaml_path = os.path.join(folder, yaml_file)
            if os.path.exists(yaml_path):
                candidates.append((os.path.join(folder, file), yaml_path))
    return candidates

def select_best_candidate(candidates):
    best = None
    highest_priority = -1
    for image_path, yaml_path in candidates:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
            priority = data.get('priority', 0)
            if priority > highest_priority:
                best = (image_path, yaml_path, data)
                highest_priority = priority
    return best

def run_daily_upload():
    candidates = find_candidates(WATCH_FOLDER)
    if not candidates:
        print("No upload candidates found.")
        return

    selected = select_best_candidate(candidates)
    if selected:
        image_path, yaml_path, metadata = selected
        title = metadata.get('title', '')
        tags = metadata.get('tags', '')
        upload_to_flickr(image_path, title, tags)

        os.remove(image_path)
        os.remove(yaml_path)
        print(f"Uploaded and removed: {image_path}, {yaml_path}")
    else:
        print("No valid image to upload.")

if __name__ == "__main__":
    run_daily_upload()

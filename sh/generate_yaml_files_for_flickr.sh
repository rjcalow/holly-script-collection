#!/bin/bash

# This script generates YAML files for images in a specified folder.

# Folder containing the images
WATCH_FOLDER="/home/holly/flickr_uploads"

# Supported image extensions (case insensitive)
shopt -s nocaseglob
cd "$WATCH_FOLDER" || exit 1

for img in *.jpg *.jpeg *.png; do
    # Skip if no match
    [ -e "$img" ] || continue

    # Get base name without extension
    base="${img%.*}"
    yaml="${base}.yaml"

    # Skip if YAML already exists
    if [ -f "$yaml" ]; then
        echo "Skipping existing YAML: $yaml"
        continue
    fi

    # Create YAML with default placeholders
    cat <<EOF > "$yaml"
title: "${base//_/ }"
tags: ["example", "tag"]
description: "Write a description for $img"
priority: 1
EOF

    echo "Created: $yaml"
done

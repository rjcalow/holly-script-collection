#!/bin/bash

WATCH_FOLDER="/home/holly/flickr_uploads"
cd "$WATCH_FOLDER" || exit 1

for img in *.jpg *.jpeg *.png; do
    [ -e "$img" ] || continue

    base="${img%.*}"
    yaml="${base}.yaml"

    if [ -f "$yaml" ]; then
        echo "Skipping existing YAML: $yaml"
        continue
    fi

    # Extract EXIF metadata
    make=$(exiftool -s3 -Make "$img")
    model=$(exiftool -s3 -Model "$img")
    lens=$(exiftool -s3 -LensModel "$img")
    focal=$(exiftool -s3 -FocalLength "$img")
    fstop=$(exiftool -s3 -FNumber "$img")
    description=$(exiftool -s3 -ImageDescription "$img")

    # Clean fallbacks
    [ -z "$make" ] && make="UnknownMake"
    [ -z "$model" ] && model="UnknownModel"
    [ -z "$lens" ] && lens="UnknownLens"
    [ -z "$focal" ] && focal="UnknownFocal"
    [ -z "$fstop" ] && fstop="UnknownFStop"
    [ -z "$description" ] && description="No description in EXIF"

    # Format tags list
    tags="[$(printf '"%s", ' "$make" "$model" "$lens" "$focal" "f/$fstop" | sed 's/, $//')]"

    # Write YAML
    cat <<EOF > "$yaml"
title: "${base//_/ }"
tags: $tags
description: "$description"
priority: 1
EOF

    echo "Created: $yaml"
done

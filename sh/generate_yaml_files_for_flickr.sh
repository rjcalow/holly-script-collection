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
    iso=$(exiftool -s3 -ISO "$img")
    focal=$(exiftool -s3 -FocalLength "$img")
    date=$(exiftool -s3 -DateTimeOriginal "$img")

    # Fallbacks
    [ -z "$make" ] && make="UnknownMake"
    [ -z "$model" ] && model="UnknownModel"

    # Compose tag list
    tags="[$(printf '"%s", ' "$make" "$model" "$lens" "$iso" "$focal" "$date" | sed 's/, $//')]"

    cat <<EOF > "$yaml"
title: "${base//_/ }"
tags: $tags
description: "Photo taken with $make $model, lens: $lens, ISO: $iso, focal length: $focal"
priority: 1
EOF

    echo "Created: $yaml"
done

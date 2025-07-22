#!/bin/bash

WATCH_FOLDER="/home/holly/flickr_uploads"
cd "$WATCH_FOLDER" || exit 1

# Convert passed arguments to tag format
if [ "$#" -gt 0 ]; then
    custom_tags="["
    for tag in "$@"; do
        custom_tags+="\"$tag\", "
    done
    custom_tags="${custom_tags%, }]"  # remove trailing comma and space
else
    custom_tags=""
fi

for img in *.jpg *.jpeg *.JPG; do
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

    # Determine tags
    if [ -n "$custom_tags" ]; then
        tags="$custom_tags"
    elif [[ "$make" == "OLYMPUS IMAGING CORP." && "$model" == "C70Z,C7000Z" ]]; then
        tags='["olympus", "c70", "olympus c70", "c70z", "c7000z", "compact digital camera", "digicam", "ccd sensor", "snapshot", "point and shoot", "ccd", "digital", "vsco"]'
    else
        tags="[$(printf '"%s", ' "$make" "$model" "$lens" "$focal" "f/$fstop" | sed 's/, $//')]"
    fi

    # Write YAML
    cat <<EOF > "$yaml"
title: "${base//_/ }"
tags: $tags
description: "$description"
priority: 1
EOF

    echo "Created: $yaml"
done

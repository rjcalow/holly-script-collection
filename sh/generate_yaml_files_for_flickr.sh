#!/bin/bash

WATCH_FOLDER="/home/holly/flickr_uploads"
cd "$WATCH_FOLDER" || exit 1

custom_tags=""
custom_description=""
collecting_tags=false

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --tags)
            collecting_tags=true
            custom_tags="["
            shift
            while [[ $# -gt 0 && ! "$1" =~ ^-- ]]; do
                custom_tags+="\"$1\", "
                shift
            done
            custom_tags="${custom_tags%, }]"  # remove trailing comma and space
            collecting_tags=false
            ;;
        --description)
            shift
            custom_description="$1"
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            shift
            ;;
    esac
done

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
    exif_description=$(exiftool -s3 -ImageDescription "$img")

    # Fallbacks
    [ -z "$make" ] && make="UnknownMake"
    [ -z "$model" ] && model="UnknownModel"
    [ -z "$lens" ] && lens="UnknownLens"
    [ -z "$focal" ] && focal="UnknownFocal"
    [ -z "$fstop" ] && fstop="UnknownFStop"
    [ -z "$exif_description" ] && exif_description="No description in EXIF"

    # Use user description if provided
    if [ -n "$custom_description" ]; then
        final_description="$custom_description"
    else
        final_description="$exif_description"
    fi

    # Use tags
    if [ -n "$custom_tags" ]; then
        tags="$custom_tags"
    elif [[ "$make" == "OLYMPUS IMAGING CORP." && "$model" == "C70Z,C7000Z" ]]; then
        tags='["olympus", "c70", "olympus c70", "c70z", "c7000z", "compact digital camera", "digicam", "ccd sensor", "snapshot", "point and shoot", "ccd", "digital", "vsco"]'
    elif [[ "$make" == "JK Imaging, Ltd." && "$model" == "KODAK PIXPRO C1" ]]; then
        tags='["KODAK", "PIXPRO", "c1", "pixproc1", "compact digital camera", "digicam", "snapshot", "point and shoot", "p&s", "digital", "vsco"]'
    else
        tags="[$(printf '"%s", ' "$make" "$model" "$lens" "$focal" "f/$fstop" | sed 's/, $//')]"
    fi

    # Write YAML
    cat <<EOF > "$yaml"
title: "${base//_/ }"
tags: $tags
description: "$final_description"
priority: 1
EOF

    echo "Created: $yaml"
done

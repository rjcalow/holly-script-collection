#!/bin/bash
#
# === Flickr YAML Generator ===
#
# This script scans a folder of images (*.jpg, *.jpeg, *.JPG) and creates
# YAML metadata files for each one, ready for Flickr uploading.
#
# USAGE:
#   ./make_yaml.sh [--tags tag1 tag2 ...] [--description "Your description here"]
#
# OPTIONS:
#   --tags         Add custom tags (space-separated list). Example:
#                  ./make_yaml.sh --tags "film" "analogue" "grainy"
#
#   --description  Provide a custom description. If omitted, the script
#                  will use the EXIF ImageDescription if available.
#
# NOTES:
#   - If a YAML file already exists for an image, it will be skipped.
#   - Special handling for some cameras:
#       * Olympus C70Z,C7000Z → adds Olympus digicam tags
#       * Kodak PIXPRO C1     → adds Kodak digicam tags
#   - Even if you provide custom tags, the Olympus/Kodak sets will still
#     be added automatically if the camera matches.
#
# REQUIREMENTS:
#   - bash
#   - exiftool
#
# OUTPUT:
#   Creates a YAML file for each image, e.g.:
#     photo1.jpg → photo1.yaml
#

WATCH_FOLDER="/home/holly/flickr_uploads"
cd "$WATCH_FOLDER" || exit 1

custom_tags=()
custom_description=""

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --tags)
            shift
            while [[ $# -gt 0 && ! "$1" =~ ^-- ]]; do
                custom_tags+=("$1")
                shift
            done
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

    # Description selection
    if [ -n "$custom_description" ]; then
        final_description="$custom_description"
    else
        final_description="$exif_description"
    fi

    # --- TAG LOGIC ---
    tags=()

    # Always include make/model/lens/focal/fstop
    tags+=("$make" "$model" "$lens" "$focal" "f/$fstop")

    # Add Olympus digicam tags if matching
    if [[ "$make" == "OLYMPUS IMAGING CORP." && "$model" == "C70Z,C7000Z" ]]; then
        tags+=("olympus" "c70" "olympus c70" "c70z" "c7000z" "compact digital camera" \
               "digicam" "ccd sensor" "snapshot" "point and shoot" "ccd" "digital" "vsco")
    fi

    # Add Kodak digicam tags if matching
    if [[ "$make" == "JK Imaging, Ltd." && "$model" == "KODAK PIXPRO C1" ]]; then
        tags+=("KODAK" "PIXPRO" "c1" "pixproc1" "compact digital camera" \
               "digicam" "snapshot" "point and shoot" "p&s" "digital" "vsco")
    fi

    # Add custom tags (always applied on top)
    if [ ${#custom_tags[@]} -gt 0 ]; then
        tags+=("${custom_tags[@]}")
    fi

    # Deduplicate tags
    unique_tags=($(printf "%s\n" "${tags[@]}" | awk '!seen[$0]++'))

    # Format into JSON-like array
    tag_str="["
    for t in "${unique_tags[@]}"; do
        tag_str+="\"$t\", "
    done
    tag_str="${tag_str%, }]"
    # -----------------

    # Write YAML
    cat <<EOF > "$yaml"
title: "${base//_/ }"
tags: $tag_str
description: "$final_description"
priority: 1
EOF

    echo "Created: $yaml"
done

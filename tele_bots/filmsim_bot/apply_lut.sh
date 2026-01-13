#!/usr/bin/env bash
# apply_lut.sh — apply a .cube LUT to ONE image using G'MIC
# Usage: ./apply_lut.sh <input_image> <lut_cube_file> <output_image> [intensity_0_to_1] [comma_separated_tags]
set -euo pipefail

need() { command -v "$1" >/dev/null 2>&1; }

if ! need gmic; then
  echo "Error: gmic not found. Install it (e.g., 'sudo apt install gmic')." >&2
  exit 127
fi

# now allow up to 5 args (tags optional)
if [ "$#" -lt 3 ] || [ "$#" -gt 5 ]; then
  echo "Usage: $0 <input_image> <lut_cube_file> <output_image> [intensity_0_to_1] [comma_separated_tags]" >&2
  exit 2
fi

INPUT="$1"
LUT="$2"
OUTPUT="$3"
INTENSITY="${4:-1}"
TAGS_RAW="${5:-}"

[ -f "$INPUT" ] || { echo "Error: input image not found: $INPUT" >&2; exit 3; }
[ -f "$LUT"   ] || { echo "Error: LUT file not found: $LUT"   >&2; exit 4; }
mkdir -p "$(dirname "$OUTPUT")"

# Clamp intensity to [0,1]
[[ "$INTENSITY" == .* ]] && INTENSITY="0$INTENSITY"
INTENSITY="$(awk -v v="$INTENSITY" 'BEGIN{ if (v+0<0) v=0; if (v+0>1) v=1; printf "%.6f", v+0 }')"

# Apply LUT with linear blend:
# [0]=orig, [1]=orig copy, [2]=LUT → map LUT to [1], then (1-a)*[0] + a*[1] → [0]
gmic "$INPUT" -to_colormode 3 \
     "$INPUT" -to_colormode 3 \
     "$LUT" \
     map_clut[1] [2] rm[2] \
     mul[0] "{1-$INTENSITY}" \
     mul[1] "$INTENSITY" \
     add[0] [1] \
     noise_rgb[0] 0.6,0,0,0 \
     -to_colormode[0] 2 \
     -o[0] "$OUTPUT"


echo "Wrote: $OUTPUT (intensity=$INTENSITY)"

# --- metadata copy + annotate (optional) ---
if need exiftool; then
  LUT_BASENAME="$(basename "$LUT")"
  NOTE="Applied LUT: ${LUT_BASENAME}; Intensity=${INTENSITY}"

  # Copy all metadata from input to output
  exiftool -overwrite_original -P \
           -TagsFromFile "$INPUT" -all:all \
           "$OUTPUT" >/dev/null

  # Build subject/keyword args
  HARD_TAG="Made on telegram with @FilmSimBot"
  SUBJECT_ARGS=( -XMP:Subject+="LUT:${LUT_BASENAME}" -XMP:Subject+="$HARD_TAG" )
  KEYWORD_ARGS=( -IPTC:Keywords+="LUT:${LUT_BASENAME}" -IPTC:Keywords+="$HARD_TAG" )

  # Split comma-separated tags, trim whitespace, append
  if [ -n "$TAGS_RAW" ]; then
    IFS=',' read -r -a _tags <<< "$TAGS_RAW"
    for tag in "${_tags[@]}"; do
      t="$(printf '%s' "$tag" | sed 's/^[[:space:]]\+//; s/[[:space:]]\+$//')"
      [ -n "$t" ] || continue
      SUBJECT_ARGS+=( -XMP:Subject+="$t" )
      KEYWORD_ARGS+=( -IPTC:Keywords+="$t" )
    done
  fi

  # Write description + subjects/keywords + tool tag
  exiftool -overwrite_original -P \
           -EXIF:ImageDescription="$NOTE" \
           -XMP:Description="$NOTE" \
           -XMP:CreatorTool="apply_lut.sh + G'MIC" \
           "${SUBJECT_ARGS[@]}" \
           "${KEYWORD_ARGS[@]}" \
           "$OUTPUT" >/dev/null
else
  echo "Note: exiftool not found — output saved without metadata copy/annotation." >&2
fi

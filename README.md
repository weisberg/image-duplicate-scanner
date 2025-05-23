# Image Duplicate Scanner

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

A safe and intelligent tool for finding and managing duplicate images and their scaled versions. Features automatic dimension-based renaming and multiple perceptual hash algorithms for accurate detection.

## Features

### Safety Features
- **Non-destructive**: Moves files to a "discarded" folder instead of deleting
- **Dry-run mode**: Preview what would be moved without making changes
- **Interactive mode**: Confirm each scaled version before moving
- **Detailed logging**: Creates a timestamped log file of all actions
- **Automatic renaming**: Kept images are renamed to include dimensions (e.g., "photo-1200x800.jpg")
- **Multiple hash algorithms**: Uses 4 different perceptual hash types for accuracy
- **Aspect ratio checking**: Prevents false positives from images with different proportions
- **Color similarity checking**: Additional validation using average color comparison
- **Confidence scoring**: Shows how confident the algorithm is about each match

### Detection Capabilities
1. **Exact Duplicates**: Byte-for-byte identical files (100% accurate)
2. **Scaled Versions**: Same image at different resolutions
3. **Quality Variations**: Same image with different compression levels

## Installation

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or on macOS with Homebrew
brew install uv

# Make scripts executable
chmod +x setup.sh
./setup.sh
```

That's it! The scripts use inline dependencies that uv will automatically install on first run.

## Usage

### Basic Scan
```bash
uv run image_scanner.py           # Scan current directory
uv run image_scanner.py ~/Pictures # Scan specific directory
```

### Safe Exploration (Recommended for First Use)
```bash
# See what would be moved without actually moving anything
uv run image_scanner.py --dry-run

# Interactively confirm each scaled version
uv run image_scanner.py --interactive

# Combine both for maximum safety
uv run image_scanner.py --dry-run --interactive
```

### Adjusting Sensitivity
```bash
# Stricter matching (fewer false positives, may miss some matches)
uv run image_scanner.py --threshold 5

# More lenient matching (catches more variations, may have false positives)
uv run image_scanner.py --threshold 15

# Default is 10 (balanced)
```

### Testing Specific Images
```bash
# Compare two specific images to see their similarity scores
uv run compare_images.py image1.jpg image2.jpg
```

### Reviewing What Was Moved
```bash
# See a summary of what's in the discarded folder
uv run review_discarded.py

# Review discarded files from a specific scan
uv run review_discarded.py ~/Pictures
```

## How It Works

### Automatic File Renaming
When the scanner finds duplicates or scaled versions, it automatically renames the kept image to include its dimensions in the filename. For example:
- `photo.jpg` becomes `photo-1200x800.jpg`
- `sample.png` becomes `sample-640x480.png`

This helps you identify the resolution of kept images at a glance and prevents confusion when multiple versions existed.

### Multi-Hash Algorithm
The scanner uses multiple perceptual hash algorithms to reduce false positives:
- **pHash** (Perceptual Hash): Most reliable for scaled images
- **dHash** (Difference Hash): Good for detecting similar structures
- **wHash** (Wavelet Hash): Handles frequency information
- **aHash** (Average Hash): Basic similarity detection

### Decision Process
For an image to be considered a scaled version:
1. Aspect ratios must match (within 1% tolerance)
2. Primary hash differences must be below threshold
3. Color similarity must be above 70%
4. Different pixel counts (not same size)

### False Positive Prevention
- Different aspect ratios are never considered scaled versions
- Multiple hash types must agree
- Color checking prevents matching unrelated images with similar structures
- Interactive mode lets you review decisions

## Understanding the Threshold

The threshold parameter (default: 10) controls how similar images need to be:
- **0-5**: Very strict - only nearly identical images
- **6-10**: Balanced - good for most use cases
- **11-15**: Lenient - catches more variations but may have false positives
- **16+**: Very lenient - use with caution

Use `compare_images.py` to test what threshold works best for your images.

## Log Files

Each scan creates a detailed log file with:
- Timestamp for each action
- Exact duplicate groups found
- Scaled version pairs with confidence scores
- Reasons for each decision
- Summary statistics

## Tips for Best Results

1. **Start with dry-run**: Always use `--dry-run` first to preview changes
2. **Use interactive mode**: When unsure, use `--interactive` to review each decision
3. **Check the logs**: Review the log file for detailed information
4. **Test threshold**: Use `compare_images.py` on sample images to find optimal threshold
5. **Review discarded folder**: Check the discarded folder before permanently deleting

## Common Scenarios

### Family Photos
```bash
# Conservative approach for irreplaceable photos
uv run image_scanner.py ~/FamilyPhotos --threshold 5 --interactive
```

### Downloaded Images
```bash
# More aggressive for replaceable content
uv run image_scanner.py ~/Downloads --threshold 12
```

### Professional Photography
```bash
# Very strict to avoid losing variations
uv run image_scanner.py ~/Photography --threshold 3 --dry-run
```

## Limitations

- Cannot detect images that have been significantly edited (color correction, filters, etc.)
- Cropped images may not be detected as related
- Very small images (< 64x64) may produce unreliable hashes
- Black and white vs color versions may not match

## Recovery

All "deleted" files are in the `discarded` folder. To recover:
```bash
# Move specific file back
mv discarded/image.jpg .

# Recover all files
mv discarded/* .
```
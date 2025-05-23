#!/usr/bin/env python3
# /// script
# dependencies = [
#   "Pillow>=10.0.0",
# ]
# ///
"""
Review Discarded Images
Shows information about images in the discarded folder to help you verify the scanner's decisions.

Usage:
    uv run review_discarded.py [directory]
"""

import sys
from pathlib import Path
from PIL import Image
import argparse


def review_discarded_folder(directory: Path):
    """Review images in the discarded folder."""
    discarded_dir = directory / "discarded"
    
    if not discarded_dir.exists():
        print("No 'discarded' folder found. Run the image scanner first.")
        return
    
    images = list(discarded_dir.glob("*.png")) + list(discarded_dir.glob("*.jpg")) + list(discarded_dir.glob("*.jpeg"))
    images.extend(list(discarded_dir.glob("*.PNG")) + list(discarded_dir.glob("*.JPG")) + list(discarded_dir.glob("*.JPEG")))
    
    if not images:
        print("No images found in the discarded folder.")
        return
    
    print(f"Found {len(images)} images in discarded folder:")
    print("-" * 80)
    
    # Group by size
    size_groups = {}
    total_size = 0
    
    for img_path in sorted(images):
        try:
            with Image.open(img_path) as img:
                width, height = img.size
                pixels = width * height
                file_size = img_path.stat().st_size
                total_size += file_size
                
                size_key = f"{width}x{height}"
                if size_key not in size_groups:
                    size_groups[size_key] = []
                size_groups[size_key].append((img_path.name, file_size))
                
        except Exception as e:
            print(f"Error reading {img_path.name}: {e}")
    
    # Display by resolution
    print("\nImages grouped by resolution:")
    for size_key in sorted(size_groups.keys(), key=lambda x: int(x.split('x')[0]) * int(x.split('x')[1]), reverse=True):
        files = size_groups[size_key]
        print(f"\n{size_key} ({len(files)} files):")
        for filename, file_size in sorted(files):
            print(f"  - {filename} ({file_size/1024:.1f} KB)")
    
    print("\n" + "-" * 80)
    print(f"Total space in discarded folder: {total_size/1024/1024:.1f} MB")
    print(f"Total images: {len(images)}")
    
    # Find the most recent log file
    log_files = list(directory.glob("image_scan_*.log"))
    if log_files:
        most_recent = max(log_files, key=lambda x: x.stat().st_mtime)
        print(f"\nMost recent log file: {most_recent.name}")
        print("Review this log for detailed information about why images were moved.")
    
    print("\nTo recover all images: mv discarded/* .")
    print("To recover specific image: mv discarded/IMAGE_NAME .")
    print("To permanently delete: rm -rf discarded/")


def main():
    parser = argparse.ArgumentParser(
        description="Review images in the discarded folder",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory containing the discarded folder (default: current directory)"
    )
    
    args = parser.parse_args()
    
    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"Error: '{directory}' is not a valid directory")
        return 1
    
    review_discarded_folder(directory)
    return 0


if __name__ == "__main__":
    exit(main())
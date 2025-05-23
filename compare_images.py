#!/usr/bin/env python3
# /// script
# dependencies = [
#   "Pillow>=10.0.0",
#   "imagehash>=4.3.1",
#   "numpy>=1.24.0",
# ]
# ///
"""
Quick tool to compare two specific images and see their similarity scores.
Useful for testing threshold values and understanding false positives/negatives.

Usage:
    uv run compare_images.py <image1> <image2>
"""

import sys
from pathlib import Path
from PIL import Image
import imagehash
import numpy as np


def compare_two_images(img1_path: str, img2_path: str):
    """Compare two images and show detailed similarity analysis."""
    path1 = Path(img1_path)
    path2 = Path(img2_path)
    
    if not path1.exists() or not path2.exists():
        print("Error: One or both image files don't exist")
        return
    
    print(f"Comparing images:")
    print(f"  Image 1: {path1.name}")
    print(f"  Image 2: {path2.name}")
    print("-" * 60)
    
    try:
        # Load images
        with Image.open(path1) as img1, Image.open(path2) as img2:
            # Basic info
            print(f"\nImage dimensions:")
            print(f"  Image 1: {img1.size[0]}x{img1.size[1]} ({img1.size[0] * img1.size[1]:,} pixels)")
            print(f"  Image 2: {img2.size[0]}x{img2.size[1]} ({img2.size[0] * img2.size[1]:,} pixels)")
            
            # Aspect ratios
            ar1 = round(img1.size[0] / img1.size[1], 3)
            ar2 = round(img2.size[0] / img2.size[1], 3)
            print(f"\nAspect ratios:")
            print(f"  Image 1: {ar1}")
            print(f"  Image 2: {ar2}")
            print(f"  Difference: {abs(ar1 - ar2):.3f}")
            
            # Calculate all hash types
            print(f"\nHash differences (lower = more similar):")
            
            phash1 = imagehash.phash(img1)
            phash2 = imagehash.phash(img2)
            phash_diff = phash1 - phash2
            print(f"  Perceptual hash (pHash): {phash_diff}")
            
            dhash1 = imagehash.dhash(img1)
            dhash2 = imagehash.dhash(img2)
            dhash_diff = dhash1 - dhash2
            print(f"  Difference hash (dHash): {dhash_diff}")
            
            whash1 = imagehash.whash(img1)
            whash2 = imagehash.whash(img2)
            whash_diff = whash1 - whash2
            print(f"  Wavelet hash (wHash): {whash_diff}")
            
            ahash1 = imagehash.average_hash(img1)
            ahash2 = imagehash.average_hash(img2)
            ahash_diff = ahash1 - ahash2
            print(f"  Average hash (aHash): {ahash_diff}")
            
            # Convert to RGB for color comparison
            if img1.mode != 'RGB':
                img1 = img1.convert('RGB')
            if img2.mode != 'RGB':
                img2 = img2.convert('RGB')
            
            # Average colors
            arr1 = np.array(img1)
            arr2 = np.array(img2)
            avg_color1 = tuple(arr1.mean(axis=(0, 1)).astype(int))
            avg_color2 = tuple(arr2.mean(axis=(0, 1)).astype(int))
            color_diff = sum(abs(c1 - c2) for c1, c2 in zip(avg_color1, avg_color2))
            
            print(f"\nAverage colors (RGB):")
            print(f"  Image 1: {avg_color1}")
            print(f"  Image 2: {avg_color2}")
            print(f"  Difference: {color_diff} (max: 765)")
            
            # Recommendations
            print(f"\nAnalysis:")
            
            if phash_diff == 0 and dhash_diff == 0:
                print("  ✓ Images are nearly identical (exact duplicates)")
            elif phash_diff <= 5 and dhash_diff <= 5:
                print("  ✓ Images are very similar (likely same image, different quality)")
            elif phash_diff <= 10 and dhash_diff <= 15:
                if abs(ar1 - ar2) < 0.01:
                    print("  ✓ Images are similar with same aspect ratio (likely scaled versions)")
                else:
                    print("  ! Images are similar but different aspect ratios (possibly cropped)")
            elif phash_diff <= 15:
                print("  ~ Images have some similarity but significant differences")
            else:
                print("  ✗ Images are different")
            
            print(f"\nRecommended threshold settings:")
            print(f"  - For high confidence (few false positives): --threshold {min(phash_diff - 2, 5)}")
            print(f"  - For balanced detection: --threshold {phash_diff}")
            print(f"  - For aggressive detection (more false positives): --threshold {phash_diff + 5}")
            
    except Exception as e:
        print(f"Error comparing images: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: uv run compare_images.py <image1> <image2>")
        print("\nExample:")
        print("  uv run compare_images.py photo.jpg photo_small.jpg")
        sys.exit(1)
    
    compare_two_images(sys.argv[1], sys.argv[2])
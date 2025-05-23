#!/usr/bin/env python3
# /// script
# dependencies = [
#   "Pillow>=10.0.0",
#   "imagehash>=4.3.1",
#   "numpy>=1.24.0",
# ]
# ///
"""
Image Duplicate Scanner
Finds and moves duplicate or scaled-down versions of images to a 'discarded' folder.

Usage:
    uv run image_scanner.py [directory] [options]
"""

import os
import shutil
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from PIL import Image
import imagehash
import argparse
import numpy as np
from datetime import datetime
import warnings

# Suppress the specific PIL warning about palette images
warnings.filterwarnings("ignore", message="Palette images with Transparency expressed in bytes should be converted to RGBA images")


class ImageScanner:
    def __init__(self, directory: str, threshold: int = 10, dry_run: bool = False, 
                 interactive: bool = False):
        """
        Initialize the image scanner.
        
        Args:
            directory: Directory to scan for images
            threshold: Similarity threshold for perceptual hashing (lower = more similar)
            dry_run: If True, only show what would be done without moving files
            interactive: If True, ask for confirmation before moving scaled versions
        """
        self.directory = Path(directory)
        self.discarded_dir = self.directory / "discarded"
        self.threshold = threshold
        self.dry_run = dry_run
        self.interactive = interactive
        self.image_extensions = {'.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG'}
        
        # Create log file
        self.log_file = self.directory / f"image_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def setup_discarded_directory(self):
        """Create the discarded directory if it doesn't exist."""
        if not self.dry_run:
            self.discarded_dir.mkdir(exist_ok=True)
    
    def log(self, message: str, also_print: bool = True):
        """Log message to file and optionally print."""
        with open(self.log_file, 'a') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        if also_print:
            print(message)
        
    def get_file_hash(self, filepath: Path) -> str:
        """Calculate MD5 hash of a file for exact duplicate detection."""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_image_info(self, filepath: Path) -> Dict:
        """
        Get comprehensive image information including multiple hashes.
        
        Returns:
            Dict containing image metadata and hashes
        """
        with Image.open(filepath) as img:
            width, height = img.size
            mode = img.mode
            
            # Calculate multiple hash types for better accuracy
            phash = str(imagehash.phash(img))
            dhash = str(imagehash.dhash(img))
            whash = str(imagehash.whash(img))
            ahash = str(imagehash.average_hash(img))
            
            # Convert to RGB for consistent comparison
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate average color for basic similarity check
            img_array = np.array(img)
            avg_color = tuple(img_array.mean(axis=(0, 1)).astype(int))
        
        file_hash = self.get_file_hash(filepath)
        file_size = filepath.stat().st_size
        
        return {
            'width': width,
            'height': height,
            'aspect_ratio': round(width / height, 3),
            'mode': mode,
            'file_hash': file_hash,
            'file_size': file_size,
            'phash': phash,
            'dhash': dhash,
            'whash': whash,
            'ahash': ahash,
            'avg_color': avg_color,
            'pixels': width * height
        }
    
    def compare_images(self, info1: Dict, info2: Dict) -> Tuple[bool, float, str]:
        """
        Compare two images using multiple criteria.
        
        Returns:
            Tuple of (is_similar, confidence, reason)
        """
        # Check aspect ratio first - if different, not scaled versions
        if abs(info1['aspect_ratio'] - info2['aspect_ratio']) > 0.01:
            return False, 0.0, "Different aspect ratios"
        
        # Calculate hash differences
        phash_diff = imagehash.hex_to_hash(info1['phash']) - imagehash.hex_to_hash(info2['phash'])
        dhash_diff = imagehash.hex_to_hash(info1['dhash']) - imagehash.hex_to_hash(info2['dhash'])
        whash_diff = imagehash.hex_to_hash(info1['whash']) - imagehash.hex_to_hash(info2['whash'])
        ahash_diff = imagehash.hex_to_hash(info1['ahash']) - imagehash.hex_to_hash(info2['ahash'])
        
        # Calculate color difference
        color_diff = sum(abs(c1 - c2) for c1, c2 in zip(info1['avg_color'], info2['avg_color']))
        
        # Weighted scoring system (ensure scores are 0-1)
        # Lower hash difference = higher score
        phash_score = max(0, 1 - (phash_diff / 64))  # Max hash diff is 64
        dhash_score = max(0, 1 - (dhash_diff / 64))
        whash_score = max(0, 1 - (whash_diff / 64))
        ahash_score = max(0, 1 - (ahash_diff / 64))
        
        # Combine hash scores with weights
        hash_score = (
            phash_score * 0.4 +  # pHash is most reliable
            dhash_score * 0.3 +
            whash_score * 0.2 +
            ahash_score * 0.1
        )
        
        # Normalize color difference (0-1 scale, inverted so higher is more similar)
        color_score = max(0, 1.0 - (color_diff / 765.0))  # Max diff is 255*3
        
        # Combined confidence score (0-1)
        confidence = hash_score * 0.8 + color_score * 0.2
        
        # Decision criteria
        if phash_diff <= self.threshold and dhash_diff <= self.threshold * 1.5:
            if color_score > 0.7:  # Colors are reasonably similar
                reasons = []
                if phash_diff <= self.threshold // 2:
                    reasons.append("very similar perceptual hash")
                if dhash_diff <= self.threshold // 2:
                    reasons.append("very similar difference hash")
                if color_score > 0.9:
                    reasons.append("very similar colors")
                
                return True, confidence, f"Similar: {', '.join(reasons)}"
        
        return False, confidence, "Not similar enough"
    
    def ask_user_confirmation(self, img1: Path, img2: Path, info1: Dict, info2: Dict, 
                            confidence: float, reason: str) -> bool:
        """Ask user for confirmation before moving an image."""
        print(f"\n{'='*60}")
        print(f"Found potentially scaled versions (confidence: {confidence:.0%}):")
        print(f"  1. {img1.name} ({info1['width']}x{info1['height']}, {info1['file_size']/1024:.1f}KB)")
        print(f"  2. {img2.name} ({info2['width']}x{info2['height']}, {info2['file_size']/1024:.1f}KB)")
        print(f"  Reason: {reason}")
        
        smaller = img1 if info1['pixels'] < info2['pixels'] else img2
        print(f"\nWould move: {smaller.name} to discarded/")
        
        while True:
            response = input("Move this file? (y/n/s[kip all]/q[uit]): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            elif response in ['s', 'skip']:
                self.interactive = False
                return False
            elif response in ['q', 'quit']:
                print("Quitting...")
                exit(0)
    
    def find_all_images(self) -> List[Path]:
        """Find all image files in the directory."""
        images = []
        for ext in self.image_extensions:
            images.extend(self.directory.glob(f"*{ext}"))
        return [img for img in images if img.is_file() and img.parent != self.discarded_dir]
        """Find all image files in the directory."""
        images = []
        for ext in self.image_extensions:
            images.extend(self.directory.glob(f"*{ext}"))
        return [img for img in images if img.is_file() and img.parent != self.discarded_dir]
    
    def move_to_discarded(self, filepath: Path, reason: str):
        """Move a file to the discarded directory."""
        dest = self.discarded_dir / filepath.name
        
        # Handle filename conflicts
        if dest.exists():
            base = dest.stem
            ext = dest.suffix
            counter = 1
            while dest.exists():
                dest = self.discarded_dir / f"{base}_{counter}{ext}"
                counter += 1
        
        if self.dry_run:
            self.log(f"[DRY RUN] Would move: {filepath.name} -> discarded/ ({reason})")
        else:
            shutil.move(str(filepath), str(dest))
            self.log(f"Moved: {filepath.name} -> discarded/ ({reason})")
    
    def rename_with_dimensions(self, filepath: Path, width: int, height: int):
        """Rename a file to include dimensions in the filename."""
        base = filepath.stem
        ext = filepath.suffix
        
        # Remove existing dimension suffix if present (e.g., "-1200x800")
        base = re.sub(r'-\d+x\d+$', '', base)
        
        new_name = f"{base}-{width}x{height}{ext}"
        new_path = filepath.parent / new_name
        
        # Handle filename conflicts
        if new_path.exists() and new_path != filepath:
            counter = 1
            while new_path.exists():
                new_name = f"{base}-{width}x{height}_{counter}{ext}"
                new_path = filepath.parent / new_name
                counter += 1
        
        if new_path != filepath:  # Only rename if the name is actually different
            if self.dry_run:
                self.log(f"[DRY RUN] Would rename: {filepath.name} -> {new_name}")
            else:
                filepath.rename(new_path)
                self.log(f"Renamed: {filepath.name} -> {new_name}")
                return new_path
        
        return filepath
    
    def scan_for_duplicates(self):
        """Main scanning logic to find duplicates and scaled versions."""
        self.log(f"Starting scan of directory: {self.directory}")
        if self.dry_run:
            self.log("[DRY RUN MODE - No files will be moved]")
        
        self.setup_discarded_directory()
        
        images = self.find_all_images()
        if not images:
            self.log("No images found in the directory.")
            return
        
        self.log(f"Found {len(images)} images to process...")
        
        # Store image information
        image_data: Dict[Path, Dict] = {}
        file_hash_map: Dict[str, List[Path]] = {}
        
        # First pass: collect all image data
        self.log("\nAnalyzing images...")
        for img_path in images:
            try:
                info = self.get_image_info(img_path)
                image_data[img_path] = info
                
                # Group by file hash for exact duplicates
                if info['file_hash'] not in file_hash_map:
                    file_hash_map[info['file_hash']] = []
                file_hash_map[info['file_hash']].append(img_path)
                
            except Exception as e:
                self.log(f"Error processing {img_path.name}: {e}")
        
        # Second pass: find exact duplicates
        self.log("\nChecking for exact duplicates...")
        processed_hashes: Set[str] = set()
        
        for file_hash, paths in file_hash_map.items():
            if len(paths) > 1 and file_hash not in processed_hashes:
                processed_hashes.add(file_hash)
                # Keep the first one, move the rest
                self.log(f"\nFound {len(paths)} identical images:")
                for path in paths:
                    self.log(f"  - {path.name}", also_print=False)
                
                # Rename the kept image (first one) to include dimensions
                kept_image = paths[0]
                kept_info = image_data[kept_image]
                new_kept_path = self.rename_with_dimensions(kept_image, kept_info['width'], kept_info['height'])
                
                # Update image_data with new path if it changed
                if new_kept_path != kept_image:
                    image_data[new_kept_path] = image_data.pop(kept_image)
                
                for path in paths[1:]:
                    self.move_to_discarded(path, "exact duplicate")
                    # Remove from image_data to avoid processing again
                    del image_data[path]
        
        # Third pass: find scaled versions
        self.log("\nChecking for scaled versions...")
        remaining_images = list(image_data.keys())
        moved_images: Set[Path] = set()
        comparisons_made = 0
        similar_found = 0
        
        for i, img1 in enumerate(remaining_images):
            if img1 in moved_images:
                continue
                
            info1 = image_data[img1]
            
            for img2 in remaining_images[i+1:]:
                if img2 in moved_images:
                    continue
                    
                info2 = image_data[img2]
                comparisons_made += 1
                
                # Check if images are similar
                is_similar, confidence, reason = self.compare_images(info1, info2)
                
                if is_similar and info1['pixels'] != info2['pixels']:
                    similar_found += 1
                    
                    # Determine which is smaller
                    if info1['pixels'] < info2['pixels']:
                        smaller, larger = img1, img2
                        smaller_info, larger_info = info1, info2
                    else:
                        smaller, larger = img2, img1
                        smaller_info, larger_info = info2, info1
                    
                    self.log(f"\nFound scaled versions (confidence: {confidence:.0%}):")
                    self.log(f"  - {larger.name} ({larger_info['width']}x{larger_info['height']})")
                    self.log(f"  - {smaller.name} ({smaller_info['width']}x{smaller_info['height']})")
                    self.log(f"  {reason}")
                    
                    # Ask for confirmation if in interactive mode
                    should_move = True
                    if self.interactive:
                        should_move = self.ask_user_confirmation(
                            img1, img2, info1, info2, confidence, reason
                        )
                    
                    if should_move:
                        self.move_to_discarded(smaller, f"smaller version of {larger.name}")
                        # Rename the kept (larger) image to include dimensions
                        new_larger_path = self.rename_with_dimensions(larger, larger_info['width'], larger_info['height'])
                        
                        # Update image_data with new path if it changed
                        if new_larger_path != larger:
                            image_data[new_larger_path] = image_data.pop(larger)
                            # Update the remaining_images list for future iterations
                            if larger in remaining_images:
                                idx = remaining_images.index(larger)
                                remaining_images[idx] = new_larger_path
                        
                        moved_images.add(smaller)
                        break
                    else:
                        self.log("  Skipped by user")
        
        self.log(f"\nScan complete! Made {comparisons_made} comparisons, found {similar_found} similar pairs.")
        
        # Summary
        if not self.dry_run:
            discarded_count = len(list(self.discarded_dir.glob("*")))
            remaining_count = len(self.find_all_images())
        else:
            discarded_count = "N/A (dry run)"
            remaining_count = "N/A (dry run)"
            
        self.log(f"\nSummary:")
        self.log(f"  - Images moved to discarded: {discarded_count}")
        self.log(f"  - Images remaining: {remaining_count}")
        self.log(f"  - Log file: {self.log_file.name}")


def main():
    parser = argparse.ArgumentParser(
        description="Scan directory for duplicate and scaled images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan current directory with default settings
  uv run image_scanner.py
  
  # Scan specific directory
  uv run image_scanner.py /path/to/images
  
  # Dry run - see what would be moved without actually moving
  uv run image_scanner.py --dry-run
  
  # Interactive mode - confirm each scaled version
  uv run image_scanner.py --interactive
  
  # Adjust similarity threshold (lower = more strict)
  uv run image_scanner.py --threshold 5
  
  # Combine options
  uv run image_scanner.py ~/Pictures --threshold 8 --interactive --dry-run
        """
    )
    
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)"
    )
    
    parser.add_argument(
        "--threshold",
        type=int,
        default=10,
        help="Similarity threshold for perceptual hashing (default: 10, lower = more similar)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be moved without actually moving files"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Ask for confirmation before moving scaled versions"
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory")
        return 1
    
    # Run scanner
    scanner = ImageScanner(
        args.directory, 
        threshold=args.threshold,
        dry_run=args.dry_run,
        interactive=args.interactive
    )
    scanner.scan_for_duplicates()
    
    return 0


if __name__ == "__main__":
    exit(main())
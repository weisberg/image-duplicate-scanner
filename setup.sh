#!/bin/bash

# Setup script for Image Scanner with uv

echo "Setting up Image Scanner..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install it first:"
    echo ""
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "Or on macOS with Homebrew:"
    echo ""
    echo "  brew install uv"
    echo ""
    exit 1
fi

# Make scripts executable
chmod +x image_scanner.py
chmod +x compare_images.py
chmod +x review_discarded.py

echo ""
echo "✅ Setup complete! The scripts are ready to use."
echo ""
echo "Usage:"
echo "------"
echo ""
echo "1. Run the scanner:"
echo "   uv run image_scanner.py [directory] [options]"
echo ""
echo "   Options:"
echo "   --dry-run         Preview what would be moved without actually moving"
echo "   --interactive     Confirm each scaled version before moving"
echo "   --threshold N     Set similarity threshold (default: 10, lower = stricter)"
echo ""
echo "2. Compare two specific images:"
echo "   uv run compare_images.py image1.jpg image2.jpg"
echo ""
echo "3. Review what was moved to discarded:"
echo "   uv run review_discarded.py [directory]"
echo ""
echo "Examples:"
echo "---------"
echo "  uv run image_scanner.py                         # Scan current directory"
echo "  uv run image_scanner.py ~/Pictures --dry-run    # Preview changes"
echo "  uv run image_scanner.py --interactive           # Confirm each move"
echo "  uv run image_scanner.py --threshold 5           # Strict matching"
echo ""
echo "Tips:"
echo "-----"
echo "  - Start with --dry-run to preview what would be moved"
echo "  - Use --interactive if you're unsure about the threshold"
echo "  - Check the log file for detailed information"
echo "  - Use compare_images.py to test specific image pairs"
echo ""
echo "Note: uv will automatically install dependencies on first run!"
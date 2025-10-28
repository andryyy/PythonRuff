#!/bin/bash
# Build PythonRuff.sublime-package

PACKAGE_NAME="PythonRuff"
BUILD_DIR="build"
OUTPUT_FILE="${PACKAGE_NAME}.sublime-package"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Building ${PACKAGE_NAME}..."

# Clean up old build
rm -rf "$BUILD_DIR"
rm -f "$OUTPUT_FILE"

# Create build directory
mkdir -p "$BUILD_DIR"

# Copy files to build directory
echo "Copying files..."
cp python_ruff.py "$BUILD_DIR/"
cp PythonRuff.sublime-settings "$BUILD_DIR/"
cp PythonRuff.sublime-commands "$BUILD_DIR/"
cp Default.sublime-keymap "$BUILD_DIR/"
cp Main.sublime-menu "$BUILD_DIR/"
cp Context.sublime-menu "$BUILD_DIR/"
cp README.md "$BUILD_DIR/"

# Create the .sublime-package file (it's just a zip file)
echo "Creating package..."
cd "$BUILD_DIR"
zip -r "../$OUTPUT_FILE" * >/dev/null

cd ..
rm -rf "$BUILD_DIR"

echo "Done! Created ${OUTPUT_FILE}"
echo ""
echo "To install:"
echo "1. Copy ${OUTPUT_FILE} to your Sublime Text Packages directory:"
echo "   - Linux: ~/.config/sublime-text/Installed Packages/"
echo "   - macOS: ~/Library/Application Support/Sublime Text/Installed Packages/"
echo "   - Windows: %APPDATA%\\Sublime Text\\Installed Packages\\"
echo ""
echo "2. Restart Sublime Text"

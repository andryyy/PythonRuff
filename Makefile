.PHONY: build clean install

PACKAGE_NAME = PythonRuff
PACKAGE_FILE = $(PACKAGE_NAME).sublime-package

build:
	@echo "Building $(PACKAGE_NAME)..."
	@./build.sh

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/
	@rm -f $(PACKAGE_FILE)
	@rm -rf __pycache__/
	@find . -name "*.pyc" -delete
	@echo "Done."

install: build
	@echo "Installing $(PACKAGE_FILE)..."
	@mkdir -p ~/.config/sublime-text/Installed\ Packages/
	@cp $(PACKAGE_FILE) ~/.config/sublime-text/Installed\ Packages/
	@echo "Done. Restart Sublime Text to activate."

help:
	@echo "PythonRuff Build Commands:"
	@echo "  make build   - Build the .sublime-package file"
	@echo "  make clean   - Remove build artifacts"
	@echo "  make install - Build and install to Sublime Text"
	@echo "  make help    - Show this help message"

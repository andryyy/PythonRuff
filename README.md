# PythonRuff

Format and lint Python code using Ruff in Sublime Text.

## Features

- **Format Python code** with `ruff format`
- **Comprehensive Linting** with `ruff check`:
  - Squiggly underlines on errors/warnings (color-coded by severity)
  - Colored gutter dots (red for errors, yellow for warnings, blue for info)
  - Errors visible in minimap
  - Hover tooltips showing error details with links to documentation
  - Clickable errors in output panel
  - Navigate between errors with F4/Shift+F4
- **Auto-fix issues** with `ruff check --fix`
- Format/lint/fix on save (configurable)
- Respects `ruff.toml`, `.ruff.toml`, and `pyproject.toml` configuration files
- Works with ruff installed globally or in virtual environments

## Installation

### Option 1: Install from .sublime-package

1. Download `PythonRuff.sublime-package`
2. Copy it to your Sublime Text `Installed Packages` directory:
   - **Linux**: `~/.config/sublime-text/Installed Packages/`
   - **macOS**: `~/Library/Application Support/Sublime Text/Installed Packages/`
   - **Windows**: `%APPDATA%\Sublime Text\Installed Packages\`
3. Restart Sublime Text
4. Install Ruff:
   ```bash
   uv tool install ruff
   ```

### Option 2: Install from Source

1. Clone or copy the plugin files to your Sublime Text `Packages` directory:
   - **Linux**: `~/.config/sublime-text/Packages/PythonRuff/`
   - **macOS**: `~/Library/Application Support/Sublime Text/Packages/PythonRuff/`
   - **Windows**: `%APPDATA%\Sublime Text\Packages\PythonRuff\`
2. Restart Sublime Text
3. Install Ruff:
   ```bash
   uv tool install ruff
   ```

## Building from Source

To build the `.sublime-package` file:

### Using the build script:
```bash
cd /path/to/PythonRuff
./build.sh
```

### Using Make:
```bash
cd /path/to/PythonRuff
make build          # Build the package
make install        # Build and install to Sublime Text
make clean          # Remove build artifacts
```

This creates `PythonRuff.sublime-package` (9.8KB) which you can distribute or install.

## Usage

### Commands

Access these via Command Palette (Ctrl+Shift+P / Cmd+Shift+P):

- **PythonRuff: Format File** - Format the entire file
- **PythonRuff: Format Selection** - Format only the selected code
- **PythonRuff: Lint File** - Check for linting issues (shows inline errors)
- **PythonRuff: Fix Issues** - Auto-fix linting issues
- **PythonRuff: Clear Lint Markers** - Remove lint error markers from view
- **PythonRuff: Next Error** - Navigate to next error
- **PythonRuff: Previous Error** - Navigate to previous error
- **PythonRuff: Check Installation** - Verify Ruff is installed
- **PythonRuff: Toggle Format on Save** - Enable/disable auto-formatting
- **PythonRuff: Toggle Lint on Save** - Enable/disable auto-linting
- **PythonRuff: Toggle Fix on Save** - Enable/disable auto-fixing

### Keyboard Shortcuts

- **Ctrl+Shift+F** - Format file
- **Ctrl+Shift+L** - Lint file
- **F4** - Jump to next error
- **Shift+F4** - Jump to previous error

### Context Menu

Right-click in a Python file to access:
- Format
- Lint (shows inline error markers with hover tooltips)
- Fix Issues
- Clear Lint Markers

### Linting Features

When you run **Lint File**, you'll see:
- **Colored underlines**: Red for errors, yellow for warnings, blue for info
- **Gutter dots**: Visual indicators in the left margin
- **Minimap markers**: Errors shown on the minimap/scrollbar
- **Hover tooltips**: Hover over any error to see detailed information
- **Output panel**: All errors listed with clickable line numbers
- **Error navigation**: Use F4/Shift+F4 to jump between errors

## Configuration

Go to **Preferences → Package Settings → PythonRuff → Settings**

Available settings:

```json
{
    // Path to ruff binary (default: "ruff")
    "ruff_binary": "ruff",

    // Format file on save
    "format_on_save": false,

    // Run auto-fixes on save
    "fix_on_save": false,

    // Run linter on save
    "lint_on_save": false,

    // Use config files (ruff.toml, pyproject.toml)
    "use_config_file": true,

    // Timeout in seconds
    "timeout": 10,

    // Line length (if no config file)
    "line_length": null
}
```

### Using a Virtual Environment

Set the `ruff_binary` path to your virtual environment:

```json
{
    "ruff_binary": "/path/to/venv/bin/ruff"
}
```

### Project-Specific Settings

Add to your `.sublime-project` file:

```json
{
    "settings": {
        "python_ruff": {
            "format_on_save": true,
            "lint_on_save": true
        }
    }
}
```

## About Ruff

Ruff is an extremely fast Python linter and formatter written in Rust. It combines the functionality of many tools (Flake8, isort, Black, etc.) into one fast tool.

Learn more at: https://docs.astral.sh/ruff/

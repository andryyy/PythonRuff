"""
PythonRuff - Format and Lint Python code using Ruff from PATH
"""

import sublime
import sublime_plugin
import subprocess
import os
import tempfile
import json

print("PythonRuff: Plugin loaded successfully")


def find_ruff_binary(settings):
    """Find the ruff binary from settings or PATH."""
    ruff_binary = settings.get("ruff_binary", "ruff")
    print("PythonRuff: Looking for ruff binary: {}".format(ruff_binary))
    print("PythonRuff: Is absolute path: {}".format(os.path.isabs(ruff_binary)))

    # If it's an absolute path, use it directly
    if os.path.isabs(ruff_binary):
        if os.path.isfile(ruff_binary) and os.access(ruff_binary, os.X_OK):
            print("PythonRuff: Found ruff at: {}".format(ruff_binary))
            return ruff_binary
        else:
            raise FileNotFoundError("Ruff binary not found at: {}".format(ruff_binary))

    # Otherwise, try to find it in PATH
    import shutil
    print("PythonRuff: Searching PATH for: {}".format(ruff_binary))
    print("PythonRuff: PATH = {}".format(os.environ.get('PATH', 'NOT SET')))
    binary_path = shutil.which(ruff_binary)
    print("PythonRuff: shutil.which() returned: {}".format(binary_path))
    if binary_path:
        print("PythonRuff: Found ruff at: {}".format(binary_path))
        return binary_path

    raise FileNotFoundError("Ruff not found in PATH. Please install ruff or configure 'ruff_binary' in settings.")


def get_ruff_config_file(filepath):
    """Find pyproject.toml or ruff.toml config file."""
    if not filepath:
        return None

    # Get the absolute path and start from the file's directory
    path = os.path.abspath(filepath)
    current_dir = os.path.dirname(path)

    # Walk up the directory tree looking for config files
    while True:
        for config_name in ["ruff.toml", ".ruff.toml", "pyproject.toml"]:
            config_file = os.path.join(current_dir, config_name)
            if os.path.isfile(config_file):
                return config_file

        # Move to parent directory
        parent_dir = os.path.dirname(current_dir)

        # Stop if we've reached the root
        if parent_dir == current_dir:
            break

        current_dir = parent_dir

    return None


class PythonRuffFormatCommand(sublime_plugin.TextCommand):
    """Format Python code with Ruff."""

    def is_visible(self):
        """Only show for Python files."""
        return self.view.match_selector(0, "source.python")

    def run(self, edit, use_selection=True):
        """Execute Ruff formatting."""
        print("PythonRuff: Format command running (use_selection={})".format(use_selection))
        settings = sublime.load_settings("PythonRuff.sublime-settings")

        # Check if it's a Python file
        if not self.view.match_selector(0, "source.python"):
            sublime.status_message("PythonRuff: Not a Python file")
            return

        # Get the ruff binary
        try:
            ruff_binary = find_ruff_binary(settings)
        except FileNotFoundError as e:
            sublime.error_message(str(e))
            return

        # Get the code to format
        region = self.view.sel()[0]
        if region.empty() or not use_selection:
            # Format entire file
            region = sublime.Region(0, self.view.size())

        code = self.view.substr(region)
        filepath = self.view.file_name()

        # Build ruff command
        cmd = [ruff_binary, "format"]

        # Add line length if specified
        line_length = settings.get("line_length")
        if line_length:
            cmd.extend(["--line-length", str(line_length)])

        # Add config file if found
        config_file = get_ruff_config_file(filepath)
        if config_file and settings.get("use_config_file", True):
            cmd.extend(["--config", config_file])

        # Format stdin/stdout
        cmd.append("-")

        # Get working directory
        if filepath:
            cwd = os.path.dirname(filepath)
        else:
            folders = self.view.window().folders()
            cwd = folders[0] if folders else None

        print("PythonRuff Format: Running command: {}".format(" ".join(cmd)))
        print("PythonRuff Format: Working directory: {}".format(cwd))

        # Run ruff
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd
            )

            stdout, stderr = proc.communicate(input=code.encode("utf-8"), timeout=settings.get("timeout", 10))

            if proc.returncode == 0:
                formatted_code = stdout.decode("utf-8")

                # Check if code changed
                if formatted_code != code:
                    self.view.replace(edit, region, formatted_code)
                    sublime.status_message("PythonRuff: Formatted successfully")
                else:
                    sublime.status_message("PythonRuff: Already formatted")
            else:
                error_msg = stderr.decode("utf-8")
                print("PythonRuff Error: {}".format(error_msg))
                sublime.status_message("PythonRuff: Formatting failed - {}".format(error_msg.splitlines()[0] if error_msg else 'Unknown error'))

        except subprocess.TimeoutExpired:
            sublime.error_message("PythonRuff: Ruff execution timed out")
        except Exception as e:
            sublime.error_message("PythonRuff: {}".format(str(e)))


class PythonRuffLintCommand(sublime_plugin.TextCommand):
    """Lint Python code with Ruff."""

    def is_visible(self):
        """Only show for Python files."""
        return self.view.match_selector(0, "source.python")

    def run(self, edit):
        """Execute Ruff linting."""
        print("PythonRuff: Lint command running")
        settings = sublime.load_settings("PythonRuff.sublime-settings")

        # Check if it's a Python file
        if not self.view.match_selector(0, "source.python"):
            sublime.status_message("PythonRuff: Not a Python file")
            return

        # Get the ruff binary
        try:
            ruff_binary = find_ruff_binary(settings)
        except FileNotFoundError as e:
            sublime.error_message(str(e))
            return

        # Clear any existing markers before running lint
        self.view.erase_regions("ruff_errors")
        self.view.erase_regions("ruff_warnings")
        self.view.erase_regions("ruff_info")

        filepath = self.view.file_name()

        # Build ruff command for linting
        cmd = [ruff_binary, "check"]

        # Add config file if found
        config_file = get_ruff_config_file(filepath)
        if config_file and settings.get("use_config_file", True):
            cmd.extend(["--config", config_file])

        # Use JSON output format for easier parsing
        cmd.extend(["--output-format", "json"])

        # If we have a saved file, lint that
        if filepath:
            cmd.append(filepath)
            cwd = os.path.dirname(filepath)
        else:
            # For unsaved files, use stdin
            cmd.extend(["--stdin-filename", "stdin.py"])
            cmd.append("-")
            folders = self.view.window().folders()
            cwd = folders[0] if folders else None

        print("PythonRuff: Running command: {}".format(" ".join(cmd)))
        print("PythonRuff: Working directory: {}".format(cwd))

        # Run ruff
        try:
            if filepath:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=cwd
                )
                stdout, stderr = proc.communicate(timeout=settings.get("timeout", 10))
            else:
                # For unsaved files, pass content via stdin
                code = self.view.substr(sublime.Region(0, self.view.size()))
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=cwd
                )
                stdout, stderr = proc.communicate(input=code.encode("utf-8"), timeout=settings.get("timeout", 10))

            output = stdout.decode("utf-8")
            error_output = stderr.decode("utf-8")

            # Ruff check returns 0 if no issues, 1 if issues found
            if proc.returncode == 0:
                # Clear any existing error markers (already cleared at start, but do it again for safety)
                self.view.erase_regions("ruff_errors")
                self.view.erase_regions("ruff_warnings")
                self.view.erase_regions("ruff_info")
                self.view.settings().erase("ruff_diagnostics")
                sublime.status_message("PythonRuff: No issues found")
            elif proc.returncode == 1:
                # Parse JSON output
                try:
                    diagnostics = json.loads(output) if output else []
                    self._show_diagnostics(diagnostics)
                except (ValueError, AttributeError) as e:
                    print("PythonRuff: Failed to parse JSON output: {}".format(e))
                    print("PythonRuff: Raw output was: {}".format(output))
                    sublime.error_message("PythonRuff: Failed to parse linter output")
            else:
                error_msg = error_output if error_output else output
                print("PythonRuff Lint Error: {}".format(error_msg))
                sublime.error_message("PythonRuff Lint failed:\n{}".format(error_msg))

        except subprocess.TimeoutExpired:
            sublime.error_message("PythonRuff: Ruff execution timed out")
        except Exception as e:
            sublime.error_message("PythonRuff: {}".format(str(e)))

    def _show_diagnostics(self, diagnostics):
        """Show diagnostics using Sublime's region API."""
        error_regions = []
        warning_regions = []
        info_regions = []
        all_diagnostics = []

        for diag in diagnostics:
            # Get location info
            location = diag.get("location", {})
            row = location.get("row", 1)
            column = location.get("column", 1)

            # Convert to 0-based indexing
            line = row - 1
            col = column - 1

            # Get the point in the buffer
            point = self.view.text_point(line, col)

            # Get end location if available
            end_location = diag.get("end_location", {})
            if end_location:
                end_row = end_location.get("row", row)
                end_col = end_location.get("column", column)
                end_point = self.view.text_point(end_row - 1, end_col - 1)
            else:
                # Highlight the word at the point
                word_region = self.view.word(point)
                if word_region.empty():
                    # If no word, highlight the whole line
                    end_point = self.view.line(point).end()
                else:
                    end_point = word_region.end()

            region = sublime.Region(point, end_point)

            # Get diagnostic info
            code = diag.get("code", "")
            message = diag.get("message", "")
            url = diag.get("url", "")

            # Determine severity based on error code
            severity = self._get_severity(code)

            # Store diagnostic info for hover (serialize region as dict)
            all_diagnostics.append({
                "region": {"a": region.a, "b": region.b},
                "code": code,
                "message": message,
                "url": url,
                "severity": severity,
                "row": row,
                "col": column
            })

            # Categorize by severity
            if severity == "error":
                error_regions.append(region)
            elif severity == "warning":
                warning_regions.append(region)
            else:
                info_regions.append(region)

        # Store diagnostics for hover functionality
        self.view.settings().set("ruff_diagnostics", all_diagnostics)

        # Add regions to the view with proper flags for minimap and gutter
        flags = (
            sublime.DRAW_NO_FILL |
            sublime.DRAW_NO_OUTLINE |
            sublime.DRAW_SQUIGGLY_UNDERLINE |
            sublime.DRAW_NO_FILL
        )

        if error_regions:
            self.view.add_regions(
                "ruff_errors",
                error_regions,
                "region.redish markup.error",
                "dot",
                flags
            )

        if warning_regions:
            self.view.add_regions(
                "ruff_warnings",
                warning_regions,
                "region.yellowish markup.warning",
                "dot",
                flags
            )

        if info_regions:
            self.view.add_regions(
                "ruff_info",
                info_regions,
                "region.bluish markup.info",
                "dot",
                flags
            )

        # Show summary
        total_issues = len(error_regions) + len(warning_regions) + len(info_regions)
        sublime.status_message("PythonRuff: Found {} issue(s)".format(total_issues))

        # Show in exec panel (standard build output panel)
        self._show_in_exec_panel(all_diagnostics)

    def _get_severity(self, code):
        """Determine severity based on ruff error code."""
        if not code:
            return "error"

        # Error codes that are errors
        error_prefixes = ["E", "F"]
        # Warning codes
        warning_prefixes = ["W", "N", "D", "UP", "ANN", "S", "B", "A", "C", "DTZ", "T", "EM", "EXE", "ISC", "ICN", "G", "INP", "PIE", "PYI", "PT", "Q", "RSE", "RET", "SLF", "SLOT", "SIM", "TID", "TCH", "INT", "ARG", "PTH", "TD", "FIX", "ERA", "PD", "PGH", "PL", "TRY", "FLY", "NPY", "AIR", "PERF", "FURB", "LOG", "RUF"]

        first_char = code[0] if code else ""

        if first_char in error_prefixes:
            return "error"
        elif any(code.startswith(prefix) for prefix in warning_prefixes):
            return "warning"
        else:
            return "info"

    def _show_in_exec_panel(self, diagnostics):
        """Show diagnostics in the exec output panel."""
        if not diagnostics:
            return

        window = self.view.window()
        output_view = window.create_output_panel("exec")

        # Format output with clickable file references
        filepath = self.view.file_name() or "stdin.py"
        lines = []

        for diag in diagnostics:
            # Format: filepath:line:col: message [code]
            line = "{}:{}:{}: {} [{}]".format(
                filepath,
                diag["row"],
                diag["col"],
                diag["message"],
                diag["code"]
            )
            lines.append(line)

        output_text = "\n".join(lines)

        output_view.settings().set("result_file_regex", r"^(.+):(\d+):(\d+): (.+)$")
        output_view.settings().set("result_line_regex", r"^\s+(\d+)")
        output_view.settings().set("word_wrap", False)
        output_view.settings().set("line_numbers", False)
        output_view.settings().set("gutter", False)
        output_view.settings().set("scroll_past_end", False)

        output_view.run_command("select_all")
        output_view.run_command("right_delete")
        output_view.run_command("append", {"characters": output_text})

        window.run_command("show_panel", {"panel": "output.exec"})


class PythonRuffFixCommand(sublime_plugin.TextCommand):
    """Fix Python code issues with Ruff."""

    def is_visible(self):
        """Only show for Python files."""
        return self.view.match_selector(0, "source.python")

    def run(self, edit):
        """Execute Ruff fix."""
        print("PythonRuff: Fix command running")
        settings = sublime.load_settings("PythonRuff.sublime-settings")

        # Check if it's a Python file
        if not self.view.match_selector(0, "source.python"):
            sublime.status_message("PythonRuff: Not a Python file")
            return

        # Get the ruff binary
        try:
            ruff_binary = find_ruff_binary(settings)
        except FileNotFoundError as e:
            sublime.error_message(str(e))
            return

        code = self.view.substr(sublime.Region(0, self.view.size()))
        filepath = self.view.file_name()

        # Build ruff command for fixing
        cmd = [ruff_binary, "check", "--fix"]

        # Add config file if found
        config_file = get_ruff_config_file(filepath)
        if config_file and settings.get("use_config_file", True):
            cmd.extend(["--config", config_file])

        # Use stdin/stdout for fixes
        if filepath:
            cmd.extend(["--stdin-filename", filepath])
        else:
            cmd.extend(["--stdin-filename", "stdin.py"])
        cmd.append("-")

        # Get working directory
        if filepath:
            cwd = os.path.dirname(filepath)
        else:
            folders = self.view.window().folders()
            cwd = folders[0] if folders else None

        # Run ruff
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd
            )

            stdout, stderr = proc.communicate(input=code.encode("utf-8"), timeout=settings.get("timeout", 10))

            if proc.returncode == 0 or proc.returncode == 1:
                fixed_code = stdout.decode("utf-8")

                # Check if code changed
                if fixed_code and fixed_code != code:
                    region = sublime.Region(0, self.view.size())
                    self.view.replace(edit, region, fixed_code)
                    sublime.status_message("PythonRuff: Fixed issues successfully")
                else:
                    sublime.status_message("PythonRuff: No fixable issues found")
            else:
                error_msg = stderr.decode("utf-8")
                print("PythonRuff Fix Error: {}".format(error_msg))
                sublime.status_message("PythonRuff: Fix failed - {}".format(error_msg.splitlines()[0] if error_msg else 'Unknown error'))

        except subprocess.TimeoutExpired:
            sublime.error_message("PythonRuff: Ruff execution timed out")
        except Exception as e:
            sublime.error_message("PythonRuff: {}".format(str(e)))


class PythonRuffClearLintCommand(sublime_plugin.TextCommand):
    """Clear lint markers from the view."""

    def is_visible(self):
        """Only show for Python files."""
        return self.view.match_selector(0, "source.python")

    def run(self, edit):
        """Clear all lint markers."""
        self.view.erase_regions("ruff_errors")
        self.view.erase_regions("ruff_warnings")
        self.view.erase_regions("ruff_info")
        self.view.settings().erase("ruff_diagnostics")
        sublime.status_message("PythonRuff: Cleared lint markers")


class PythonRuffNextErrorCommand(sublime_plugin.TextCommand):
    """Navigate to next error."""

    def is_visible(self):
        """Only show for Python files."""
        return self.view.match_selector(0, "source.python")

    def run(self, edit):
        """Jump to the next error."""
        diagnostics = self.view.settings().get("ruff_diagnostics", [])
        if not diagnostics:
            sublime.status_message("PythonRuff: No errors found")
            return

        # Get current cursor position
        current_pos = self.view.sel()[0].begin()

        # Find next error after current position
        next_diag = None
        for diag in diagnostics:
            region = diag["region"]
            if isinstance(region, dict):
                region = sublime.Region(region["a"], region["b"])

            if region.begin() > current_pos:
                next_diag = diag
                break

        # If no error found after cursor, wrap to first error
        if not next_diag and diagnostics:
            next_diag = diagnostics[0]

        if next_diag:
            region = next_diag["region"]
            if isinstance(region, dict):
                region = sublime.Region(region["a"], region["b"])

            # Move cursor to error
            self.view.sel().clear()
            self.view.sel().add(region)
            self.view.show(region, show_surrounds=True)

            # Show message
            sublime.status_message("PythonRuff: {} [{}]".format(
                next_diag["message"], next_diag["code"]))


class PythonRuffPreviousErrorCommand(sublime_plugin.TextCommand):
    """Navigate to previous error."""

    def is_visible(self):
        """Only show for Python files."""
        return self.view.match_selector(0, "source.python")

    def run(self, edit):
        """Jump to the previous error."""
        diagnostics = self.view.settings().get("ruff_diagnostics", [])
        if not diagnostics:
            sublime.status_message("PythonRuff: No errors found")
            return

        # Get current cursor position
        current_pos = self.view.sel()[0].begin()

        # Find previous error before current position
        prev_diag = None
        for diag in reversed(diagnostics):
            region = diag["region"]
            if isinstance(region, dict):
                region = sublime.Region(region["a"], region["b"])

            if region.begin() < current_pos:
                prev_diag = diag
                break

        # If no error found before cursor, wrap to last error
        if not prev_diag and diagnostics:
            prev_diag = diagnostics[-1]

        if prev_diag:
            region = prev_diag["region"]
            if isinstance(region, dict):
                region = sublime.Region(region["a"], region["b"])

            # Move cursor to error
            self.view.sel().clear()
            self.view.sel().add(region)
            self.view.show(region, show_surrounds=True)

            # Show message
            sublime.status_message("PythonRuff: {} [{}]".format(
                prev_diag["message"], prev_diag["code"]))


class PythonRuffEventListener(sublime_plugin.EventListener):
    """Event listener for format/lint on save and hover."""

    def on_hover(self, view, point, hover_zone):
        """Show error details on hover."""
        if hover_zone != sublime.HOVER_TEXT:
            return

        if not view.match_selector(point, "source.python"):
            return

        # Get stored diagnostics
        diagnostics = view.settings().get("ruff_diagnostics", [])
        if not diagnostics:
            return

        # Find diagnostic at hover point
        hover_diagnostics = []
        for diag in diagnostics:
            # Check if point is in region (need to recreate region from stored data)
            region = diag["region"]
            if isinstance(region, dict):
                # Region was serialized, recreate it
                region = sublime.Region(region["a"], region["b"])

            if region.contains(point):
                hover_diagnostics.append(diag)

        if not hover_diagnostics:
            return

        # Format hover content
        html_parts = ['<div style="padding: 8px;">']

        for diag in hover_diagnostics:
            severity = diag["severity"]
            severity_color = {
                "error": "#ff3333",
                "warning": "#ffaa00",
                "info": "#3399ff"
            }.get(severity, "#ffffff")

            html_parts.append('<div style="margin-bottom: 8px;">')
            html_parts.append('<span style="color: {}; font-weight: bold;">[{}]</span> '.format(
                severity_color, diag["code"]))
            html_parts.append('<span>{}</span>'.format(diag["message"]))

            if diag.get("url"):
                html_parts.append('<br><a href="{}">View documentation</a>'.format(diag["url"]))

            html_parts.append('</div>')

        html_parts.append('</div>')

        html = ''.join(html_parts)

        view.show_popup(
            html,
            sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            point,
            max_width=800,
            max_height=400,
            on_navigate=lambda href: sublime.run_command("open_url", {"url": href})
        )

    def on_modified_async(self, view):
        """Clear lint markers when the user modifies the file."""
        if not view.match_selector(0, "source.python"):
            return

        # Clear markers on modification so they don't get stale
        # You can disable this by commenting out the next lines if you prefer
        # view.erase_regions("ruff_errors")
        # view.erase_regions("ruff_warnings")
        # view.erase_regions("ruff_info")
        # view.settings().erase("ruff_diagnostics")

    def on_pre_save(self, view):
        """Format/lint on save if enabled."""
        print("PythonRuff: on_pre_save triggered")

        if not view.match_selector(0, "source.python"):
            print("PythonRuff: Not a Python file, skipping")
            return

        print("PythonRuff: Python file detected")
        settings = sublime.load_settings("PythonRuff.sublime-settings")

        format_on_save = settings.get("format_on_save", False)
        lint_on_save = settings.get("lint_on_save", False)
        fix_on_save = settings.get("fix_on_save", False)

        print("PythonRuff: format_on_save = {}".format(format_on_save))
        print("PythonRuff: lint_on_save = {}".format(lint_on_save))
        print("PythonRuff: fix_on_save = {}".format(fix_on_save))

        # Check for project-specific settings
        project_data = view.window().project_data()
        if project_data:
            project_settings = project_data.get("settings", {}).get("python_ruff", {})
            format_on_save = project_settings.get("format_on_save", format_on_save)
            lint_on_save = project_settings.get("lint_on_save", lint_on_save)
            fix_on_save = project_settings.get("fix_on_save", fix_on_save)

        # Run fix first if enabled (it can fix many issues)
        if fix_on_save:
            print("PythonRuff: Running fix command")
            view.run_command("python_ruff_fix")

        # Then format if enabled
        if format_on_save:
            print("PythonRuff: Running format command")
            view.run_command("python_ruff_format", {"use_selection": False})

    def on_post_save(self, view):
        """Lint after save if enabled."""
        if not view.match_selector(0, "source.python"):
            return

        settings = sublime.load_settings("PythonRuff.sublime-settings")
        lint_on_save = settings.get("lint_on_save", False)

        # Check for project-specific settings
        project_data = view.window().project_data()
        if project_data:
            project_settings = project_data.get("settings", {}).get("python_ruff", {})
            lint_on_save = project_settings.get("lint_on_save", lint_on_save)

        if lint_on_save:
            print("PythonRuff: Running lint command on post_save")
            view.run_command("python_ruff_lint")


class PythonRuffCheckCommand(sublime_plugin.WindowCommand):
    """Check if Ruff is available."""

    def run(self):
        settings = sublime.load_settings("PythonRuff.sublime-settings")

        try:
            ruff_binary = find_ruff_binary(settings)

            # Get version
            proc = subprocess.Popen(
                [ruff_binary, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = proc.communicate(timeout=5)

            if proc.returncode == 0:
                version = stdout.decode("utf-8").strip()
                sublime.message_dialog("PythonRuff\n\nFound: {}\n{}".format(ruff_binary, version))
            else:
                sublime.error_message("Found ruff at {} but failed to get version".format(ruff_binary))

        except FileNotFoundError as e:
            sublime.error_message(str(e))
        except Exception as e:
            sublime.error_message("PythonRuff: {}".format(str(e)))


class PythonRuffToggleFormatOnSaveCommand(sublime_plugin.WindowCommand):
    """Toggle format on save setting."""

    def run(self):
        settings = sublime.load_settings("PythonRuff.sublime-settings")
        current = settings.get("format_on_save", False)
        settings.set("format_on_save", not current)
        sublime.save_settings("PythonRuff.sublime-settings")

        status = "enabled" if not current else "disabled"
        sublime.status_message("PythonRuff: Format on save {}".format(status))

    def is_checked(self):
        settings = sublime.load_settings("PythonRuff.sublime-settings")
        return settings.get("format_on_save", False)


class PythonRuffToggleLintOnSaveCommand(sublime_plugin.WindowCommand):
    """Toggle lint on save setting."""

    def run(self):
        settings = sublime.load_settings("PythonRuff.sublime-settings")
        current = settings.get("lint_on_save", False)
        settings.set("lint_on_save", not current)
        sublime.save_settings("PythonRuff.sublime-settings")

        status = "enabled" if not current else "disabled"
        sublime.status_message("PythonRuff: Lint on save {}".format(status))

    def is_checked(self):
        settings = sublime.load_settings("PythonRuff.sublime-settings")
        return settings.get("lint_on_save", False)


class PythonRuffToggleFixOnSaveCommand(sublime_plugin.WindowCommand):
    """Toggle fix on save setting."""

    def run(self):
        settings = sublime.load_settings("PythonRuff.sublime-settings")
        current = settings.get("fix_on_save", False)
        settings.set("fix_on_save", not current)
        sublime.save_settings("PythonRuff.sublime-settings")

        status = "enabled" if not current else "disabled"
        sublime.status_message("PythonRuff: Fix on save {}".format(status))

    def is_checked(self):
        settings = sublime.load_settings("PythonRuff.sublime-settings")
        return settings.get("fix_on_save", False)

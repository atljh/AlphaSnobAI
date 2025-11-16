"""Log Viewer Widget - Real-time log viewing with filtering.

Displays bot logs in real-time with color coding and filtering options.
"""

import sys
from pathlib import Path
from collections import deque

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QComboBox, QLineEdit, QLabel, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import get_settings
from gui.backend.bot_process import BotProcessManager


class LogViewerWidget(QWidget):
    """Widget for viewing bot logs in real-time."""

    def __init__(self, bot_manager: BotProcessManager):
        super().__init__()
        self.bot_manager = bot_manager
        self.settings = get_settings()

        # Log buffer
        self.log_buffer = deque(maxlen=1000)  # Keep last 1000 lines

        # Autoscroll enabled
        self.autoscroll_enabled = True

        # Filter settings
        self.current_level_filter = "ALL"
        self.current_search_filter = ""

        # Connect to bot manager signals
        self.bot_manager.log_received.connect(self._on_log_received)

        # Create UI
        self._create_ui()

        # Start log file tailing timer
        self.tail_timer = QTimer()
        self.tail_timer.timeout.connect(self._tail_log_file)
        self.tail_timer.start(1000)  # Check every second

        # Track last file position
        self.last_file_position = 0

        # Load existing logs
        self._load_existing_logs()

    def _create_ui(self):
        """Create user interface with glassmorphism design."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Toolbar with glass styling
        toolbar = QWidget()
        toolbar.setObjectName("glassCard")
        toolbar.setStyleSheet("""
            QWidget#glassCard {
                padding: 12px;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setSpacing(12)

        # Level filter
        level_label = QLabel("Level:")
        level_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        toolbar_layout.addWidget(level_label)

        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR"])
        self.level_combo.setMinimumWidth(120)
        self.level_combo.currentTextChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self.level_combo)

        # Search filter
        search_label = QLabel("Search:")
        search_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        toolbar_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter logs...")
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self.search_input)

        # Autoscroll checkbox
        self.autoscroll_checkbox = QCheckBox("Auto-scroll")
        self.autoscroll_checkbox.setChecked(True)
        self.autoscroll_checkbox.stateChanged.connect(self._on_autoscroll_toggled)
        toolbar_layout.addWidget(self.autoscroll_checkbox)

        toolbar_layout.addStretch()

        # Clear button with gradient
        clear_button = QPushButton("Clear")
        clear_button.setMinimumHeight(36)
        clear_button.setCursor(Qt.PointingHandCursor)
        clear_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ef4444,
                    stop:1 #f59e0b
                );
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #dc2626,
                    stop:1 #d97706
                );
            }
        """)
        clear_button.clicked.connect(self._on_clear_clicked)
        toolbar_layout.addWidget(clear_button)

        # Export button with gradient
        export_button = QPushButton("Export")
        export_button.setMinimumHeight(36)
        export_button.setCursor(Qt.PointingHandCursor)
        export_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1,
                    stop:1 #8b5cf6
                );
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5,
                    stop:1 #7c3aed
                );
            }
        """)
        export_button.clicked.connect(self._on_export_clicked)
        toolbar_layout.addWidget(export_button)

        layout.addWidget(toolbar)

        # Log text area with glass styling
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("JetBrains Mono", 12))
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        # Styling handled by theme QSS
        layout.addWidget(self.log_text)

    def _load_existing_logs(self):
        """Load existing logs from file."""
        try:
            log_file = Path(self.settings.paths.logs)
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Get last 100 lines
                    for line in lines[-100:]:
                        self._add_log_line(line.rstrip())

                    self.last_file_position = f.tell()
        except Exception as e:
            self._add_log_line(f"[WARNING] Failed to load existing logs: {e}", force=True)

    def _tail_log_file(self):
        """Tail log file for new lines."""
        try:
            log_file = Path(self.settings.paths.logs)
            if not log_file.exists():
                return

            with open(log_file, 'r', encoding='utf-8') as f:
                # Seek to last known position
                f.seek(self.last_file_position)

                # Read new lines
                for line in f:
                    self._add_log_line(line.rstrip())

                # Update position
                self.last_file_position = f.tell()

        except Exception as e:
            # Silently ignore errors (file might be locked)
            pass

    def _on_log_received(self, log_line: str):
        """Handle log line from bot process."""
        self._add_log_line(log_line)

    def _add_log_line(self, line: str, force: bool = False):
        """Add log line to buffer and display.

        Args:
            line: Log line to add
            force: If True, bypass filters
        """
        # Add to buffer
        self.log_buffer.append(line)

        # Check filters (unless forced)
        if not force and not self._line_matches_filters(line):
            return

        # Detect level
        level = self._detect_level(line)

        # Format line with colors
        self._append_colored_line(line, level)

        # Autoscroll if enabled
        if self.autoscroll_enabled:
            self.log_text.moveCursor(QTextCursor.End)

    def _detect_level(self, line: str) -> str:
        """Detect log level from line."""
        line_upper = line.upper()
        if "[ERROR]" in line_upper or "ERROR:" in line_upper:
            return "ERROR"
        elif "[WARNING]" in line_upper or "WARNING:" in line_upper:
            return "WARNING"
        elif "[SUCCESS]" in line_upper or "SUCCESS:" in line_upper:
            return "SUCCESS"
        elif "[DEBUG]" in line_upper or "DEBUG:" in line_upper:
            return "DEBUG"
        elif "[INFO]" in line_upper or "INFO:" in line_upper:
            return "INFO"
        else:
            return "INFO"

    def _append_colored_line(self, line: str, level: str):
        """Append line with modern neon color formatting."""
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Create format based on level
        fmt = QTextCharFormat()

        # Modern vibrant neon colors
        colors = {
            "ERROR": QColor(239, 68, 68),        # #ef4444 - Bright Red
            "WARNING": QColor(245, 158, 11),     # #f59e0b - Bright Orange
            "SUCCESS": QColor(16, 185, 129),     # #10b981 - Bright Green
            "INFO": QColor(99, 102, 241),        # #6366f1 - Bright Indigo
            "DEBUG": QColor(148, 163, 184),      # #94a3b8 - Light Gray
        }

        fmt.setForeground(colors.get(level, QColor(203, 213, 225)))

        # Insert text with format
        cursor.insertText(line + "\n", fmt)

    def _line_matches_filters(self, line: str) -> bool:
        """Check if line matches current filters."""
        # Level filter
        if self.current_level_filter != "ALL":
            if self.current_level_filter not in line.upper():
                return False

        # Search filter
        if self.current_search_filter:
            if self.current_search_filter.lower() not in line.lower():
                return False

        return True

    def _on_filter_changed(self):
        """Handle filter change."""
        self.current_level_filter = self.level_combo.currentText()
        self.current_search_filter = self.search_input.text()

        # Re-render all logs with new filter
        self._rerender_logs()

    def _rerender_logs(self):
        """Re-render all logs from buffer with current filters."""
        self.log_text.clear()

        for line in self.log_buffer:
            if self._line_matches_filters(line):
                level = self._detect_level(line)
                self._append_colored_line(line, level)

        # Scroll to bottom
        if self.autoscroll_enabled:
            self.log_text.moveCursor(QTextCursor.End)

    def _on_autoscroll_toggled(self, state):
        """Handle autoscroll toggle."""
        self.autoscroll_enabled = (state == Qt.Checked)

    def _on_clear_clicked(self):
        """Handle clear button click."""
        self.log_text.clear()
        self.log_buffer.clear()

    def _on_export_clicked(self):
        """Handle export button click."""
        from PySide6.QtWidgets import QFileDialog
        from datetime import datetime

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())

                self._add_log_line(f"[SUCCESS] Logs exported to {filename}", force=True)
            except Exception as e:
                self._add_log_line(f"[ERROR] Failed to export logs: {e}", force=True)

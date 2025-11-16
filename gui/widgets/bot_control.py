"""Bot Control Widget - Start/Stop/Restart Bot.

Provides controls and status display for the bot process.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from gui.backend.bot_process import BotProcessManager


class BotControlWidget(QWidget):
    """Widget for controlling bot process."""

    def __init__(self, bot_manager: BotProcessManager):
        super().__init__()
        self.bot_manager = bot_manager

        # Connect signals
        self.bot_manager.status_changed.connect(self._on_status_changed)
        self.bot_manager.error_occurred.connect(self._on_error)

        # Create UI
        self._create_ui()

        # Update status
        self._update_status()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(2000)  # Update every 2 seconds

    def _create_ui(self):
        """Create user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Status group with glass card styling
        status_group = QGroupBox("Bot Status")
        status_group.setObjectName("glassCard")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(16)

        # Status indicator with larger modern style
        status_indicator_layout = QHBoxLayout()

        # Status indicator dot
        self.status_icon = QLabel("●")
        self.status_icon.setFont(QFont("Arial", 32))
        self.status_icon.setStyleSheet("color: #ef4444;")  # Red by default
        status_indicator_layout.addWidget(self.status_icon)

        self.status_label = QLabel("Stopped")
        self.status_label.setFont(QFont("Inter", 18, QFont.Bold))
        self.status_label.setStyleSheet("color: #e2e8f0;")
        status_indicator_layout.addWidget(self.status_label)

        status_indicator_layout.addStretch()

        status_layout.addLayout(status_indicator_layout)

        # Process info with modern styling
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        self.pid_label = QLabel("PID: --")
        self.pid_label.setStyleSheet("font-size: 13px; color: #cbd5e1; padding: 4px;")
        info_layout.addWidget(self.pid_label)

        self.uptime_label = QLabel("Uptime: --")
        self.uptime_label.setStyleSheet("font-size: 13px; color: #cbd5e1; padding: 4px;")
        info_layout.addWidget(self.uptime_label)

        self.cpu_label = QLabel("CPU: --")
        self.cpu_label.setStyleSheet("font-size: 13px; color: #cbd5e1; padding: 4px;")
        info_layout.addWidget(self.cpu_label)

        self.memory_label = QLabel("Memory: --")
        self.memory_label.setStyleSheet("font-size: 13px; color: #cbd5e1; padding: 4px;")
        info_layout.addWidget(self.memory_label)

        status_layout.addLayout(info_layout)

        layout.addWidget(status_group)

        # Control buttons with glass card styling
        control_group = QGroupBox("Controls")
        control_group.setObjectName("glassCard")
        control_layout = QVBoxLayout(control_group)
        control_layout.setSpacing(12)

        # Start button with green gradient
        self.start_button = QPushButton("Start Bot")
        self.start_button.setMinimumHeight(48)
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981,
                    stop:1 #06b6d4
                );
                color: white;
                font-size: 15px;
                font-weight: 600;
                border: none;
                border-radius: 12px;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669,
                    stop:1 #0891b2
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #047857,
                    stop:1 #0e7490
                );
            }
            QPushButton:disabled {
                background: rgba(71, 85, 105, 0.5);
                color: #64748b;
            }
        """)
        self.start_button.clicked.connect(self._on_start_clicked)
        control_layout.addWidget(self.start_button)

        # Stop button with red gradient
        self.stop_button = QPushButton("Stop Bot")
        self.stop_button.setMinimumHeight(48)
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ef4444,
                    stop:1 #f59e0b
                );
                color: white;
                font-size: 15px;
                font-weight: 600;
                border: none;
                border-radius: 12px;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #dc2626,
                    stop:1 #d97706
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #b91c1c,
                    stop:1 #b45309
                );
            }
            QPushButton:disabled {
                background: rgba(71, 85, 105, 0.5);
                color: #64748b;
            }
        """)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        control_layout.addWidget(self.stop_button)

        # Restart button with purple gradient
        self.restart_button = QPushButton("Restart Bot")
        self.restart_button.setMinimumHeight(48)
        self.restart_button.setCursor(Qt.PointingHandCursor)
        self.restart_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6,
                    stop:1 #ec4899
                );
                color: white;
                font-size: 15px;
                font-weight: 600;
                border: none;
                border-radius: 12px;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed,
                    stop:1 #db2777
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d28d9,
                    stop:1 #be185d
                );
            }
            QPushButton:disabled {
                background: rgba(71, 85, 105, 0.5);
                color: #64748b;
            }
        """)
        self.restart_button.clicked.connect(self._on_restart_clicked)
        control_layout.addWidget(self.restart_button)

        layout.addWidget(control_group)

        # Restart required indicator with glass styling
        self.restart_required_label = QLabel("Restart required to apply settings")
        self.restart_required_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f59e0b,
                    stop:1 #f97316
                );
                color: white;
                padding: 14px 20px;
                border-radius: 12px;
                font-weight: 600;
                font-size: 14px;
                border: 1px solid rgba(251, 146, 60, 0.3);
            }
        """)
        self.restart_required_label.setAlignment(Qt.AlignCenter)
        self.restart_required_label.hide()
        layout.addWidget(self.restart_required_label)

        layout.addStretch()

    def _on_start_clicked(self):
        """Handle start button click."""
        self.start_button.setEnabled(False)
        self.bot_manager.start_bot()

    def _on_stop_clicked(self):
        """Handle stop button click."""
        self.stop_button.setEnabled(False)
        self.bot_manager.stop_bot()

    def _on_restart_clicked(self):
        """Handle restart button click."""
        # Confirm restart
        reply = QMessageBox.question(
            self,
            "Confirm Restart",
            "Are you sure you want to restart the bot?\n\n"
            "This will temporarily disconnect from Telegram.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.restart_button.setEnabled(False)
            self.bot_manager.restart_bot()
            # Hide restart required indicator
            self.restart_required_label.hide()

    def _on_status_changed(self, status: str):
        """Handle status change."""
        self._update_status()

    def _on_error(self, error: str):
        """Handle error."""
        QMessageBox.critical(
            self,
            "Bot Error",
            error
        )
        self._update_status()

    def _update_status(self):
        """Update status display."""
        status = self.bot_manager.get_status()

        # Update status label and icon
        if status["status"] == "running":
            self.status_icon.setText("●")
            self.status_icon.setStyleSheet("color: #10b981;")  # Green
            self.status_label.setText("Running")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.restart_button.setEnabled(True)
        elif status["status"] == "starting":
            self.status_icon.setText("●")
            self.status_icon.setStyleSheet("color: #f59e0b;")  # Yellow
            self.status_label.setText("Starting...")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.restart_button.setEnabled(False)
        elif status["status"] == "stopping":
            self.status_icon.setText("●")
            self.status_icon.setStyleSheet("color: #f59e0b;")  # Yellow
            self.status_label.setText("Stopping...")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.restart_button.setEnabled(False)
        else:  # stopped
            self.status_icon.setText("●")
            self.status_icon.setStyleSheet("color: #ef4444;")  # Red
            self.status_label.setText("Stopped")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.restart_button.setEnabled(False)

        # Update process info
        if status["pid"]:
            self.pid_label.setText(f"PID: {status['pid']}")
        else:
            self.pid_label.setText("PID: --")

        if status["uptime"]:
            hours = int(status["uptime"] // 3600)
            minutes = int((status["uptime"] % 3600) // 60)
            seconds = int(status["uptime"] % 60)
            self.uptime_label.setText(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            self.uptime_label.setText("Uptime: --")

        if status["cpu_percent"] > 0:
            self.cpu_label.setText(f"CPU: {status['cpu_percent']:.1f}%")
        else:
            self.cpu_label.setText("CPU: --")

        if status["memory_mb"] > 0:
            self.memory_label.setText(f"Memory: {status['memory_mb']:.1f} MB")
        else:
            self.memory_label.setText("Memory: --")

    def show_restart_required(self):
        """Show restart required indicator."""
        self.restart_required_label.show()

    def hide_restart_required(self):
        """Hide restart required indicator."""
        self.restart_required_label.hide()

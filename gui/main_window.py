"""Main Window for AlphaSnobAI GUI Application.

Provides the main interface with sidebar navigation and content area.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QStackedWidget, QLabel, QStatusBar,
    QMenuBar, QMenu
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction

# Import backend
from gui.backend.bot_process import BotProcessManager

# Import widgets
from gui.widgets.bot_control import BotControlWidget
from gui.widgets.log_viewer import LogViewerWidget


class PlaceholderWidget(QWidget):
    """Placeholder widget for development."""

    def __init__(self, name: str):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel(f"<h1>{name}</h1><p>This screen is under development.</p>")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AlphaSnobAI - Bot Management")
        self.resize(1200, 800)

        # Create bot process manager
        self.bot_manager = BotProcessManager()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create sidebar
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)

        # Create stacked widget for content
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        # Add screens
        self._add_screens()

        # Create menu bar
        self._create_menu_bar()

        # Create status bar
        self._create_status_bar()

        # Connect sidebar to content stack
        self.sidebar.currentRowChanged.connect(self.content_stack.setCurrentIndex)

        # Set initial screen
        self.sidebar.setCurrentRow(0)

        # Update status bar periodically
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(2000)  # Update every 2 seconds

    def _create_sidebar(self) -> QListWidget:
        """Create sidebar navigation."""
        sidebar = QListWidget()
        sidebar.setMaximumWidth(200)
        sidebar.setMinimumWidth(150)

        # Add navigation items
        items = [
            "📊 Dashboard",
            "📋 Logs",
            "⚙️ Settings",
            "🎓 Owner Learning",
            "📈 Statistics",
            "🗄️ Database",
        ]

        for item in items:
            sidebar.addItem(item)

        # Style
        sidebar.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                border: none;
                border-right: 1px solid #3d3d3d;
                font-size: 14px;
                padding: 10px 0;
            }
            QListWidget::item {
                padding: 12px 20px;
                border-bottom: 1px solid #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #0d47a1;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
        """)

        return sidebar

    def _add_screens(self):
        """Add screens to content stack."""
        # Dashboard - create container with bot control widget
        self.dashboard_widget = self._create_dashboard()
        self.content_stack.addWidget(self.dashboard_widget)

        # Logs - use LogViewerWidget
        self.logs_widget = LogViewerWidget(self.bot_manager)
        self.content_stack.addWidget(self.logs_widget)

        # Settings (placeholder for now)
        self.settings_widget = PlaceholderWidget("Settings Editor")
        self.content_stack.addWidget(self.settings_widget)

        # Owner Learning (placeholder for now)
        self.owner_widget = PlaceholderWidget("Owner Learning")
        self.content_stack.addWidget(self.owner_widget)

        # Statistics (placeholder for now)
        self.stats_widget = PlaceholderWidget("Statistics")
        self.content_stack.addWidget(self.stats_widget)

        # Database (placeholder for now)
        self.db_widget = PlaceholderWidget("Database Manager")
        self.content_stack.addWidget(self.db_widget)

    def _create_dashboard(self) -> QWidget:
        """Create dashboard widget."""
        dashboard = QWidget()
        layout = QHBoxLayout(dashboard)

        # Left side - Bot Control
        self.bot_control_widget = BotControlWidget(self.bot_manager)
        self.bot_control_widget.setMaximumWidth(400)
        layout.addWidget(self.bot_control_widget)

        # Right side - Info/Stats
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)

        # Welcome message
        welcome_label = QLabel(
            "<h1>Welcome to AlphaSnobAI</h1>"
            "<p>Desktop management application for your Telegram bot.</p>"
        )
        welcome_label.setAlignment(Qt.AlignTop)
        info_layout.addWidget(welcome_label)

        # Quick stats placeholder
        stats_label = QLabel(
            "<h2>Quick Stats</h2>"
            "<p>• Messages processed: --</p>"
            "<p>• Responses sent: --</p>"
            "<p>• Response rate: --</p>"
        )
        stats_label.setAlignment(Qt.AlignTop)
        info_layout.addWidget(stats_label)

        info_layout.addStretch()

        layout.addWidget(info_widget)

        return dashboard

    def _create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_config_action = QAction("Open Config Folder", self)
        file_menu.addAction(open_config_action)

        open_logs_action = QAction("Open Logs Folder", self)
        file_menu.addAction(open_logs_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Bot menu
        bot_menu = menubar.addMenu("&Bot")

        start_action = QAction("Start Bot", self)
        start_action.setShortcut("Ctrl+S")
        bot_menu.addAction(start_action)

        stop_action = QAction("Stop Bot", self)
        stop_action.setShortcut("Ctrl+T")
        bot_menu.addAction(stop_action)

        restart_action = QAction("Restart Bot", self)
        restart_action.setShortcut("Ctrl+R")
        bot_menu.addAction(restart_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("About AlphaSnobAI", self)
        help_menu.addAction(about_action)

    def _create_status_bar(self):
        """Create status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status label
        self.status_label = QLabel("Bot Status: Checking...")
        self.status_bar.addWidget(self.status_label)

        # Uptime label
        self.uptime_label = QLabel("Uptime: --")
        self.status_bar.addPermanentWidget(self.uptime_label)

    def _update_status(self):
        """Update status bar information."""
        status = self.bot_manager.get_status()

        # Update status label
        status_icons = {
            "running": "🟢",
            "stopped": "🔴",
            "starting": "🟡",
            "stopping": "🟡"
        }
        icon = status_icons.get(status["status"], "🔴")
        self.status_label.setText(f"Bot Status: {icon} {status['status'].title()}")

        # Update uptime
        if status["uptime"]:
            hours = int(status["uptime"] // 3600)
            minutes = int((status["uptime"] % 3600) // 60)
            seconds = int(status["uptime"] % 60)
            self.uptime_label.setText(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            self.uptime_label.setText("Uptime: --")

    def closeEvent(self, event):
        """Handle window close event."""
        # Stop timers
        self.status_timer.stop()

        # Accept the event
        event.accept()

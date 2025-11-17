"""Main Window for AlphaSnobAI GUI Application.

Provides the main interface with sidebar navigation and content area.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

# Import backend
from gui.backend.bot_process import BotProcessManager

# Import widgets
from gui.widgets.bot_control import BotControlWidget
from gui.widgets.database_viewer import DatabaseViewerWidget
from gui.widgets.log_viewer import LogViewerWidget
from gui.widgets.owner_learning import OwnerLearningWidget
from gui.widgets.settings_editor import SettingsEditorWidget
from gui.widgets.statistics import StatisticsWidget


class PlaceholderWidget(QWidget):
    """Placeholder widget for development with glassmorphism design."""

    def __init__(self, name: str):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignCenter)

        # Glass card container
        card = QWidget()
        card.setObjectName("glassCard")
        card.setMaximumWidth(600)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(16)

        # Title
        title = QLabel(name)
        title.setStyleSheet(
            """
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #f1f5f9;
            }
        """,
        )
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        # Description
        desc = QLabel("This feature is under development and will be available soon.")
        desc.setWordWrap(True)
        desc.setStyleSheet(
            """
            QLabel {
                font-size: 15px;
                color: #cbd5e1;
                line-height: 1.6;
            }
        """,
        )
        desc.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(desc)

        layout.addWidget(card, alignment=Qt.AlignCenter)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, theme_manager=None):
        super().__init__()
        self.setWindowTitle("AlphaSnobAI - Bot Management")
        self.resize(1200, 800)

        # Store theme manager
        self.theme_manager = theme_manager

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
        sidebar.setMaximumWidth(220)
        sidebar.setMinimumWidth(180)

        # Add navigation items
        items = [
            "Dashboard",
            "Logs",
            "Settings",
            "Owner Learning",
            "Statistics",
            "Database",
        ]

        for item in items:
            sidebar.addItem(item)

        # Styling is handled by theme QSS files
        return sidebar

    def _add_screens(self):
        """Add screens to content stack."""
        # Dashboard - create container with bot control widget
        self.dashboard_widget = self._create_dashboard()
        self.content_stack.addWidget(self.dashboard_widget)

        # Logs - use LogViewerWidget
        self.logs_widget = LogViewerWidget(self.bot_manager)
        self.content_stack.addWidget(self.logs_widget)

        # Settings - use SettingsEditorWidget
        self.settings_widget = SettingsEditorWidget()
        self.content_stack.addWidget(self.settings_widget)

        # Owner Learning - use OwnerLearningWidget
        self.owner_widget = OwnerLearningWidget()
        self.content_stack.addWidget(self.owner_widget)

        # Statistics - use StatisticsWidget
        self.stats_widget = StatisticsWidget()
        self.content_stack.addWidget(self.stats_widget)

        # Database - use DatabaseViewerWidget
        self.db_widget = DatabaseViewerWidget()
        self.content_stack.addWidget(self.db_widget)

    def _create_dashboard(self) -> QWidget:
        """Create dashboard widget with glassmorphism design."""
        dashboard = QWidget()
        layout = QHBoxLayout(dashboard)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Left side - Bot Control
        self.bot_control_widget = BotControlWidget(self.bot_manager)
        self.bot_control_widget.setMaximumWidth(420)
        layout.addWidget(self.bot_control_widget)

        # Right side - Info/Stats with glass cards
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(20)

        # Welcome card
        welcome_card = QWidget()
        welcome_card.setObjectName("glassCard")
        welcome_layout = QVBoxLayout(welcome_card)
        welcome_layout.setContentsMargins(24, 24, 24, 24)

        welcome_title = QLabel("Welcome to AlphaSnobAI")
        welcome_title.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: 700;
                color: #f1f5f9;
                margin-bottom: 8px;
            }
        """,
        )
        welcome_layout.addWidget(welcome_title)

        welcome_desc = QLabel(
            "Modern desktop application for managing your Telegram bot with style.",
        )
        welcome_desc.setWordWrap(True)
        welcome_desc.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                color: #cbd5e1;
                line-height: 1.6;
            }
        """,
        )
        welcome_layout.addWidget(welcome_desc)

        info_layout.addWidget(welcome_card)

        # Quick stats card
        stats_card = QWidget()
        stats_card.setObjectName("glassCard")
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setContentsMargins(24, 24, 24, 24)
        stats_layout.setSpacing(16)

        stats_title = QLabel("Quick Stats")
        stats_title.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #f1f5f9;
                margin-bottom: 8px;
            }
        """,
        )
        stats_layout.addWidget(stats_title)

        # Stats items with gradient accents
        stats_items = [
            ("Messages processed", "--", "#10b981"),
            ("Responses sent", "--", "#8b5cf6"),
            ("Response rate", "--", "#06b6d4"),
        ]

        for label, value, color in stats_items:
            stat_item = QWidget()
            stat_layout = QHBoxLayout(stat_item)
            stat_layout.setContentsMargins(0, 8, 0, 8)

            stat_label = QLabel(f"• {label}:")
            stat_label.setStyleSheet(
                """
                QLabel {
                    font-size: 14px;
                    color: #cbd5e1;
                }
            """,
            )
            stat_layout.addWidget(stat_label)

            stat_value = QLabel(value)
            stat_value.setStyleSheet(
                f"""
                QLabel {{
                    font-size: 14px;
                    font-weight: 600;
                    color: {color};
                }}
            """,
            )
            stat_layout.addWidget(stat_value)
            stat_layout.addStretch()

            stats_layout.addWidget(stat_item)

        info_layout.addWidget(stats_card)

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

        # View menu
        view_menu = menubar.addMenu("&View")

        # Theme submenu
        theme_menu = view_menu.addMenu("Theme")

        # Glass themes (modern)
        glass_dark_action = QAction("Glass Dark (Modern)", self)
        glass_dark_action.triggered.connect(lambda: self._apply_theme_by_name("glass_dark"))
        theme_menu.addAction(glass_dark_action)

        glass_light_action = QAction("Glass Light (Modern)", self)
        glass_light_action.triggered.connect(lambda: self._apply_theme_by_name("glass_light"))
        theme_menu.addAction(glass_light_action)

        theme_menu.addSeparator()

        # macOS themes (classic)
        macos_dark_action = QAction("macOS Dark (Classic)", self)
        macos_dark_action.triggered.connect(lambda: self._apply_theme_by_name("macos_dark"))
        theme_menu.addAction(macos_dark_action)

        macos_light_action = QAction("macOS Light (Classic)", self)
        macos_light_action.triggered.connect(lambda: self._apply_theme_by_name("macos_light"))
        theme_menu.addAction(macos_light_action)

        theme_menu.addSeparator()

        toggle_theme_action = QAction("Toggle Theme", self)
        toggle_theme_action.setShortcut("Ctrl+Shift+T")
        toggle_theme_action.triggered.connect(self._toggle_theme)
        theme_menu.addAction(toggle_theme_action)

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
        self.status_label.setText(f"Bot Status: {status['status'].title()}")

        # Update uptime
        if status["uptime"]:
            hours = int(status["uptime"] // 3600)
            minutes = int((status["uptime"] % 3600) // 60)
            seconds = int(status["uptime"] % 60)
            self.uptime_label.setText(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            self.uptime_label.setText("Uptime: --")

    def _apply_theme_by_name(self, theme_name: str):
        """Apply theme by name."""
        if self.theme_manager:
            from gui.themes import Theme

            theme_map = {
                "glass_dark": Theme.GLASS_DARK,
                "glass_light": Theme.GLASS_LIGHT,
                "macos_dark": Theme.MACOS_DARK,
                "macos_light": Theme.MACOS_LIGHT,
            }
            theme = theme_map.get(theme_name)
            if theme:
                self.theme_manager.apply_theme(theme)

    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        if self.theme_manager:
            self.theme_manager.toggle_theme()

    def closeEvent(self, event):
        """Handle window close event."""
        # Stop timers
        self.status_timer.stop()

        # Accept the event
        event.accept()

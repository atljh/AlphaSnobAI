"""Theme management for AlphaSnobAI GUI.

Provides macOS-style themes with light and dark modes.
"""

from enum import Enum
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication


class Theme(Enum):
    """Available themes."""

    GLASS_DARK = "glass_dark"  # Modern glassmorphism dark (default)
    GLASS_LIGHT = "glass_light"  # Modern glassmorphism light
    MACOS_DARK = "macos_dark"  # Classic macOS dark
    MACOS_LIGHT = "macos_light"  # Classic macOS light


class ThemeManager:
    """Manages application themes."""

    def __init__(self):
        """Initialize theme manager."""
        self.themes_dir = Path(__file__).parent
        self.settings = QSettings("AlphaSnob", "AlphaSnobAI")
        self.current_theme = self._load_saved_theme()

    def _load_saved_theme(self) -> Theme:
        """Load saved theme from settings."""
        saved = self.settings.value("theme", "glass_dark")
        try:
            return Theme(saved)
        except ValueError:
            return Theme.GLASS_DARK

    def _save_theme(self, theme: Theme):
        """Save theme to settings."""
        self.settings.setValue("theme", theme.value)

    def get_stylesheet(self, theme: Theme) -> str:
        """Get stylesheet for theme.

        Args:
            theme: Theme to load

        Returns:
            QSS stylesheet content
        """
        qss_file = self.themes_dir / f"{theme.value}.qss"

        if not qss_file.exists():
            return ""

        with open(qss_file, encoding="utf-8") as f:
            return f.read()

    def apply_theme(self, theme: Theme, app: QApplication = None):
        """Apply theme to application.

        Args:
            theme: Theme to apply
            app: QApplication instance (if None, uses QApplication.instance())
        """
        if app is None:
            app = QApplication.instance()

        if app is None:
            return

        stylesheet = self.get_stylesheet(theme)
        app.setStyleSheet(stylesheet)

        self.current_theme = theme
        self._save_theme(theme)

    def toggle_theme(self, app: QApplication = None):
        """Toggle between light and dark themes.

        Args:
            app: QApplication instance
        """
        # Toggle between glass themes
        if self.current_theme == Theme.GLASS_DARK:
            new_theme = Theme.GLASS_LIGHT
        elif self.current_theme == Theme.GLASS_LIGHT:
            new_theme = Theme.GLASS_DARK
        elif self.current_theme == Theme.MACOS_DARK:
            new_theme = Theme.MACOS_LIGHT
        elif self.current_theme == Theme.MACOS_LIGHT:
            new_theme = Theme.MACOS_DARK
        else:
            new_theme = Theme.GLASS_DARK

        self.apply_theme(new_theme, app)

    def get_current_theme(self) -> Theme:
        """Get current active theme."""
        return self.current_theme

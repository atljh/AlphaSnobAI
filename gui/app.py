"""AlphaSnobAI GUI Application - Main Entry Point.

Cross-platform desktop application for managing AlphaSnobAI bot.
Built with PySide6 and QtAsyncio for seamless async/await integration.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtAsyncio import QAsyncioEventLoopPolicy
except ImportError:
    print("ERROR: PySide6 not installed!")
    print("Please install GUI dependencies:")
    print("  pip install -r requirements-gui.txt")
    sys.exit(1)

from gui.main_window import MainWindow
from gui.themes import ThemeManager, Theme


class AlphaSnobApp:
    """AlphaSnobAI Desktop Application."""

    def __init__(self):
        """Initialize the application."""
        # Enable high DPI scaling (must be set before creating QApplication)
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        # Create Qt application (or get existing instance)
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

        self.app.setApplicationName("AlphaSnobAI")
        self.app.setOrganizationName("AlphaSnob")
        self.app.setOrganizationDomain("alphasnob.ai")

        # Set asyncio event loop policy for Qt integration
        asyncio.set_event_loop_policy(QAsyncioEventLoopPolicy())

        # Create theme manager
        self.theme_manager = ThemeManager()

        # Apply theme
        self.theme_manager.apply_theme(self.theme_manager.current_theme, self.app)

        # Create main window (pass theme manager)
        self.main_window = MainWindow(self.theme_manager)


    def run(self):
        """Run the application."""
        self.main_window.show()
        return self.app.exec()


def main():
    """Main entry point for GUI application."""
    try:
        app = AlphaSnobApp()
        sys.exit(app.run())
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

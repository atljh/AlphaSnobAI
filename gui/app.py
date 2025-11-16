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

        # Apply dark theme
        self._apply_theme()

        # Create main window
        self.main_window = MainWindow()

    def _apply_theme(self):
        """Apply dark theme to application."""
        try:
            import qdarkstyle
            self.app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside6'))
        except ImportError:
            # Fallback to basic dark palette if qdarkstyle not available
            self._apply_basic_dark_theme()

    def _apply_basic_dark_theme(self):
        """Apply basic dark theme without qdarkstyle."""
        from PySide6.QtGui import QPalette, QColor
        from PySide6.QtCore import Qt

        palette = QPalette()

        # Dark colors
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(35, 35, 35))

        self.app.setPalette(palette)

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

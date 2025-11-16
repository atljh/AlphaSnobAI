#!/usr/bin/env python3
"""AlphaSnobAI GUI Launcher.

Launch the desktop GUI application for managing AlphaSnobAI bot.

Usage:
    python3 gui_launcher.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Check for PySide6
try:
    import PySide6
except ImportError:
    print("ERROR: PySide6 not installed!")
    print("\nPlease install GUI dependencies:")
    print("  pip install -r requirements-gui.txt")
    print("\nOr install manually:")
    print("  pip install PySide6 qtawesome qdarkstyle")
    sys.exit(1)

# Import and run GUI application
from gui.app import main

if __name__ == "__main__":
    sys.exit(main())

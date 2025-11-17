"""Bot Process Manager for GUI Application.

Manages the bot subprocess using QProcess with real-time output streaming.
"""

import sys
from datetime import datetime
from pathlib import Path

import psutil
from PySide6.QtCore import QObject, QProcess, QTimer, Signal

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bot.daemon import DaemonManager


class BotProcessManager(QObject):
    log_received = Signal(str)  # Emitted when new log line received
    status_changed = Signal(str)  # Emitted when bot status changes
    error_occurred = Signal(str)  # Emitted on error

    def __init__(self):
        super().__init__()

        from config.settings import get_settings

        settings = get_settings()

        self.process = None
        self.daemon_manager = DaemonManager(settings.daemon.pid_file)

        self._status = "stopped"
        self._pid = None
        self._start_time = None

        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._monitor_status)
        self.monitor_timer.start(2000)  # Check every 2 seconds

        self._check_existing_process()

    def _check_existing_process(self):
        if self.daemon_manager.is_running():
            self._pid = self.daemon_manager.get_pid()
            self._status = "running"
            self.status_changed.emit("running")
            self.log_received.emit(f"[INFO] Found running bot process (PID: {self._pid})")
        else:
            self._status = "stopped"
            self.status_changed.emit("stopped")

    def start_bot(self) -> bool:
        try:
            if self._status == "running":
                self.error_occurred.emit("Bot is already running")
                return False

            self.log_received.emit("[INFO] Starting bot...")
            self._status = "starting"
            self.status_changed.emit("starting")

            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(self._handle_stdout)
            self.process.readyReadStandardError.connect(self._handle_stderr)
            self.process.stateChanged.connect(self._handle_state_change)
            self.process.finished.connect(self._handle_finished)

            python_exe = sys.executable
            main_py = str(Path(__file__).parent.parent.parent / "main.py")

            self.process.start(python_exe, [main_py])

            if self.process.waitForStarted(5000):
                self._pid = self.process.processId()
                self._start_time = datetime.now()
                self._status = "running"
                self.status_changed.emit("running")
                self.log_received.emit(f"[SUCCESS] Bot started (PID: {self._pid})")
                return True
            self._status = "stopped"
            self.status_changed.emit("stopped")
            self.error_occurred.emit("Failed to start bot process")
            return False

        except Exception as e:
            self._status = "stopped"
            self.status_changed.emit("stopped")
            self.error_occurred.emit(f"Failed to start bot: {e}")
            return False

    def stop_bot(self) -> bool:
        """Stop the bot process.

        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if self._status == "stopped":
                self.error_occurred.emit("Bot is not running")
                return False

            self.log_received.emit("[INFO] Stopping bot...")
            self._status = "stopping"
            self.status_changed.emit("stopping")

            # Try to stop via QProcess if we have it
            if self.process and self.process.state() == QProcess.Running:
                self.process.terminate()

                if not self.process.waitForFinished(10000):  # Wait 10 seconds
                    self.log_received.emit("[WARNING] Termination timeout, killing process...")
                    self.process.kill()
                    self.process.waitForFinished(2000)

            # Also try daemon manager (in case bot was started externally)
            elif self.daemon_manager.is_running():
                self.daemon_manager.stop(timeout=10)

            self._pid = None
            self._start_time = None
            self._status = "stopped"
            self.status_changed.emit("stopped")
            self.log_received.emit("[SUCCESS] Bot stopped")
            return True

        except Exception as e:
            self.error_occurred.emit(f"Failed to stop bot: {e}")
            return False

    def restart_bot(self) -> bool:
        self.log_received.emit("[INFO] Restarting bot...")

        if self._status != "stopped":
            if not self.stop_bot():
                return False

        # Wait a bit before restarting
        QTimer.singleShot(2000, self.start_bot)
        return True

    def get_status(self) -> dict:
        """Get current bot status.

        Returns:
            Dictionary with status information
        """
        status = {
            "status": self._status,
            "pid": self._pid,
            "uptime": None,
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
        }

        if self._status == "running" and self._pid:
            # Calculate uptime
            if self._start_time:
                uptime_seconds = (datetime.now() - self._start_time).total_seconds()
                status["uptime"] = uptime_seconds

            # Get process info
            try:
                process = psutil.Process(self._pid)
                status["cpu_percent"] = process.cpu_percent(interval=0.1)
                status["memory_mb"] = process.memory_info().rss / 1024 / 1024
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return status

    def _monitor_status(self):
        """Monitor bot process status periodically."""
        if self._status == "running":
            # Check if process still exists
            if self._pid:
                try:
                    psutil.Process(self._pid)
                except psutil.NoSuchProcess:
                    self._status = "stopped"
                    self._pid = None
                    self._start_time = None
                    self.status_changed.emit("stopped")
                    self.log_received.emit("[WARNING] Bot process terminated unexpectedly")

    def _handle_stdout(self):
        """Handle stdout from bot process."""
        if self.process:
            data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
            for line in data.strip().split("\n"):
                if line:
                    self.log_received.emit(line)

    def _handle_stderr(self):
        """Handle stderr from bot process."""
        if self.process:
            data = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
            for line in data.strip().split("\n"):
                if line:
                    self.log_received.emit(f"[ERROR] {line}")

    def _handle_state_change(self, state):
        """Handle QProcess state changes."""
        if state == QProcess.NotRunning and self._status != "stopped":
            self._status = "stopped"
            self._pid = None
            self._start_time = None
            self.status_changed.emit("stopped")

    def _handle_finished(self, exit_code, exit_status):
        """Handle process finish."""
        if exit_code != 0:
            self.log_received.emit(f"[ERROR] Bot process exited with code {exit_code}")
            self.error_occurred.emit(f"Bot crashed (exit code: {exit_code})")
        else:
            self.log_received.emit("[INFO] Bot process finished normally")

        self._status = "stopped"
        self._pid = None
        self._start_time = None
        self.status_changed.emit("stopped")

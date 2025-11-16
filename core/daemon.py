"""Daemon management for AlphaSnobAI."""

import os
import sys
import time
import signal
import psutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class DaemonManager:
    """Manages daemon process lifecycle."""

    def __init__(self, pid_file: Path):
        """Initialize daemon manager.

        Args:
            pid_file: Path to PID file
        """
        self.pid_file = Path(pid_file)
        self.pid_file.parent.mkdir(exist_ok=True, parents=True)

    def start(self) -> int:
        """Start daemon process.

        Returns:
            PID of started process

        Raises:
            RuntimeError: If daemon is already running
        """
        # Check if already running
        if self.is_running():
            pid = self.get_pid()
            raise RuntimeError(f"Daemon is already running with PID {pid}")

        # Fork process
        try:
            pid = os.fork()
            if pid > 0:
                # Parent process - write PID and exit
                self._write_pid(pid)
                return pid
        except OSError as e:
            raise RuntimeError(f"Fork failed: {e}")

        # Child process continues
        # Detach from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # Second fork for complete daemon
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first child
                sys.exit(0)
        except OSError as e:
            raise RuntimeError(f"Second fork failed: {e}")

        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()

        # Note: We don't close/redirect stdin/stdout/stderr here
        # because we want to keep them for logging

        return os.getpid()

    def stop(self, timeout: int = 10) -> bool:
        """Stop daemon process.

        Args:
            timeout: Timeout in seconds to wait for graceful shutdown

        Returns:
            True if stopped successfully, False otherwise
        """
        pid = self.get_pid()
        if pid is None:
            return False

        try:
            process = psutil.Process(pid)

            # Send SIGTERM for graceful shutdown
            process.terminate()

            # Wait for process to terminate
            try:
                process.wait(timeout=timeout)
            except psutil.TimeoutExpired:
                # Force kill if not terminated
                process.kill()
                process.wait(timeout=5)

            # Remove PID file
            self._remove_pid()
            return True

        except psutil.NoSuchProcess:
            # Process doesn't exist, clean up PID file
            self._remove_pid()
            return True
        except Exception:
            return False

    def restart(self, timeout: int = 10) -> int:
        """Restart daemon process.

        Args:
            timeout: Timeout for stopping

        Returns:
            PID of new process
        """
        if self.is_running():
            self.stop(timeout=timeout)

        # Wait a bit for cleanup
        time.sleep(1)

        return self.start()

    def is_running(self) -> bool:
        """Check if daemon is running.

        Returns:
            True if running, False otherwise
        """
        pid = self.get_pid()
        if pid is None:
            return False

        try:
            process = psutil.Process(pid)
            return process.is_running()
        except psutil.NoSuchProcess:
            # PID file exists but process doesn't
            self._remove_pid()
            return False

    def get_pid(self) -> Optional[int]:
        """Get PID from PID file.

        Returns:
            PID or None if not found
        """
        if not self.pid_file.exists():
            return None

        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            return pid
        except (ValueError, IOError):
            return None

    def get_status(self) -> Dict[str, Any]:
        """Get detailed daemon status.

        Returns:
            Dictionary with status information
        """
        pid = self.get_pid()

        if pid is None:
            return {
                'running': False,
                'pid': None,
                'uptime': None,
                'memory_mb': None,
                'cpu_percent': None,
            }

        try:
            process = psutil.Process(pid)

            if not process.is_running():
                self._remove_pid()
                return {
                    'running': False,
                    'pid': pid,
                    'uptime': None,
                    'memory_mb': None,
                    'cpu_percent': None,
                }

            # Get process info
            create_time = datetime.fromtimestamp(process.create_time())
            uptime = datetime.now() - create_time

            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB

            cpu_percent = process.cpu_percent(interval=0.1)

            return {
                'running': True,
                'pid': pid,
                'uptime': uptime,
                'memory_mb': memory_mb,
                'cpu_percent': cpu_percent,
                'create_time': create_time,
            }

        except psutil.NoSuchProcess:
            self._remove_pid()
            return {
                'running': False,
                'pid': pid,
                'uptime': None,
                'memory_mb': None,
                'cpu_percent': None,
            }

    def _write_pid(self, pid: int):
        """Write PID to file.

        Args:
            pid: Process ID to write
        """
        with open(self.pid_file, 'w') as f:
            f.write(str(pid))

    def _remove_pid(self):
        """Remove PID file."""
        if self.pid_file.exists():
            self.pid_file.unlink()


def setup_signal_handlers(callback):
    """Setup signal handlers for graceful shutdown.

    Args:
        callback: Function to call on shutdown signal
    """
    def signal_handler(signum, frame):
        callback()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

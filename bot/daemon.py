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

    def __init__(self, pid_file: Path):
        """Initialize daemon manager.

        Args:
            pid_file: Path to PID file
        """
        self.pid_file = Path(pid_file)
        self.pid_file.parent.mkdir(exist_ok=True, parents=True)

    def start(self) -> int:

        if self.is_running():
            pid = self.get_pid()
            raise RuntimeError(f"Daemon is already running with PID {pid}")

        try:
            pid = os.fork()
            if pid > 0:
                self._write_pid(pid)
                return pid
        except OSError as e:
            raise RuntimeError(f"Fork failed: {e}")

        os.chdir("/")
        os.setsid()
        os.umask(0)

        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            raise RuntimeError(f"Second fork failed: {e}")

        sys.stdout.flush()
        sys.stderr.flush()

        # Note: We don't close/redirect stdin/stdout/stderr here
        # because we want to keep them for logging

        return os.getpid()

    def stop(self, timeout: int = 10) -> bool:
        pid = self.get_pid()
        if pid is None:
            return False

        try:
            process = psutil.Process(pid)

            process.terminate()

            try:
                process.wait(timeout=timeout)
            except psutil.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

            self._remove_pid()
            return True

        except psutil.NoSuchProcess:
            self._remove_pid()
            return True
        except Exception:
            return False

    def restart(self, timeout: int = 10) -> int:
        if self.is_running():
            self.stop(timeout=timeout)

        time.sleep(1)

        return self.start()

    def is_running(self) -> bool:
        pid = self.get_pid()
        if pid is None:
            return False

        try:
            process = psutil.Process(pid)
            return process.is_running()
        except psutil.NoSuchProcess:
            self._remove_pid()
            return False

    def get_pid(self) -> Optional[int]:
        if not self.pid_file.exists():
            return None

        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            return pid
        except (ValueError, IOError):
            return None

    def get_status(self) -> Dict[str, Any]:
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
        with open(self.pid_file, 'w') as f:
            f.write(str(pid))

    def _remove_pid(self):
        """Remove PID file."""
        if self.pid_file.exists():
            self.pid_file.unlink()


def setup_signal_handlers(callback):
    def signal_handler(signum, frame):
        callback()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

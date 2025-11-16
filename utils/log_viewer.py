"""Log viewing and filtering utilities."""

import re
from pathlib import Path
from typing import Optional, List, Iterator
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    SUCCESS = "SUCCESS"


@dataclass
class LogEntry:
    """Parsed log entry."""
    timestamp: datetime
    logger: str
    level: LogLevel
    message: str
    raw: str


class LogViewer:
    """View and filter log files."""

    # Log line pattern: timestamp - logger - level - message
    LOG_PATTERN = re.compile(
        r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([\w\.]+) - (\w+) - (.+)$'
    )

    # Level icons
    LEVEL_ICONS = {
        LogLevel.DEBUG: "🔍",
        LogLevel.INFO: "🤖",
        LogLevel.WARNING: "⚠️",
        LogLevel.ERROR: "❌",
        LogLevel.CRITICAL: "🚨",
        LogLevel.SUCCESS: "✅",
    }

    # Level colors
    LEVEL_COLORS = {
        LogLevel.DEBUG: "dim",
        LogLevel.INFO: "cyan",
        LogLevel.WARNING: "yellow",
        LogLevel.ERROR: "red",
        LogLevel.CRITICAL: "bold red",
        LogLevel.SUCCESS: "green",
    }

    def __init__(self, log_path: Path):
        """Initialize log viewer.

        Args:
            log_path: Path to log file
        """
        self.log_path = log_path

    def parse_line(self, line: str) -> Optional[LogEntry]:
        """Parse a log line.

        Args:
            line: Log line to parse

        Returns:
            LogEntry if parsed successfully, None otherwise
        """
        match = self.LOG_PATTERN.match(line.strip())
        if not match:
            return None

        timestamp_str, logger, level_str, message = match.groups()

        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
            level = LogLevel(level_str)

            return LogEntry(
                timestamp=timestamp,
                logger=logger,
                level=level,
                message=message,
                raw=line
            )
        except (ValueError, KeyError):
            return None

    def read_logs(
        self,
        lines: Optional[int] = None,
        level: Optional[LogLevel] = None,
        since: Optional[timedelta] = None,
        search: Optional[str] = None,
        reverse: bool = True
    ) -> List[LogEntry]:
        """Read and filter logs.

        Args:
            lines: Number of lines to return (None = all)
            level: Filter by minimum log level
            since: Filter logs since this time ago
            search: Search text in messages
            reverse: Return in reverse chronological order

        Returns:
            List of log entries
        """
        if not self.log_path.exists():
            return []

        entries = []
        cutoff_time = datetime.now() - since if since else None

        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line in f:
                entry = self.parse_line(line)
                if not entry:
                    continue

                # Filter by time
                if cutoff_time and entry.timestamp < cutoff_time:
                    continue

                # Filter by level
                if level and not self._level_matches(entry.level, level):
                    continue

                # Filter by search text
                if search and search.lower() not in entry.message.lower():
                    continue

                entries.append(entry)

        # Sort and limit
        if reverse:
            entries = list(reversed(entries))

        if lines:
            entries = entries[:lines]

        return entries

    def tail_logs(
        self,
        level: Optional[LogLevel] = None,
        search: Optional[str] = None
    ) -> Iterator[LogEntry]:
        """Tail log file (like tail -f).

        Args:
            level: Filter by minimum log level
            search: Search text in messages

        Yields:
            Log entries as they appear
        """
        import time

        if not self.log_path.exists():
            return

        with open(self.log_path, 'r', encoding='utf-8') as f:
            # Go to end of file
            f.seek(0, 2)

            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue

                entry = self.parse_line(line)
                if not entry:
                    continue

                # Filter by level
                if level and not self._level_matches(entry.level, level):
                    continue

                # Filter by search text
                if search and search.lower() not in entry.message.lower():
                    continue

                yield entry

    def export_logs(
        self,
        output_path: Path,
        level: Optional[LogLevel] = None,
        since: Optional[timedelta] = None,
        search: Optional[str] = None
    ) -> int:
        """Export filtered logs to file.

        Args:
            output_path: Path to output file
            level: Filter by minimum log level
            since: Filter logs since this time ago
            search: Search text in messages

        Returns:
            Number of lines exported
        """
        entries = self.read_logs(
            lines=None,
            level=level,
            since=since,
            search=search,
            reverse=False
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in entries:
                f.write(entry.raw)

        return len(entries)

    def _level_matches(self, entry_level: LogLevel, filter_level: LogLevel) -> bool:
        """Check if entry level matches filter.

        Args:
            entry_level: Log entry level
            filter_level: Filter level (minimum)

        Returns:
            True if entry should be included
        """
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.SUCCESS: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4,
        }

        return level_order.get(entry_level, 0) >= level_order.get(filter_level, 0)

    @staticmethod
    def format_entry(entry: LogEntry, show_logger: bool = False) -> str:
        """Format log entry for display.

        Args:
            entry: Log entry to format
            show_logger: Include logger name

        Returns:
            Formatted string with Rich markup
        """
        icon = LogViewer.LEVEL_ICONS.get(entry.level, "")
        color = LogViewer.LEVEL_COLORS.get(entry.level, "")

        timestamp = entry.timestamp.strftime("%H:%M:%S")

        parts = [
            f"[dim]{timestamp}[/dim]",
            f"{icon}",
            f"[{color}]{entry.level.value}[/{color}]",
        ]

        if show_logger:
            parts.append(f"[dim]{entry.logger}[/dim]")

        parts.append(entry.message)

        return " ".join(parts)

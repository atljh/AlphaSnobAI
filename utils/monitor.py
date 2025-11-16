"""Real-time monitoring with Rich Live display."""

import asyncio
import psutil
from pathlib import Path
from collections import deque
from datetime import datetime, timedelta
from typing import Optional, Deque
from dataclasses import dataclass

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

from utils.log_viewer import LogViewer, LogEntry
from utils.stats_collector import StatsCollector


@dataclass
class MonitorState:
    """Monitor state data."""
    start_time: datetime
    pid: Optional[int]
    messages_count: int
    responses_count: int
    recent_messages: Deque[str]
    recent_responses: Deque[str]
    recent_decisions: Deque[str]
    recent_logs: Deque[LogEntry]


class BotMonitor:
    """Real-time bot monitoring."""

    def __init__(
        self,
        db_path: Path,
        log_path: Path,
        pid_file: Path,
        update_interval: float = 1.0
    ):
        """Initialize monitor.

        Args:
            db_path: Path to database
            log_path: Path to log file
            pid_file: Path to PID file
            update_interval: Update interval in seconds
        """
        self.db_path = db_path
        self.log_path = log_path
        self.pid_file = pid_file
        self.update_interval = update_interval

        self.console = Console()
        self.stats_collector = StatsCollector(db_path)
        self.log_viewer = LogViewer(log_path)

        self.state = MonitorState(
            start_time=datetime.now(),
            pid=None,
            messages_count=0,
            responses_count=0,
            recent_messages=deque(maxlen=10),
            recent_responses=deque(maxlen=10),
            recent_decisions=deque(maxlen=10),
            recent_logs=deque(maxlen=20)
        )

        self._running = False

    def get_bot_pid(self) -> Optional[int]:
        """Get bot process ID.

        Returns:
            PID or None if not running
        """
        if not self.pid_file.exists():
            return None

        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Check if process exists
            if psutil.pid_exists(pid):
                return pid

            return None
        except (ValueError, FileNotFoundError):
            return None

    def get_process_info(self, pid: int) -> Optional[dict]:
        """Get process information.

        Args:
            pid: Process ID

        Returns:
            Process info dict or None
        """
        try:
            process = psutil.Process(pid)
            return {
                'cpu_percent': process.cpu_percent(),
                'memory_mb': process.memory_info().rss / (1024 * 1024),
                'threads': process.num_threads(),
                'status': process.status()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def create_status_panel(self) -> Panel:
        """Create status panel.

        Returns:
            Rich Panel
        """
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Key", style="dim")
        table.add_column("Value")

        # Uptime
        uptime = datetime.now() - self.state.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        table.add_row("Uptime", uptime_str)

        # PID and process info
        if self.state.pid:
            table.add_row("PID", str(self.state.pid))

            proc_info = self.get_process_info(self.state.pid)
            if proc_info:
                table.add_row("CPU", f"{proc_info['cpu_percent']:.1f}%")
                table.add_row("Memory", f"{proc_info['memory_mb']:.1f} MB")
                table.add_row("Status", proc_info['status'])
        else:
            table.add_row("Status", "[red]Not running[/red]")

        # Messages
        table.add_row("Messages", str(self.state.messages_count))
        table.add_row("Responses", str(self.state.responses_count))

        return Panel(table, title="[bold]Status[/bold]", border_style="cyan")

    def create_messages_panel(self) -> Panel:
        """Create recent messages panel.

        Returns:
            Rich Panel
        """
        if not self.state.recent_messages:
            content = Text("No recent messages", style="dim")
        else:
            lines = []
            for msg in list(self.state.recent_messages)[-10:]:
                lines.append(msg)
            content = "\n".join(lines)

        return Panel(content, title="[bold]Recent Messages[/bold]", border_style="blue")

    def create_responses_panel(self) -> Panel:
        """Create recent responses panel.

        Returns:
            Rich Panel
        """
        if not self.state.recent_responses:
            content = Text("No recent responses", style="dim")
        else:
            lines = []
            for resp in list(self.state.recent_responses)[-10:]:
                lines.append(resp)
            content = "\n".join(lines)

        return Panel(content, title="[bold]Bot Responses[/bold]", border_style="green")

    def create_decisions_panel(self) -> Panel:
        """Create decisions panel.

        Returns:
            Rich Panel
        """
        if not self.state.recent_decisions:
            content = Text("No recent decisions", style="dim")
        else:
            lines = []
            for decision in list(self.state.recent_decisions)[-10:]:
                lines.append(decision)
            content = "\n".join(lines)

        return Panel(content, title="[bold]Decisions[/bold]", border_style="yellow")

    def create_logs_panel(self) -> Panel:
        """Create logs panel.

        Returns:
            Rich Panel
        """
        if not self.state.recent_logs:
            content = Text("No recent logs", style="dim")
        else:
            lines = []
            for log_entry in list(self.state.recent_logs)[-15:]:
                formatted = LogViewer.format_entry(log_entry, show_logger=False)
                lines.append(formatted)
            content = "\n".join(lines)

        return Panel(content, title="[bold]Logs[/bold]", border_style="magenta")

    def create_layout(self) -> Layout:
        """Create monitor layout.

        Returns:
            Rich Layout
        """
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=10),
            Layout(name="body"),
            Layout(name="footer", size=18)
        )

        layout["header"].split_row(
            Layout(name="status"),
            Layout(name="messages")
        )

        layout["body"].split_row(
            Layout(name="responses"),
            Layout(name="decisions")
        )

        layout["footer"].update(self.create_logs_panel())

        layout["status"].update(self.create_status_panel())
        layout["messages"].update(self.create_messages_panel())
        layout["responses"].update(self.create_responses_panel())
        layout["decisions"].update(self.create_decisions_panel())

        return layout

    async def update_stats(self):
        """Update statistics from database."""
        try:
            general_stats = await self.stats_collector.get_general_stats()
            self.state.messages_count = general_stats.total_messages
            self.state.responses_count = general_stats.bot_messages
        except Exception:
            pass

    async def update_logs(self):
        """Update logs."""
        try:
            # Get recent logs
            entries = self.log_viewer.read_logs(lines=20, reverse=True)

            # Add new entries
            for entry in reversed(entries):
                if entry not in self.state.recent_logs:
                    self.state.recent_logs.append(entry)

                    # Parse special log types
                    if "📨 Message from" in entry.message:
                        self.state.recent_messages.append(f"{entry.timestamp.strftime('%H:%M:%S')} {entry.message}")

                    elif "📤 Sent response" in entry.message:
                        self.state.recent_responses.append(f"{entry.timestamp.strftime('%H:%M:%S')} {entry.message}")

                    elif "DecisionEngine" in entry.message or "🎲" in entry.message:
                        self.state.recent_decisions.append(f"{entry.timestamp.strftime('%H:%M:%S')} {entry.message}")

        except Exception:
            pass

    async def run(self):
        """Run monitor loop."""
        self._running = True

        with Live(self.create_layout(), console=self.console, refresh_per_second=1) as live:
            while self._running:
                try:
                    # Update PID
                    self.state.pid = self.get_bot_pid()

                    # Update stats and logs
                    await self.update_stats()
                    await self.update_logs()

                    # Update display
                    live.update(self.create_layout())

                    await asyncio.sleep(self.update_interval)

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")
                    await asyncio.sleep(self.update_interval)

    def stop(self):
        """Stop monitor."""
        self._running = False

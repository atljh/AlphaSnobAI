import asyncio
import time
from datetime import datetime, timedelta
from collections import deque
from threading import Thread
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Console
from rich import box

console = Console()


class InteractiveSession:
    def __init__(self):
        self.layout = Layout()
        self.logs = deque(maxlen=50)
        self.stats = {
            'messages_processed': 0,
            'responses_sent': 0,
            'start_time': datetime.now(),
            'last_activity': None
        }
        self.running = True

        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )

        self.layout["main"].split_row(
            Layout(name="stats", ratio=1),
            Layout(name="logs", ratio=2)
        )

    def add_log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {
            "INFO": "🤖",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "DEBUG": "🔍"
        }
        icon = icons.get(level, "•")
        self.logs.append(f"[dim]{timestamp}[/dim] {icon} {message}")

    def increment_messages(self):
        self.stats['messages_processed'] += 1
        self.stats['last_activity'] = datetime.now()

    def increment_responses(self):
        self.stats['responses_sent'] += 1

    def make_header(self) -> Panel:
        header = Text()
        header.append("🎭 AlphaSnob AI - Interactive Mode", style="bold magenta")
        header.append(" | ", style="dim")
        header.append("Press ", style="dim")
        header.append("Q", style="bold red")
        header.append(" to quit, ", style="dim")
        header.append("R", style="bold yellow")
        header.append(" to restart", style="dim")
        return Panel(header, border_style="cyan")

    def make_stats(self) -> Panel:
        uptime = datetime.now() - self.stats['start_time']
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        rate = (
            self.stats['responses_sent'] / self.stats['messages_processed'] * 100
            if self.stats['messages_processed'] > 0
            else 0
        )

        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", justify="right")
        table.add_column(style="white")

        table.add_row("Status:", "🟢 Running")
        table.add_row("Uptime:", f"{hours}h {minutes}m {seconds}s")
        table.add_row("Messages:", str(self.stats['messages_processed']))
        table.add_row("Responses:", str(self.stats['responses_sent']))
        table.add_row("Rate:", f"{rate:.1f}%")

        if self.stats['last_activity']:
            elapsed = (datetime.now() - self.stats['last_activity']).seconds
            table.add_row("Last activity:", f"{elapsed}s ago")

        return Panel(table, title="📊 Statistics", border_style="green", box=box.ROUNDED)

    def make_logs(self) -> Panel:
        if not self.logs:
            log_text = Text("Waiting for logs...", style="dim")
        else:
            log_text = Text("\n".join(list(self.logs)[-25:]))

        return Panel(
            log_text,
            title="📝 Live Logs",
            border_style="blue",
            box=box.ROUNDED
        )

    def make_footer(self) -> Panel:
        footer = Text()
        footer.append("Commands: ", style="dim")
        footer.append("Q", style="bold red")
        footer.append("=Quit  ", style="dim")
        footer.append("R", style="bold yellow")
        footer.append("=Restart  ", style="dim")
        footer.append("C", style="bold cyan")
        footer.append("=Clear  ", style="dim")
        footer.append("S", style="bold green")
        footer.append("=Stats", style="dim")
        return Panel(footer, border_style="dim")

    def update_layout(self):
        self.layout["header"].update(self.make_header())
        self.layout["stats"].update(self.make_stats())
        self.layout["logs"].update(self.make_logs())
        self.layout["footer"].update(self.make_footer())

    def get_layout(self):
        self.update_layout()
        return self.layout


session = InteractiveSession()


def get_session():
    return session

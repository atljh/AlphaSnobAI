from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box

console = Console()


def print_banner():
    banner = Text()
    banner.append("\n")
    banner.append("╔═══════════════════════════════════════════════════════════╗\n", style="bold cyan")
    banner.append("║                                                           ║\n", style="bold cyan")
    banner.append("║              ", style="bold cyan")
    banner.append("🎭 ALPHASNOB AI USERBOT 🎭", style="bold magenta")
    banner.append("                   ║\n", style="bold cyan")
    banner.append("║                                                           ║\n", style="bold cyan")
    banner.append("║  ", style="bold cyan")
    banner.append("Элитарный эстет-псих с AI-интеллектом", style="bold white")
    banner.append("                   ║\n", style="bold cyan")
    banner.append("║  ", style="bold cyan")
    banner.append("Стиль: Бордовый треш × American Psycho × Гиперболы", style="bold yellow")
    banner.append("      ║\n", style="bold cyan")
    banner.append("║                                                           ║\n", style="bold cyan")
    banner.append("╚═══════════════════════════════════════════════════════════╝\n", style="bold cyan")
    console.print(banner)


def create_status_panel(
    status: str,
    pid: Optional[int] = None,
    uptime: Optional[timedelta] = None,
    messages_processed: int = 0,
    responses_sent: int = 0,
    last_activity: Optional[str] = None
) -> Panel:
    """Create status panel.

    Args:
        status: Bot status ("running", "stopped", "error")
        pid: Process ID
        uptime: Bot uptime
        messages_processed: Total messages processed
        responses_sent: Total responses sent
        last_activity: Last activity timestamp

    Returns:
        Rich Panel with status information
    """
    status_icons = {
        "running": "🟢 Running",
        "stopped": "🔴 Stopped",
        "error": "🟡 Error",
        "starting": "🔵 Starting...",
    }
    status_text = status_icons.get(status, status)

    response_rate = (responses_sent / messages_processed * 100) if messages_processed > 0 else 0

    content = Text()
    content.append(f"Status: {status_text}\n", style="bold")

    if pid:
        content.append(f"PID: {pid}\n")

    if uptime:
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        content.append(f"Uptime: {hours}h {minutes}m {seconds}s\n", style="cyan")

    content.append(f"Messages processed: {messages_processed}\n")
    content.append(f"Responses sent: {responses_sent} ({response_rate:.1f}%)\n", style="green")

    if last_activity:
        content.append(f"Last activity: {last_activity}\n", style="dim")

    return Panel(
        content,
        title="🎭 AlphaSnob Status",
        border_style="cyan",
        box=box.ROUNDED
    )


def create_stats_table(stats: List[Dict[str, Any]]) -> Table:
    table = Table(
        title="📊 Chat Statistics",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("Chat ID", style="dim", width=20)
    table.add_column("Messages", justify="right", style="cyan")
    table.add_column("Responses", justify="right", style="green")
    table.add_column("Rate", justify="right", style="yellow")

    for stat in stats:
        chat_id = str(stat.get('chat_id', 'Unknown'))
        messages = stat.get('messages', 0)
        responses = stat.get('responses', 0)
        rate = stat.get('rate', 0)

        if len(chat_id) > 18:
            chat_id = chat_id[:15] + "..."

        table.add_row(
            chat_id,
            str(messages),
            str(responses),
            f"{rate:.1f}%"
        )

    return table


def create_config_panel(config_dict: Dict[str, Any]) -> Panel:
    content = Text()

    if 'telegram' in config_dict:
        tg = config_dict['telegram']
        content.append("📱 Telegram\n", style="bold cyan")
        content.append(f"  Session: {tg.get('session_name', 'N/A')}\n")
        content.append(f"  API ID: {tg.get('api_id', 'N/A')}\n")
        content.append("\n")

    if 'llm' in config_dict:
        llm = config_dict['llm']
        content.append("🤖 LLM\n", style="bold cyan")
        content.append(f"  Provider: {llm.get('provider', 'N/A')}\n")
        content.append(f"  Model: {llm.get('model', 'N/A')}\n")
        content.append(f"  Temperature: {llm.get('temperature', 'N/A')}\n")
        content.append(f"  Max Tokens: {llm.get('max_tokens', 'N/A')}\n")
        content.append("\n")

    if 'bot' in config_dict:
        bot = config_dict['bot']
        content.append("⚙️  Bot\n", style="bold cyan")
        content.append(f"  Response Mode: {bot.get('response_mode', 'N/A')}\n")
        if bot.get('response_mode') == 'probability':
            content.append(f"  Probability: {bot.get('response_probability', 'N/A')}\n")
        content.append(f"  Context Length: {bot.get('context_length', 'N/A')}\n")

    return Panel(
        content,
        title="⚙️  Configuration",
        border_style="yellow",
        box=box.ROUNDED
    )


def create_message_log_table(messages: List[Dict[str, str]]) -> Table:
    table = Table(
        title="💬 Recent Messages",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("Time", style="dim", width=8)
    table.add_column("User", style="cyan", width=15)
    table.add_column("Message", style="white")

    for msg in messages[-20:]:  # Last 20 messages
        time_str = msg.get('timestamp', '')[:8]  # HH:MM:SS
        username = msg.get('username', 'Unknown')
        text = msg.get('text', '')

        # Truncate long messages
        if len(text) > 60:
            text = text[:57] + "..."

        # Truncate long usernames
        if len(username) > 13:
            username = username[:10] + "..."

        table.add_row(time_str, username, text)

    return table


def get_progress_bar() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    )


def show_warning(message: str):
    console.print(f"⚠️  [yellow]{message}[/yellow]")


def show_error(message: str):
    console.print(f"❌ [bold red]{message}[/bold red]")


def show_success(message: str):
    console.print(f"✅ [bold green]{message}[/bold green]")


def show_info(message: str):
    console.print(f"🤖 [cyan]{message}[/cyan]")


def create_live_status_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="status", size=10),
        Layout(name="logs", ratio=1)
    )

    return layout


def format_uptime(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

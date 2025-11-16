import logging
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

ALPHASNOB_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "critical": "bold white on red",
    "success": "bold green",
    "debug": "dim cyan",
})

LOG_ICONS = {
    "DEBUG": "🔍",
    "INFO": "🤖",
    "WARNING": "⚠️ ",
    "ERROR": "❌",
    "CRITICAL": "🚨",
    "SUCCESS": "✅",
}


class RichLogger:

    def __init__(
        self,
        name: str = "alphasnob",
        level: str = "INFO",
        log_file: Optional[Path] = None,
        show_time: bool = True,
        show_path: bool = False
    ):
        """Initialize rich logger.

        Args:
            name: Logger name
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for file logging
            show_time: Show timestamps in logs
            show_path: Show file paths in logs
        """
        self.console = Console(theme=ALPHASNOB_THEME)
        self.name = name
        self.level = getattr(logging, level.upper())
        self.log_file = log_file

        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        self.logger.handlers.clear()

        console_handler = RichHandler(
            console=self.console,
            show_time=show_time,
            show_path=show_path,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )
        console_handler.setLevel(self.level)
        self.logger.addHandler(console_handler)

        if log_file:
            log_file.parent.mkdir(exist_ok=True, parents=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(self.level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def _format_message(self, message: str, level: str) -> str:
        icon = LOG_ICONS.get(level, "")
        return f"{icon} {message}" if icon else message

    def debug(self, message: str, *args, **kwargs):
        self.logger.debug(self._format_message(message, "DEBUG"), *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        self.logger.info(self._format_message(message, "INFO"), *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self.logger.warning(self._format_message(message, "WARNING"), *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        self.logger.error(self._format_message(message, "ERROR"), *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        self.logger.critical(self._format_message(message, "CRITICAL"), *args, **kwargs)

    def success(self, message: str, *args, **kwargs):
        self.logger.info(
            f"[success]{self._format_message(message, 'SUCCESS')}[/success]",
            *args,
            extra={"markup": True},
            **kwargs
        )

    def exception(self, message: str, *args, **kwargs):
        self.logger.exception(self._format_message(message, "ERROR"), *args, **kwargs)


def setup_rich_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    show_time: bool = True,
    show_path: bool = False
) -> RichLogger:
    return RichLogger(
        name="alphasnob",
        level=level,
        log_file=log_file,
        show_time=show_time,
        show_path=show_path
    )


_global_logger: Optional[RichLogger] = None


def get_logger() -> RichLogger:
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_rich_logging()
    return _global_logger

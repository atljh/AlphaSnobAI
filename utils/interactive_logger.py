import logging
from typing import Optional


class InteractiveHandler(logging.Handler):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname
            self.session.add_log(level, msg)
        except Exception:
            self.handleError(record)


def setup_interactive_logging(session):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = InteractiveHandler(session)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)

    return logger

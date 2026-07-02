#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   logging linuxgram!   #
##########################

import logging
import os
from pathlib import Path

from .constants import LOG_FILE, LOGS_DIR, TRACE_LEVEL


def _logger_trace(self, message, *args, **kwargs):
    if self.isEnabledFor(TRACE_LEVEL):
        self._log(TRACE_LEVEL, message, args, **kwargs)


logging.addLevelName(TRACE_LEVEL, 'TRACE')
logging.Logger.trace = _logger_trace
logger = logging.getLogger('linuxgram')


def configure_logging(logs_dir: str = LOGS_DIR, log_file: str = LOG_FILE) -> None:
    """Configure application logging to the LinuxGram log file."""
    os.makedirs(logs_dir, mode=0o700, exist_ok=True)
    try:
        os.chmod(logs_dir, 0o700)
        Path(log_file).touch(mode=0o600, exist_ok=True)
        os.chmod(log_file, 0o600)
    except OSError:
        pass

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    root_logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(TRACE_LEVEL)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    ))
    root_logger.addHandler(file_handler)

    logger.setLevel(TRACE_LEVEL)
    for noisy_logger in ('asyncio', 'telethon', 'urwid'):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    logger.info('Logging started: %s', log_file)


class LoggingConfig:
    """Compatibility wrapper for logging setup during migration."""

    logger = logger
    configure_logging = staticmethod(configure_logging)


__all__ = ['TRACE_LEVEL', 'logger', 'configure_logging', 'LoggingConfig']

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from .settings import settings


class Logger:
    def __init__(self):
        self.logger = logging.getLogger(settings.APP_NAME)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        self.logger.setLevel(logging.DEBUG)

        # Create logs directory
        os.makedirs("logs", exist_ok=True)

        formatter = logging.Formatter(
            fmt=(
                "%(asctime)s | %(levelname)s | "
                "%(name)s | %(filename)s:%(lineno)d | %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        #
        # Console Handler
        #
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)

        #
        # App File Handler
        #
        file_handler = RotatingFileHandler(
            filename="logs/app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        #
        # Error File Handler
        #
        error_handler = RotatingFileHandler(
            filename="logs/error.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)

        self.logger.propagate = False

    def _build_extra(self, level: str):
        return {
            "elastic_fields": {
                "version": f"python version: {repr(sys.version_info)}",
                "level": level,
            }
        }

    def debug(self, msg: str):
        self.logger.debug(
            msg,
            extra=self._build_extra("DEBUG"),
        )

    def info(self, msg: str):
        self.logger.info(
            msg,
            extra=self._build_extra("INFO"),
        )

    def warning(self, msg: str):
        self.logger.warning(
            msg,
            extra=self._build_extra("WARNING"),
        )

    def error(self, msg: str):
        self.logger.error(
            msg,
            extra=self._build_extra("ERROR"),
        )

    def exception(self, msg: str):
        self.logger.exception(
            msg,
            extra=self._build_extra("EXCEPTION"),
        )

    def fatal(self, msg: str):
        self.logger.critical(
            msg,
            extra=self._build_extra("FATAL"),
        )


log = Logger()
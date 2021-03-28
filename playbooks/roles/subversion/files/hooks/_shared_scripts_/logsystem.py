#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys
from logging.handlers import RotatingFileHandler
from logging import StreamHandler


class Logging:
    """Logsystem simplified class."""

    # https://docs.python.org/3/library/logging.html#logging.Formatter
    default_formatter = "%(asctime)s - %(levelname)s - %(message)s"
    default_level = "ERROR"

    def __init__(self, name="Some service name"):
        """Init."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

    def __get_debug_level(self, level=""):
        levels = {"debug": logging.DEBUG,
                  "info": logging.INFO,
                  "warning": logging.WARNING,
                  "warn": logging.WARNING,
                  "error": logging.ERROR,
                  "critical": logging.CRITICAL,
                  "fatal": logging.FATAL}
        return levels.get(level.lower(), None)

    def debug(self, msg):
        """Send debug message."""
        self.logger.debug(msg)

    def info(self, msg):
        """Send info message."""
        self.logger.info(msg)

    def warn(self, msg):
        """Send warn message."""
        self.logger.warn(msg)

    def error(self, msg):
        """Send error message."""
        self.logger.error(msg)

    def critical(self, msg):
        """Send critical message."""
        self.logger.critical(msg)

    def fatal(self, msg):
        """Send fatal aka critical message."""
        self.logger.fatal(msg)

    def enable_console(self, formatter=default_formatter,
                            level=default_level):
        """Console handler."""
        h = StreamHandler(sys.stderr)
        h.setFormatter(logging.Formatter(formatter))
        h.setLevel(self.__get_debug_level(level))
        self.logger.addHandler(h)

    def enable_file(self, logfile=None,
                         formatter=default_formatter,
                         level=default_level,
                         maxbytes=0,
                         backupcount=0):
        """File handler."""
        h = RotatingFileHandler(logfile, maxBytes=maxbytes, backupCount=backupcount, encoding="utf-8")
        h.setFormatter(logging.Formatter(formatter))
        h.setLevel(self.__get_debug_level(level))
        self.logger.addHandler(h)

    def close(self):
        """Close all handlers."""
        for h in self.logger.handlers:
            h.close()
            self.logger.removeFilter(h)

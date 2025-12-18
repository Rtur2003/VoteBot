"""Logging configuration module for VOTRYX."""

import logging
import tempfile
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Tuple


class LoggingManager:
    """Manages logging configuration and file handling."""

    def __init__(self, base_dir: Path, log_path: Optional[str] = None):
        self.base_dir = base_dir
        self.log_path = log_path or "logs"
        self.log_dir, self.warning = self._resolve_logs_dir()
        self.logger = self._build_logger()

    def _resolve_logs_dir(self) -> Tuple[Path, Optional[str]]:
        """Resolve and create logging directory."""
        path = Path(self.log_path)
        if not path.is_absolute():
            path = self.base_dir / path

        try:
            path.mkdir(parents=True, exist_ok=True)
            return path, None
        except Exception as exc:
            fallback = Path(tempfile.mkdtemp(prefix="votryx-logs-"))
            warning = (
                f"Log klasoru '{path}' olusturulamadi ({exc}); "
                f"gecici '{fallback}' kullaniliyor."
            )
            return fallback, warning

    def _build_logger(self) -> logging.Logger:
        """Configure and return application logger."""
        logger = logging.getLogger("Votryx")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        file_handler = RotatingFileHandler(
            self.log_dir / "votryx.log",
            encoding="utf-8",
            maxBytes=512 * 1024,
            backupCount=3,
        )
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def get_logger(self) -> logging.Logger:
        """Return configured logger instance."""
        return self.logger

    def get_log_dir(self) -> Path:
        """Return log directory path."""
        return self.log_dir

    def get_warning(self) -> Optional[str]:
        """Return warning message if log directory fallback occurred."""
        return self.warning

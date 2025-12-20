"""Configuration management module for VOTRYX."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List


class ConfigurationManager:
    """Manages application configuration with validation and persistence."""

    DEFAULT_CONFIG = {
        "paths": {},
        "target_url": "https://distrokid.com/spotlight/hasanarthuraltunta/vote/",
        "pause_between_votes": 3,
        "batch_size": 1,
        "max_errors": 3,
        "parallel_workers": 2,
        "headless": True,
        "timeout_seconds": 15,
        "use_selenium_manager": False,
        "use_random_user_agent": True,
        "block_images": True,
        "user_agents": [],
        "vote_selectors": [],
        "backoff_seconds": 5,
        "backoff_cap_seconds": 60,
    }

    def __init__(self, base_dir: Path, code_dir: Path):
        """Initialize configuration manager.

        Args:
            base_dir: Base repository directory path
            code_dir: Code directory path
        """
        self.base_dir = base_dir
        self.code_dir = code_dir
        self.ignored_config_paths: List[Path] = []
        self.config_path = self._find_config_path()
        self.config = self._load_config()

    def _find_config_path(self) -> Path:
        """Locate configuration file from candidate paths."""
        candidates = [
            self.base_dir / "config.json",
            self.code_dir / "config.json",
        ]
        existing = [path for path in candidates if path.exists()]
        if existing:
            selected = existing[0]
            self.ignored_config_paths = [path for path in existing[1:] if path != selected]
            return selected
        return candidates[0]

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file with defaults fallback."""
        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                merged = {**self.DEFAULT_CONFIG, **data}
                default_paths: Dict[str, Any] = self.DEFAULT_CONFIG.get("paths", {})  # type: ignore[assignment]
                data_paths: Dict[str, Any] = data.get("paths", {})
                merged["paths"] = {**default_paths, **data_paths}
                return merged
        except Exception:
            return dict(self.DEFAULT_CONFIG)

    def save(self) -> None:
        """Persist configuration to disk with atomic write."""
        target_dir = self.config_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix="config-", suffix=".json", dir=target_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
                json.dump(self.config, temp_file, ensure_ascii=False, indent=4)
            Path(temp_path).replace(self.config_path)
        except Exception:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.config[key] = value

    def get_paths(self) -> Dict[str, str]:
        """Get paths configuration."""
        paths = self.config.get("paths", {})
        if not isinstance(paths, dict):
            return {}
        return {k: str(v) for k, v in paths.items()}

    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        self.config.update(updates)

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.config = dict(self.DEFAULT_CONFIG)

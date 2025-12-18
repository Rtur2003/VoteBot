"""Unit tests for configuration management module."""

import json
import tempfile
from pathlib import Path

import pytest

from Code_EXE.Votryx.core.config import ConfigurationManager


class TestConfigurationManager:
    """Test suite for ConfigurationManager."""

    def test_default_config_loaded_when_file_missing(self):
        """Test that default configuration is loaded when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            code_dir = base_dir / "code"
            code_dir.mkdir()

            manager = ConfigurationManager(base_dir, code_dir)

            assert manager.config is not None
            assert manager.get("target_url") is not None
            assert manager.get("batch_size") == 1
            assert manager.get("headless") is True

    def test_config_loaded_from_file(self):
        """Test that configuration is loaded from existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            code_dir = base_dir / "code"
            code_dir.mkdir()

            config_path = base_dir / "config.json"
            test_config = {
                "target_url": "https://example.com/vote",
                "batch_size": 5,
                "headless": False,
            }

            with open(config_path, "w") as f:
                json.dump(test_config, f)

            manager = ConfigurationManager(base_dir, code_dir)

            assert manager.get("target_url") == "https://example.com/vote"
            assert manager.get("batch_size") == 5
            assert manager.get("headless") is False

    def test_config_save(self):
        """Test that configuration can be saved to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            code_dir = base_dir / "code"
            code_dir.mkdir()

            manager = ConfigurationManager(base_dir, code_dir)
            manager.set("batch_size", 10)
            manager.save()

            config_path = manager.config_path
            assert config_path.exists()

            with open(config_path, "r") as f:
                loaded = json.load(f)
                assert loaded["batch_size"] == 10

    def test_get_and_set_operations(self):
        """Test get and set configuration operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            code_dir = base_dir / "code"
            code_dir.mkdir()

            manager = ConfigurationManager(base_dir, code_dir)

            manager.set("test_key", "test_value")
            assert manager.get("test_key") == "test_value"
            assert manager.get("nonexistent_key") is None
            assert manager.get("nonexistent_key", "default") == "default"

    def test_update_multiple_values(self):
        """Test updating multiple configuration values at once."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            code_dir = base_dir / "code"
            code_dir.mkdir()

            manager = ConfigurationManager(base_dir, code_dir)

            updates = {"batch_size": 3, "headless": False, "max_errors": 5}
            manager.update(updates)

            assert manager.get("batch_size") == 3
            assert manager.get("headless") is False
            assert manager.get("max_errors") == 5

    def test_reset_to_defaults(self):
        """Test resetting configuration to default values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            code_dir = base_dir / "code"
            code_dir.mkdir()

            manager = ConfigurationManager(base_dir, code_dir)

            manager.set("batch_size", 100)
            manager.reset_to_defaults()

            assert manager.get("batch_size") == 1
            assert manager.get("headless") is True

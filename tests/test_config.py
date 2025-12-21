"""Unit tests for configuration management module."""

import json
import tempfile
from pathlib import Path

from Code_EXE.Votryx.core.config import ConfigurationManager


class TestConfigurationManager:
    """Test suite for ConfigurationManager."""

    def test_multiple_config_files_tracks_ignored_paths(self):
        """Track ignored config paths when multiple candidates exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            code_dir = base_dir / "code"
            code_dir.mkdir()

            base_config_path = base_dir / "config.json"
            code_config_path = code_dir / "config.json"

            with open(base_config_path, "w") as f:
                json.dump({"batch_size": 2}, f)
            with open(code_config_path, "w") as f:
                json.dump({"batch_size": 3}, f)

            manager = ConfigurationManager(base_dir, code_dir)

            assert manager.config_path == base_config_path
            assert manager.ignored_config_paths == [code_config_path]

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

    def test_config_with_malformed_json(self):
        """Test configuration with malformed JSON falls back to defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            code_dir = base_dir / "code"
            code_dir.mkdir()

            config_path = base_dir / "config.json"
            with open(config_path, "w") as f:
                f.write("{invalid json}")

            manager = ConfigurationManager(base_dir, code_dir)

            # Should fall back to defaults
            assert manager.get("batch_size") == 1
            assert manager.get("headless") is True

    def test_config_with_partial_data(self):
        """Test configuration with partial data merges with defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            code_dir = base_dir / "code"
            code_dir.mkdir()

            config_path = base_dir / "config.json"
            # Only set one value
            with open(config_path, "w") as f:
                json.dump({"batch_size": 7}, f)

            manager = ConfigurationManager(base_dir, code_dir)

            # Custom value should be present
            assert manager.get("batch_size") == 7
            # Default values should still be available
            assert manager.get("headless") is True
            assert manager.get("target_url") is not None

    def test_config_save_creates_directory(self):
        """Test that save creates parent directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            code_dir = base_dir / "code"
            code_dir.mkdir()

            # Create nested path
            nested_config = base_dir / "nested" / "config.json"

            manager = ConfigurationManager(base_dir, code_dir)
            manager.config_path = nested_config
            manager.set("batch_size", 5)
            manager.save()

            assert nested_config.exists()
            assert nested_config.parent.exists()

    def test_get_paths_with_invalid_type(self):
        """Test get_paths with invalid paths configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            code_dir = base_dir / "code"
            code_dir.mkdir()

            manager = ConfigurationManager(base_dir, code_dir)

            # Set paths to invalid type
            manager.config["paths"] = "not a dict"
            paths = manager.get_paths()

            # Should return empty dict
            assert paths == {}

    def test_update_with_nested_paths(self):
        """Test updating with nested paths structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            code_dir = base_dir / "code"
            code_dir.mkdir()

            manager = ConfigurationManager(base_dir, code_dir)

            updates = {
                "batch_size": 5,
                "paths": {"chrome": "/usr/bin/chrome", "driver": "/usr/bin/chromedriver"},
            }
            manager.update(updates)

            assert manager.get("batch_size") == 5
            assert manager.get("paths")["chrome"] == "/usr/bin/chrome"

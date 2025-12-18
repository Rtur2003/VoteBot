"""Unit tests for validation module."""

import tempfile
from pathlib import Path

import pytest

from Code_EXE.Votryx.core.validation import InputValidator, ValidationError


class TestInputValidator:
    """Test suite for InputValidator."""

    def test_validate_url_valid(self):
        """Test URL validation with valid URLs."""
        valid, error = InputValidator.validate_url("https://example.com")
        assert valid is True
        assert error is None

        valid, error = InputValidator.validate_url("http://example.com/path")
        assert valid is True
        assert error is None

    def test_validate_url_invalid(self):
        """Test URL validation with invalid URLs."""
        valid, error = InputValidator.validate_url("")
        assert valid is False
        assert error is not None

        valid, error = InputValidator.validate_url("not-a-url")
        assert valid is False
        assert error is not None

        valid, error = InputValidator.validate_url("ftp://example.com")
        assert valid is False
        assert error is not None

    def test_validate_positive_number(self):
        """Test positive number validation."""
        valid, error = InputValidator.validate_positive_number(5.0, "test")
        assert valid is True
        assert error is None

        valid, error = InputValidator.validate_positive_number(0.0, "test")
        assert valid is False
        assert error is not None

        valid, error = InputValidator.validate_positive_number(-1.0, "test")
        assert valid is False
        assert error is not None

        valid, error = InputValidator.validate_positive_number("not_a_number", "test")
        assert valid is False
        assert error is not None

    def test_validate_integer_range(self):
        """Test integer range validation."""
        valid, error = InputValidator.validate_integer_range(5, "test", 1, 10)
        assert valid is True
        assert error is None

        valid, error = InputValidator.validate_integer_range(0, "test", 1, 10)
        assert valid is False
        assert error is not None

        valid, error = InputValidator.validate_integer_range(11, "test", 1, 10)
        assert valid is False
        assert error is not None

        valid, error = InputValidator.validate_integer_range("not_int", "test", 1, 10)
        assert valid is False
        assert error is not None

    def test_validate_path_exists(self):
        """Test path existence validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing_path = Path(tmpdir) / "test.txt"
            existing_path.touch()

            valid, error = InputValidator.validate_path_exists(existing_path, "test")
            assert valid is True
            assert error is None

            nonexistent_path = Path(tmpdir) / "nonexistent.txt"
            valid, error = InputValidator.validate_path_exists(nonexistent_path, "test")
            assert valid is False
            assert error is not None

    def test_validate_backoff_values(self):
        """Test backoff values validation."""
        valid, error = InputValidator.validate_backoff_values(5.0, 60.0)
        assert valid is True
        assert error is None

        valid, error = InputValidator.validate_backoff_values(0.0, 60.0)
        assert valid is False
        assert error is not None

        valid, error = InputValidator.validate_backoff_values(5.0, 0.0)
        assert valid is False
        assert error is not None

        valid, error = InputValidator.validate_backoff_values(60.0, 5.0)
        assert valid is False
        assert error is not None

    def test_normalize_user_agents(self):
        """Test user agent normalization."""
        agents = [
            "Valid User Agent 1",
            "Valid User Agent 2",
            "short",  # Too short
            "Valid User Agent 1",  # Duplicate
            123,  # Not a string
            "Valid User Agent 3",
        ]

        normalized = InputValidator.normalize_user_agents(agents)

        assert len(normalized) == 3
        assert "Valid User Agent 1" in normalized
        assert "Valid User Agent 2" in normalized
        assert "Valid User Agent 3" in normalized
        assert "short" not in normalized

    def test_normalize_user_agents_empty(self):
        """Test user agent normalization with empty list."""
        normalized = InputValidator.normalize_user_agents([])
        assert normalized == []

        normalized = InputValidator.normalize_user_agents(None)
        assert normalized == []

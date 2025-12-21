"""Unit tests for validation module."""

import tempfile
from pathlib import Path

from Code_EXE.Votryx.core.validation import InputValidator


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

    def test_validate_url_strips_whitespace(self):
        """Test URL validation trims whitespace."""
        valid, error = InputValidator.validate_url("  https://example.com  ")
        assert valid is True
        assert error is None

    def test_validate_url_whitespace_only(self):
        """Test URL validation with whitespace-only string."""
        valid, error = InputValidator.validate_url("   ")
        assert valid is False
        assert error == "URL cannot be empty"

        valid, error = InputValidator.validate_url("\t\n  ")
        assert valid is False
        assert error == "URL cannot be empty"

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

    def test_validate_url_missing_domain(self):
        """Test URL validation when domain is missing."""
        valid, error = InputValidator.validate_url("https://")
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

    def test_validate_positive_number_min_value(self):
        """Test positive number validation with a custom minimum."""
        valid, error = InputValidator.validate_positive_number(5.0, "test", min_value=5.0)
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

    def test_validate_integer_range_bounds(self):
        """Test integer range boundaries."""
        valid, error = InputValidator.validate_integer_range(1, "test", 1, 10)
        assert valid is True
        assert error is None

        valid, error = InputValidator.validate_integer_range(10, "test", 1, 10)
        assert valid is True
        assert error is None

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

    def test_validate_path_exists_none(self):
        """Test path existence validation with missing path."""
        valid, error = InputValidator.validate_path_exists(None, "test")
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
        """Test user agent normalization with empty inputs."""
        normalized = InputValidator.normalize_user_agents([])
        assert normalized == []

        normalized = InputValidator.normalize_user_agents(None)
        assert normalized == []

    def test_validate_url_with_none(self):
        """Test URL validation with None input."""
        valid, error = InputValidator.validate_url(None)
        assert valid is False
        assert error is not None

    def test_validate_url_with_numeric(self):
        """Test URL validation with numeric input."""
        valid, error = InputValidator.validate_url(123)
        assert valid is False
        assert error is not None

    def test_validate_path_exists_with_string(self):
        """Test path validation with string input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing_path = Path(tmpdir) / "test.txt"
            existing_path.touch()

            # Test with string path
            valid, error = InputValidator.validate_path_exists(str(existing_path), "test")
            assert valid is True
            assert error is None

            # Test with non-existent string path
            valid, error = InputValidator.validate_path_exists(
                str(Path(tmpdir) / "nonexistent.txt"), "test"
            )
            assert valid is False
            assert error is not None

    def test_validate_path_exists_with_whitespace(self):
        """Test path validation with whitespace-only string."""
        valid, error = InputValidator.validate_path_exists("   ", "test")
        assert valid is False
        assert error == "test path is not specified"

        valid, error = InputValidator.validate_path_exists("\t\n", "test")
        assert valid is False
        assert error == "test path is not specified"

    def test_validate_path_exists_with_invalid_type(self):
        """Test path validation with invalid type."""
        valid, error = InputValidator.validate_path_exists(123, "test")
        assert valid is False
        assert error is not None

    def test_validate_positive_number_edge_cases(self):
        """Test positive number validation with edge cases."""
        # Test with zero when min_value is 0
        valid, error = InputValidator.validate_positive_number(0.0, "test", min_value=0.0)
        assert valid is False
        assert error is not None

        # Test with very small positive number
        valid, error = InputValidator.validate_positive_number(0.0001, "test")
        assert valid is True
        assert error is None

        # Test with None
        valid, error = InputValidator.validate_positive_number(None, "test")
        assert valid is False
        assert error is not None

    def test_validate_integer_range_edge_cases(self):
        """Test integer range validation edge cases."""
        # Test with float that's an integer
        valid, error = InputValidator.validate_integer_range(5.0, "test", 1, 10)
        assert valid is True
        assert error is None

        # Test with None
        valid, error = InputValidator.validate_integer_range(None, "test", 1, 10)
        assert valid is False
        assert error is not None

    def test_validate_backoff_values_edge_cases(self):
        """Test backoff validation with edge cases."""
        # Test with equal values
        valid, error = InputValidator.validate_backoff_values(5.0, 5.0)
        assert valid is True
        assert error is None

        # Test with very small difference
        valid, error = InputValidator.validate_backoff_values(5.0, 5.1)
        assert valid is True
        assert error is None

    def test_normalize_user_agents_whitespace(self):
        """Test user agent normalization with whitespace."""
        agents = [
            "  Valid User Agent 1  ",
            "\tValid User Agent 2\n",
            "Valid User Agent 3",
        ]
        normalized = InputValidator.normalize_user_agents(agents)
        assert len(normalized) == 3
        assert all(agent.strip() == agent for agent in normalized)

    def test_normalize_user_agents_case_sensitivity(self):
        """Test user agent normalization is case-insensitive for duplicates."""
        agents = ["User Agent One", "user agent one", "USER AGENT ONE"]
        normalized = InputValidator.normalize_user_agents(agents)
        # Should only keep one (case-insensitive deduplication)
        assert len(normalized) == 1

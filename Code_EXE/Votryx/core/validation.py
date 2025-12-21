"""Input validation module for VOTRYX."""

from pathlib import Path
from typing import Any, Optional, Tuple, Union
from urllib.parse import urlparse


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


class InputValidator:
    """Validates user inputs and configuration values."""

    @staticmethod
    def validate_url(url: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate URL format and scheme.

        Args:
            url: URL to validate (should be string, but accepts any type)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url or not isinstance(url, str):
            return False, "URL cannot be empty"

        url = url.strip()
        if not url:
            return False, "URL cannot be empty"

        if not url.startswith(("http://", "https://")):
            return False, "URL must start with http:// or https://"

        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return False, "URL must contain a valid domain"
            return True, None
        except Exception as e:
            return False, f"Invalid URL format: {e}"

    @staticmethod
    def validate_positive_number(
        value: Any, name: str, min_value: float = 0.0
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value is a positive number.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            num = float(value)
            if num <= min_value:
                return False, f"{name} must be greater than {min_value}"
            return True, None
        except (ValueError, TypeError):
            return False, f"{name} must be a valid number"

    @staticmethod
    def validate_integer_range(
        value: Any, name: str, min_val: int, max_val: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value is an integer within a range.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            num = int(value)
            if num < min_val or num > max_val:
                return False, f"{name} must be between {min_val} and {max_val}"
            return True, None
        except (ValueError, TypeError):
            return False, f"{name} must be a valid integer"

    @staticmethod
    def validate_path_exists(path: Union[str, Path, Any], name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a path exists.

        Args:
            path: Path to validate (can be string, Path, or other type)
            name: Name of the path for error messages

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not path:
            return False, f"{name} path is not specified"

        # Convert string to Path if necessary
        if isinstance(path, str):
            # Check for whitespace-only strings
            if not path.strip():
                return False, f"{name} path is not specified"
            path = Path(path)
        elif not isinstance(path, Path):
            return False, f"{name} must be a valid path"

        if not path.exists():
            return False, f"{name} not found at {path}"

        return True, None

    @staticmethod
    def validate_backoff_values(
        backoff_seconds: float, backoff_cap_seconds: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate backoff timing values.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if backoff_seconds <= 0:
            return False, "Backoff seconds must be greater than 0"

        if backoff_cap_seconds <= 0:
            return False, "Backoff cap seconds must be greater than 0"

        if backoff_cap_seconds < backoff_seconds:
            return (
                False,
                "Backoff cap cannot be less than initial backoff value",
            )

        return True, None

    @staticmethod
    def normalize_user_agents(agents: Optional[list]) -> list:
        """
        Normalize and deduplicate user agent strings.

        Args:
            agents: List of user agent strings (or None)

        Returns:
            List of cleaned user agent strings (minimum 10 chars, trimmed, deduplicated)

        Note:
            - Filters out non-string values
            - Removes strings shorter than 10 characters
            - Trims whitespace
            - Case-insensitive deduplication
        """
        cleaned = []
        seen = set()
        for ua in agents or []:
            if not isinstance(ua, str):
                continue
            stripped = ua.strip()
            if not stripped or len(stripped) < 10:
                continue
            if stripped.lower() in seen:
                continue
            seen.add(stripped.lower())
            cleaned.append(stripped)
        return cleaned

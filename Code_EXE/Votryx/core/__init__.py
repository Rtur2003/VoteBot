"""Core package - application business logic and services.

This package contains the core business logic separated from the UI layer.
Each module has a single, well-defined responsibility.

Architecture:
- browser_manager: WebDriver lifecycle management
- config: Configuration loading and persistence  
- driver: WebDriver factory and options
- i18n: Internationalized UI strings
- logging_manager: File-based logging
- state_manager: Application state with observer pattern
- validation: Input validation utilities
- voting_engine: Core voting business logic
"""

from .browser_manager import BrowserLifecycleManager
from .config import ConfigurationManager
from .driver import DriverManager
from .i18n import UIStrings
from .logging_manager import LoggingManager
from .state_manager import LogEntry, LogHistory, StateManager, VotingStatistics
from .validation import InputValidator, ValidationError
from .voting_engine import VotingEngine, VotingSession

__all__ = [
    "BrowserLifecycleManager",
    "ConfigurationManager",
    "DriverManager",
    "UIStrings",
    "LoggingManager",
    "StateManager",
    "VotingStatistics",
    "LogEntry",
    "LogHistory",
    "InputValidator",
    "ValidationError",
    "VotingEngine",
    "VotingSession",
]

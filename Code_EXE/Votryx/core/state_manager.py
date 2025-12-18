"""State management module - centralized application state."""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List, Optional, Tuple


@dataclass
class VotingStatistics:
    """Immutable voting statistics snapshot."""

    vote_count: int = 0
    error_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    start_time: Optional[float] = None
    is_running: bool = False

    def with_vote(self) -> "VotingStatistics":
        """Return new state with incremented vote count."""
        return VotingStatistics(
            vote_count=self.vote_count + 1,
            error_count=self.error_count,
            success_count=self.success_count + 1,
            failure_count=self.failure_count,
            start_time=self.start_time,
            is_running=self.is_running,
        )

    def with_error(self) -> "VotingStatistics":
        """Return new state with incremented error count."""
        return VotingStatistics(
            vote_count=self.vote_count,
            error_count=self.error_count + 1,
            success_count=self.success_count,
            failure_count=self.failure_count + 1,
            start_time=self.start_time,
            is_running=self.is_running,
        )

    def with_running(self, running: bool) -> "VotingStatistics":
        """Return new state with updated running status."""
        new_start = self.start_time
        if running and not self.is_running:
            new_start = time.time()
        elif not running and self.is_running:
            new_start = None

        return VotingStatistics(
            vote_count=self.vote_count,
            error_count=self.error_count,
            success_count=self.success_count,
            failure_count=self.failure_count,
            start_time=new_start,
            is_running=running,
        )

    def reset_counters(self) -> "VotingStatistics":
        """Return new state with reset counters."""
        return VotingStatistics(
            vote_count=0,
            error_count=0,
            success_count=0,
            failure_count=0,
            start_time=None,
            is_running=False,
        )

    def get_runtime_formatted(self) -> str:
        """Get formatted runtime string."""
        if not self.start_time or not self.is_running:
            return "00:00:00"

        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@dataclass
class LogEntry:
    """Represents a single log entry."""

    timestamp: str
    level: str
    message: str


class LogHistory:
    """Manages log entry history with size limit."""

    def __init__(self, max_entries: int = 500):
        self.max_entries = max_entries
        self._entries: List[LogEntry] = []

    def add(self, level: str, message: str) -> None:
        """Add new log entry."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = LogEntry(timestamp=timestamp, level=level, message=message)
        self._entries.append(entry)

        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries :]

    def get_all(self) -> List[LogEntry]:
        """Get all log entries."""
        return list(self._entries)

    def get_errors_only(self) -> List[LogEntry]:
        """Get only error entries."""
        return [e for e in self._entries if e.level == "error"]

    def clear(self) -> None:
        """Clear all log entries."""
        self._entries.clear()


class StateManager:
    """Manages application state with observer pattern."""

    def __init__(self):
        self._stats = VotingStatistics()
        self._log_history = LogHistory()
        self._observers: List[Callable[[VotingStatistics], None]] = []

    def register_observer(self, callback: Callable[[VotingStatistics], None]):
        """Register state change observer."""
        if callback not in self._observers:
            self._observers.append(callback)

    def unregister_observer(self, callback: Callable[[VotingStatistics], None]):
        """Unregister state change observer."""
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self):
        """Notify all observers of state change."""
        for observer in self._observers:
            try:
                observer(self._stats)
            except Exception:
                pass

    def get_statistics(self) -> VotingStatistics:
        """Get current statistics snapshot."""
        return self._stats

    def increment_vote(self):
        """Increment vote counter."""
        self._stats = self._stats.with_vote()
        self._notify_observers()

    def increment_error(self):
        """Increment error counter."""
        self._stats = self._stats.with_error()
        self._notify_observers()

    def set_running(self, running: bool):
        """Update running status."""
        self._stats = self._stats.with_running(running)
        self._notify_observers()

    def reset_counters(self):
        """Reset all counters."""
        self._stats = self._stats.reset_counters()
        self._notify_observers()

    def add_log(self, level: str, message: str):
        """Add log entry."""
        self._log_history.add(level, message)

    def get_logs(self, errors_only: bool = False) -> List[LogEntry]:
        """Get log entries."""
        if errors_only:
            return self._log_history.get_errors_only()
        return self._log_history.get_all()

    def clear_logs(self):
        """Clear log history."""
        self._log_history.clear()

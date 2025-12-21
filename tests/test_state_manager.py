"""Unit tests for state management module."""

from Code_EXE.Votryx.core.state_manager import LogHistory, StateManager, VotingStatistics


class TestVotingStatistics:
    """Test suite for VotingStatistics."""

    def test_initial_state(self):
        """Test initial statistics state."""
        stats = VotingStatistics()
        assert stats.vote_count == 0
        assert stats.error_count == 0
        assert stats.success_count == 0
        assert stats.failure_count == 0
        assert stats.start_time is None
        assert stats.is_running is False

    def test_with_vote_increments_counters(self):
        """Test vote increment returns new state."""
        stats = VotingStatistics()
        new_stats = stats.with_vote()

        assert new_stats.vote_count == 1
        assert new_stats.success_count == 1
        assert stats.vote_count == 0

    def test_with_error_increments_counters(self):
        """Test error increment returns new state."""
        stats = VotingStatistics()
        new_stats = stats.with_error()

        assert new_stats.error_count == 1
        assert new_stats.failure_count == 1
        assert stats.error_count == 0

    def test_with_running_sets_start_time(self):
        """Test running state sets start time."""
        stats = VotingStatistics()
        new_stats = stats.with_running(True)

        assert new_stats.is_running is True
        assert new_stats.start_time is not None
        assert stats.start_time is None

    def test_with_running_clears_start_time(self):
        """Test stopping clears start time."""
        stats = VotingStatistics().with_running(True)
        new_stats = stats.with_running(False)

        assert new_stats.is_running is False
        assert new_stats.start_time is None

    def test_reset_counters(self):
        """Test counter reset."""
        stats = VotingStatistics(vote_count=10, error_count=5, success_count=8, failure_count=2)
        new_stats = stats.reset_counters()

        assert new_stats.vote_count == 0
        assert new_stats.error_count == 0
        assert new_stats.success_count == 0
        assert new_stats.failure_count == 0

    def test_get_runtime_formatted_not_running(self):
        """Test runtime format when not running."""
        stats = VotingStatistics()
        assert stats.get_runtime_formatted() == "00:00:00"

    def test_get_runtime_formatted_negative_time(self):
        """Test runtime format with future start time (edge case)."""
        import time

        stats = VotingStatistics(start_time=time.time() + 100, is_running=True)
        # Should handle gracefully and return 00:00:00
        runtime = stats.get_runtime_formatted()
        assert runtime == "00:00:00"

    def test_get_runtime_formatted_long_duration(self):
        """Test runtime format with long duration."""
        import time

        # Simulate 24+ hours of running
        stats = VotingStatistics(start_time=time.time() - 86400, is_running=True)
        runtime = stats.get_runtime_formatted()
        # Should be at least 24:00:00
        hours = int(runtime.split(":")[0])
        assert hours >= 24


class TestLogHistory:
    """Test suite for LogHistory."""

    def test_add_log_entry(self):
        """Test adding log entries."""
        history = LogHistory(max_entries=10)
        history.add("info", "Test message")

        logs = history.get_all()
        assert len(logs) == 1
        assert logs[0].level == "info"
        assert logs[0].message == "Test message"

    def test_max_entries_limit(self):
        """Test log history size limit."""
        history = LogHistory(max_entries=3)
        history.add("info", "Message 1")
        history.add("info", "Message 2")
        history.add("info", "Message 3")
        history.add("info", "Message 4")

        logs = history.get_all()
        assert len(logs) == 3
        assert logs[0].message == "Message 2"

    def test_get_errors_only(self):
        """Test filtering error logs."""
        history = LogHistory()
        history.add("info", "Info message")
        history.add("error", "Error message")
        history.add("success", "Success message")
        history.add("error", "Another error")

        errors = history.get_errors_only()
        assert len(errors) == 2
        assert all(e.level == "error" for e in errors)

    def test_clear_logs(self):
        """Test clearing log history."""
        history = LogHistory()
        history.add("info", "Message 1")
        history.add("info", "Message 2")
        history.clear()

        assert len(history.get_all()) == 0


class TestStateManager:
    """Test suite for StateManager."""

    def test_initial_statistics(self):
        """Test initial state manager statistics."""
        manager = StateManager()
        stats = manager.get_statistics()

        assert stats.vote_count == 0
        assert stats.error_count == 0
        assert not stats.is_running

    def test_increment_vote(self):
        """Test vote counter increment."""
        manager = StateManager()
        manager.increment_vote()

        stats = manager.get_statistics()
        assert stats.vote_count == 1
        assert stats.success_count == 1

    def test_increment_error(self):
        """Test error counter increment."""
        manager = StateManager()
        manager.increment_error()

        stats = manager.get_statistics()
        assert stats.error_count == 1
        assert stats.failure_count == 1

    def test_set_running(self):
        """Test running state toggle."""
        manager = StateManager()
        manager.set_running(True)

        stats = manager.get_statistics()
        assert stats.is_running is True

        manager.set_running(False)
        stats = manager.get_statistics()
        assert stats.is_running is False

    def test_reset_counters(self):
        """Test counter reset."""
        manager = StateManager()
        manager.increment_vote()
        manager.increment_error()
        manager.reset_counters()

        stats = manager.get_statistics()
        assert stats.vote_count == 0
        assert stats.error_count == 0

    def test_observer_notification(self):
        """Test observer pattern notifications."""
        manager = StateManager()
        notifications = []

        def observer(stats):
            notifications.append(stats.vote_count)

        manager.register_observer(observer)
        manager.increment_vote()
        manager.increment_vote()

        assert len(notifications) == 2
        assert notifications == [1, 2]

    def test_unregister_observer(self):
        """Test observer unregistration."""
        manager = StateManager()
        notifications = []

        def observer(stats):
            notifications.append(stats.vote_count)

        manager.register_observer(observer)
        manager.increment_vote()
        manager.unregister_observer(observer)
        manager.increment_vote()

        assert len(notifications) == 1

    def test_add_and_get_logs(self):
        """Test log management."""
        manager = StateManager()
        manager.add_log("info", "Test message")
        manager.add_log("error", "Error message")

        logs = manager.get_logs()
        assert len(logs) == 2

        errors = manager.get_logs(errors_only=True)
        assert len(errors) == 1
        assert errors[0].level == "error"

    def test_clear_logs(self):
        """Test log clearing."""
        manager = StateManager()
        manager.add_log("info", "Message")
        manager.clear_logs()

        assert len(manager.get_logs()) == 0

    def test_observer_error_handling(self):
        """Test that observer errors don't break state updates."""
        manager = StateManager()

        def bad_observer(stats):
            raise Exception("Observer error")

        def good_observer(stats):
            good_observer.called = True

        good_observer.called = False

        manager.register_observer(bad_observer)
        manager.register_observer(good_observer)

        # Should not raise exception
        manager.increment_vote()

        # Good observer should still be called
        assert good_observer.called is True

    def test_multiple_observers(self):
        """Test multiple observers receive updates."""
        manager = StateManager()
        call_counts = {"obs1": 0, "obs2": 0, "obs3": 0}

        def observer1(stats):
            call_counts["obs1"] += 1

        def observer2(stats):
            call_counts["obs2"] += 1

        def observer3(stats):
            call_counts["obs3"] += 1

        manager.register_observer(observer1)
        manager.register_observer(observer2)
        manager.register_observer(observer3)

        manager.increment_vote()
        manager.increment_error()

        assert call_counts["obs1"] == 2
        assert call_counts["obs2"] == 2
        assert call_counts["obs3"] == 2

    def test_register_same_observer_twice(self):
        """Test registering the same observer twice doesn't duplicate."""
        manager = StateManager()
        call_count = [0]

        def observer(stats):
            call_count[0] += 1

        manager.register_observer(observer)
        manager.register_observer(observer)  # Register again

        manager.increment_vote()

        # Should only be called once
        assert call_count[0] == 1

    def test_unregister_nonexistent_observer(self):
        """Test unregistering an observer that was never registered."""
        manager = StateManager()

        def observer(stats):
            pass

        # Should not raise error
        manager.unregister_observer(observer)

"""Voting engine module - core voting logic separated from UI."""

import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional, Tuple

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class VotingSession:
    """Represents a single voting session with driver and target."""

    def __init__(
        self,
        driver: webdriver.Chrome,
        target_url: str,
        timeout_seconds: int,
        vote_selectors: list,
    ):
        """Initialize voting session.

        Args:
            driver: Chrome WebDriver instance
            target_url: Target voting page URL
            timeout_seconds: Page load timeout
            vote_selectors: List of selector tuples for vote button
        """
        self.driver = driver
        self.target_url = target_url
        self.timeout_seconds = timeout_seconds
        self.vote_selectors = vote_selectors

    def navigate_to_target(self) -> bool:
        """Navigate to voting page and wait for load."""
        try:
            self.driver.set_page_load_timeout(self.timeout_seconds)
            self.driver.get(self.target_url)
            return self._wait_for_document_ready()
        except Exception:
            return False

    def _wait_for_document_ready(self) -> bool:
        """Wait for document ready state."""
        deadline = time.time() + self.timeout_seconds
        while time.time() < deadline:
            try:
                state = self.driver.execute_script("return document.readyState")
                if state in ("interactive", "complete"):
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    def locate_vote_button(self):
        """Find clickable vote button using configured selectors."""
        wait = WebDriverWait(self.driver, self.timeout_seconds)
        last_exc = None

        for by, value in self.vote_selectors:
            try:
                button = wait.until(EC.element_to_be_clickable((by, value)))
                try:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", button
                    )
                except Exception:
                    pass
                return button
            except Exception as exc:
                last_exc = exc

        if last_exc:
            raise last_exc
        return None

    def execute_vote(self, button) -> bool:
        """Click vote button."""
        try:
            button.click()
            return True
        except Exception:
            return False


class VotingEngine:
    """Core voting engine - handles batch voting logic."""

    def __init__(
        self,
        target_url: str,
        batch_size: int,
        parallel_workers: int,
        timeout_seconds: int,
        vote_selectors: list,
        pause_between_votes: float,
        max_errors: int,
        backoff_seconds: float,
        backoff_cap_seconds: float,
    ):
        """Initialize voting engine with configuration.

        Args:
            target_url: Target voting page URL
            batch_size: Number of votes per batch
            parallel_workers: Number of parallel browser windows
            timeout_seconds: Page load timeout
            vote_selectors: List of selector tuples for vote button
            pause_between_votes: Delay between votes in seconds
            max_errors: Maximum consecutive errors before stopping
            backoff_seconds: Initial backoff delay on error
            backoff_cap_seconds: Maximum backoff delay
        """
        self.target_url = target_url
        self.batch_size = batch_size
        self.parallel_workers = parallel_workers
        self.timeout_seconds = timeout_seconds
        self.vote_selectors = vote_selectors
        self.pause_between_votes = pause_between_votes
        self.max_errors = max_errors
        self.backoff_seconds = backoff_seconds
        self.backoff_cap_seconds = backoff_cap_seconds
        self.is_stopped = False

    def execute_batch(
        self,
        driver_factory: Callable,
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_prepare_error: Optional[Callable] = None,
        log_callback: Optional[Callable] = None,
    ) -> Tuple[int, int]:
        """Execute a batch of votes with parallel workers.

        Returns:
            Tuple of (successes, failures)
        """
        if log_callback:
            log_callback("Oy veriliyor", "info")

        successes = 0
        failures = 0
        total = self.batch_size

        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = []
            for i in range(total):
                if self.is_stopped:
                    break
                futures.append(executor.submit(self._prepare_and_vote, i, driver_factory))

            for idx, future in enumerate(as_completed(futures), start=1):
                if self.is_stopped:
                    continue

                try:
                    result = future.result()
                except Exception:
                    result = None

                if result is None:
                    failures += 1
                    if on_prepare_error:
                        on_prepare_error()
                    continue

                driver, vote_success = result

                if vote_success:
                    successes += 1
                    if on_success:
                        on_success(idx, total)
                else:
                    failures += 1
                    if on_error:
                        on_error()

        return successes, failures

    def _prepare_and_vote(self, batch_index: int, driver_factory: Callable):
        """Prepare session and execute vote."""
        driver = driver_factory()
        if not driver:
            return None

        if self.is_stopped:
            return None

        session = VotingSession(
            driver=driver,
            target_url=self.target_url,
            timeout_seconds=self.timeout_seconds,
            vote_selectors=self.vote_selectors,
        )

        try:
            if not session.navigate_to_target():
                return driver, False

            vote_button = session.locate_vote_button()
            if not vote_button:
                return driver, False

            success = session.execute_vote(vote_button)
            return driver, success

        except (TimeoutException, Exception):
            return driver, False

    def stop(self):
        """Signal engine to stop processing."""
        self.is_stopped = True

    def calculate_backoff_delay(self, consecutive_errors: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.backoff_seconds * (2 ** (consecutive_errors - 1))
        return min(delay, self.backoff_cap_seconds)

    def sleep_with_jitter(self, base_seconds: float) -> float:
        """Add random jitter to sleep duration."""
        jitter = random.uniform(-0.3, 0.3)
        return max(0.5, base_seconds + jitter)

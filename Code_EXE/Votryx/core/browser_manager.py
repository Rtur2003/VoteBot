"""Browser lifecycle management module."""

import shutil
import tempfile
import threading
from pathlib import Path
from typing import Dict, Optional, Set
from urllib.parse import urlparse

from selenium import webdriver


class BrowserLifecycleManager:
    """Manages browser driver lifecycle and cleanup."""

    def __init__(self, target_url: Optional[str] = None):
        """Initialize browser lifecycle manager.

        Args:
            target_url: Optional target URL for origin extraction
        """
        self.target_url = target_url
        self.target_origin = self._extract_origin(target_url)
        self._driver_lock = threading.Lock()
        self.active_drivers: Set[webdriver.Chrome] = set()
        self.driver_profiles: Dict[webdriver.Chrome, Path] = {}
        self.temp_root = Path(tempfile.mkdtemp(prefix="votryx-profiles-"))

    def _extract_origin(self, url: Optional[str]) -> Optional[str]:
        """Extract origin from URL for storage clearing."""
        if not url:
            return None
        try:
            parsed = urlparse(url)
            if parsed.scheme and parsed.netloc:
                return "{}://{}".format(parsed.scheme, parsed.netloc)
        except Exception:
            pass
        return None

    def create_temp_profile_dir(self) -> Optional[Path]:
        """Create temporary profile directory for browser session."""
        try:
            return Path(tempfile.mkdtemp(prefix="profile-", dir=self.temp_root))
        except Exception:
            return None

    def register_driver(self, driver: webdriver.Chrome, profile_dir: Optional[Path] = None):
        """Register active driver for lifecycle management."""
        with self._driver_lock:
            self.active_drivers.add(driver)
            if profile_dir:
                self.driver_profiles[driver] = profile_dir

    def unregister_driver(self, driver: webdriver.Chrome):
        """Unregister driver and cleanup profile."""
        profile_dir = None
        with self._driver_lock:
            self.active_drivers.discard(driver)
            profile_dir = self.driver_profiles.pop(driver, None)

        if profile_dir:
            self._discard_profile_dir(profile_dir)

    def clear_browser_state(self, driver: webdriver.Chrome):
        """Clear cookies, cache and storage for fresh session."""
        try:
            driver.delete_all_cookies()
        except Exception:
            pass

        if self.target_origin:
            try:
                driver.execute_cdp_cmd(
                    "Storage.clearDataForOrigin",
                    {"origin": self.target_origin, "storageTypes": "all"},
                )
            except Exception:
                pass

        try:
            driver.execute_cdp_cmd("Network.clearBrowserCache", {})
        except Exception:
            pass

        try:
            driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
        except Exception:
            pass

    def teardown_driver(self, driver: webdriver.Chrome):
        """Quit driver and cleanup resources."""
        try:
            driver.quit()
        except Exception:
            pass
        self.unregister_driver(driver)

    def cleanup_all_drivers(self):
        """Cleanup all active drivers."""
        with self._driver_lock:
            drivers = list(self.active_drivers)

        for driver in drivers:
            self.teardown_driver(driver)

    def cleanup_all_profiles(self):
        """Cleanup all temporary profiles and root directory."""
        self.cleanup_all_drivers()

        with self._driver_lock:
            remaining = list(self.driver_profiles.values())
            self.driver_profiles.clear()

        for path in remaining:
            self._discard_profile_dir(path)

        if self.temp_root.exists():
            shutil.rmtree(self.temp_root, ignore_errors=True)

    def _discard_profile_dir(self, profile_dir: Optional[Path]):
        """Remove profile directory."""
        if profile_dir and profile_dir.exists():
            shutil.rmtree(profile_dir, ignore_errors=True)

    def get_active_driver_count(self) -> int:
        """Get count of active drivers."""
        with self._driver_lock:
            return len(self.active_drivers)

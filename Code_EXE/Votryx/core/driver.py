"""Selenium WebDriver management module for VOTRYX."""

import random
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


class DriverManager:
    """Manages Chrome WebDriver creation and configuration."""

    DEFAULT_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    ]

    def __init__(
        self,
        base_dir: Path,
        chrome_path: Optional[str] = None,
        driver_path: Optional[str] = None,
        headless: bool = True,
        use_selenium_manager: bool = False,
        use_random_user_agent: bool = True,
        block_images: bool = True,
        custom_user_agents: Optional[List[str]] = None,
    ):
        """Initialize driver manager with configuration.

        Args:
            base_dir: Base directory for resolving paths
            chrome_path: Optional Chrome executable path
            driver_path: Optional ChromeDriver path
            headless: Run browser in headless mode
            use_selenium_manager: Use Selenium Manager for driver
            use_random_user_agent: Randomize user agent
            block_images: Block image loading
            custom_user_agents: Optional list of custom user agents
        """
        self.base_dir = base_dir
        self.chrome_path = chrome_path
        self.driver_path = driver_path
        self.headless = headless
        self.use_selenium_manager = use_selenium_manager
        self.use_random_user_agent = use_random_user_agent
        self.block_images = block_images
        self.custom_user_agents = custom_user_agents or []

    def resolve_chrome_path(self) -> Optional[Path]:
        """Locate Chrome browser executable."""
        candidates = []
        if self.chrome_path:
            chrome_path = Path(self.chrome_path)
            if not chrome_path.is_absolute():
                chrome_path = self.base_dir / chrome_path
            candidates.append(chrome_path)

        candidates.extend(
            [
                Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            ]
        )

        for path in candidates:
            if path.exists():
                return path
        return candidates[0] if candidates else None

    def resolve_driver_path(self) -> Optional[Path]:
        """Locate ChromeDriver executable."""
        if self.use_selenium_manager:
            return None

        candidates = []
        if self.driver_path:
            driver_path = Path(self.driver_path)
            if not driver_path.is_absolute():
                driver_path = self.base_dir / driver_path
            candidates.append(driver_path)

        candidates.extend(
            [
                self.base_dir / "chromedriver.exe",
                Path(__file__).parent.parent / "chromedriver.exe",
            ]
        )

        for path in candidates:
            if path and path.exists():
                return path
        return candidates[0] if candidates else None

    def get_version_info(self, binary_path: Path) -> Tuple[Optional[str], Optional[int]]:
        """Extract version information from binary."""
        try:
            result = subprocess.run(
                [str(binary_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = (result.stdout or result.stderr or "").strip()
            major = None
            for token in output.split():
                if token and token[0].isdigit():
                    major = token.split(".")[0]
                    break
            return output, int(major) if major and major.isdigit() else None
        except Exception:
            return None, None

    def check_version_compatibility(self, driver_path: Path, chrome_path: Path) -> bool:
        """Verify driver and browser version compatibility."""
        driver_out, driver_major = self.get_version_info(driver_path)
        chrome_out, chrome_major = self.get_version_info(chrome_path)

        if driver_major and chrome_major and driver_major != chrome_major:
            return False
        return True

    def pick_user_agent(self) -> Optional[str]:
        """Select a random user agent from pool."""
        pool = self.custom_user_agents or self.DEFAULT_USER_AGENTS
        if not pool or not self.use_random_user_agent:
            return None
        return random.choice(pool)

    def create_chrome_options(self, profile_dir: Optional[Path] = None) -> Options:
        """Build Chrome options for WebDriver."""
        chrome_options = Options()
        chrome_options.page_load_strategy = "eager"

        if self.chrome_path:
            chrome_options.binary_location = self.chrome_path

        if self.headless:
            chrome_options.add_argument("--headless=new")

        if profile_dir:
            chrome_options.add_argument(f"--user-data-dir={profile_dir}")

        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-application-cache")
        chrome_options.add_argument("--disk-cache-size=0")
        chrome_options.add_argument("--media-cache-size=0")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled,Translate,BackForwardCache"
        )
        chrome_options.add_argument("--remote-allow-origins=*")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--log-level=3")

        user_agent = self.pick_user_agent()
        if user_agent:
            chrome_options.add_argument(f"--user-agent={user_agent}")

        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-logging", "enable-automation"]
        )
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option(
            "prefs",
            {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "intl.accept_languages": "tr-TR,tr",
                "profile.managed_default_content_settings.images": (2 if self.block_images else 1),
            },
        )

        return chrome_options

    def create_driver(self, profile_dir: Optional[Path] = None) -> Optional[webdriver.Chrome]:
        """Create and configure Chrome WebDriver instance."""
        options = self.create_chrome_options(profile_dir=profile_dir)

        try:
            if self.use_selenium_manager:
                driver = webdriver.Chrome(options=options)
            else:
                resolved_driver_path = self.resolve_driver_path()
                if not resolved_driver_path:
                    raise WebDriverException("ChromeDriver path not found")
                service = Service(executable_path=str(resolved_driver_path))
                driver = webdriver.Chrome(service=service, options=options)

            self.apply_stealth_patches(driver)
            return driver

        except WebDriverException:
            if not self.use_selenium_manager:
                try:
                    driver = webdriver.Chrome(options=options)
                    self.apply_stealth_patches(driver)
                    return driver
                except Exception:
                    return None
            return None

    @staticmethod
    def apply_stealth_patches(driver: webdriver.Chrome) -> None:
        """Apply stealth techniques to avoid detection."""
        try:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = window.chrome || {};
                window.chrome.runtime = {};
                """
                },
            )
            browser_info = driver.execute_cdp_cmd("Browser.getVersion", {})
            user_agent = browser_info.get("userAgent")
            if user_agent:
                driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": user_agent})
        except Exception:
            pass

    @staticmethod
    def create_temp_profile_dir(temp_root: Path) -> Optional[Path]:
        """Create temporary profile directory."""
        try:
            return Path(tempfile.mkdtemp(prefix="profile-", dir=temp_root))
        except Exception:
            return None

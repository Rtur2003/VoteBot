# mypy: ignore-errors
"""VOTRYX Application - Tkinter UI for automated DistroKid voting.

Provides graphical control surface for voting automation with real-time
status updates, configurable parameters, and comprehensive logging.
"""

import atexit
import json
import logging
import math
import os
import platform
import random
import shutil
import subprocess
import tempfile
import threading
import time
import tkinter as tk
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

try:
    import pystray
    from PIL import Image, ImageDraw

    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

try:
    from ui.panel import ControlPanelView
except Exception:
    ControlPanelView = None


class VotryxApp:
    """Main application class for VOTRYX voting automation UI.

    Manages Tkinter interface, user interactions, and orchestrates
    voting operations through the voting engine and browser manager.
    """

    # UI Layout Constants
    STAT_CARDS_COUNT = 4

    def __init__(self, root):
        """Initialize VOTRYX application.

        Args:
            root: Tkinter root window instance
        """
        self.root = root
        self.root.title("VOTRYX - DistroKid Spotlight")
        self.root.geometry("1280x820")
        self.root.minsize(1080, 720)
        self._make_maximized()

        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.code_dir = Path(__file__).resolve().parent
        self.defaults = {
            "paths": {},
            "target_url": "https://distrokid.com/spotlight/hasanarthuraltunta/vote/",
            "pause_between_votes": 3,
            "batch_size": 1,
            "max_errors": 3,
            "parallel_workers": 2,
            "headless": True,
            "timeout_seconds": 15,
            "use_selenium_manager": False,
            "use_random_user_agent": True,
            "block_images": True,
            "user_agents": [],
            "vote_selectors": [],
            "backoff_seconds": 5,
            "backoff_cap_seconds": 60,
        }
        self.config_path = self._find_config_path()
        self.config = self._load_config()
        self.paths = self.config.setdefault("paths", {})
        self.config["user_agents"] = self._normalize_user_agents(self.config.get("user_agents", []))

        self.target_url = self.config.get(
            "target_url", "https://distrokid.com/spotlight/hasanarthuraltunta/vote/"
        )
        self.target_origin = self._extract_origin(self.target_url)
        self.pause_between_votes = float(self.config.get("pause_between_votes", 3))
        self.batch_size = max(1, int(self.config.get("batch_size", 1)))
        self.headless = bool(self.config.get("headless", True))
        self.timeout_seconds = int(self.config.get("timeout_seconds", 15))
        self.max_errors = max(1, int(self.config.get("max_errors", 3)))
        self.parallel_workers = max(1, min(10, int(self.config.get("parallel_workers", 2))))
        self.use_selenium_manager = bool(self.config.get("use_selenium_manager", False))
        self.use_random_user_agent = bool(self.config.get("use_random_user_agent", True))
        self.block_images = bool(self.config.get("block_images", True))
        self.custom_user_agents = self.config.get("user_agents") or []
        self.vote_selectors = self._build_vote_selectors(self.config.get("vote_selectors"))
        self.backoff_seconds = float(self.config.get("backoff_seconds", 5))
        self.backoff_cap_seconds = float(self.config.get("backoff_cap_seconds", 60))

        self.driver_path = None
        self.chrome_path = None
        self.general_tab = None  # will be assigned during UI build
        self.advanced_tab = None  # will be assigned during UI build
        self.stats_wrapper = None
        self.actions_frame = None
        self.log_frame = None
        self.view_stack = None
        self.main = None
        self.welcome_frame = None
        self.hero_image = None
        self.ui_ready = False

        self.is_running = False
        self.vote_count = 0
        self.error_count = 0
        self.start_time = None
        self.worker = None
        self._stop_event = threading.Event()
        self._driver_lock = threading.Lock()
        self.active_drivers = set()
        self.driver_profiles = {}
        self.temp_root = Path(tempfile.mkdtemp(prefix="votryx-profiles-"))
        self.log_records = []
        self.log_history_limit = 500
        self.success_count = 0
        self.failure_count = 0
        self.autoscroll_var = tk.BooleanVar(value=True)
        self.errors_only_var = tk.BooleanVar(value=False)
        self.random_ua_var = tk.BooleanVar(value=self.use_random_user_agent)
        self.block_images_var = tk.BooleanVar(value=self.block_images)
        self.tray_icon = None
        self.is_minimized_to_tray = False
        self.tray_available = TRAY_AVAILABLE

        self.log_dir, self.log_dir_warning = self._resolve_logs_dir()
        self.logger = self._build_logger()
        atexit.register(self._cleanup_temp_profiles)
        if getattr(self, "ignored_config_paths", []):
            ignored = ", ".join(str(p) for p in self.ignored_config_paths)
            self.logger.info(
                "Birden fazla config bulundu. Kullanılan: %s, yok sayılan: %s",
                self.config_path,
                ignored,
            )

        self.brand_image = self._load_brand_image()
        self.hero_image = self._load_hero_image()
        self.colors = {
            "bg": "#0b1224",
            "panel": "#0f1a30",
            "card": "#13213b",
            "border": "#1f2f4a",
            "accent": "#ff7a1a",
            "accent2": "#23c4ff",
            "text": "#e6edf7",
            "muted": "#a5b4ce",
            "error": "#f97070",
            "success": "#38e0a3",
            "danger": "#f43f5e",
        }

        try:
            self.brand_icon = None
            icon_candidates = [
                self.base_dir / "docs" / "screenshots" / "votryx-logo-transparent.png",
                self.base_dir / "docs" / "screenshots" / "votryx-logo-2-transparent.png",
                self.base_dir / "docs" / "screenshots" / "votryx-logo-3-dark.png",
                self.base_dir / "docs" / "screenshots" / "votryx-logo-4.png.png",
            ]
            for candidate in icon_candidates:
                if not candidate.exists():
                    continue
                try:
                    icon = tk.PhotoImage(file=str(candidate))
                    width = int(icon.width())
                    height = int(icon.height())
                    scale = max(1, math.ceil(max(width, height) / 48))
                    if scale > 1:
                        icon = icon.subsample(scale, scale)
                    self.brand_icon = icon
                    break
                except Exception:
                    continue

            if not self.brand_icon:
                self.brand_icon = self._build_icon_image()
            self.root.iconphoto(False, self.brand_icon)
        except Exception as exc:
            self.brand_icon = None
            self.logger.warning("Uygulama ikonu ayarlanamadi: %s", exc)

        try:
            self._build_styles()
            self._build_ui()
        except Exception as exc:
            tb = traceback.format_exc()
            self.logger.error("UI baslatilamadi: %s\n%s", exc, tb, exc_info=False)
            self._build_boot_error_screen(exc, tb)
            return
        self.ui_ready = True
        self._apply_responsive_layout(compact=self.root.winfo_width() < 1200)
        if self.log_dir_warning:
            self.log_message(self.log_dir_warning, level="info")
        self._set_state_badge("Bekliyor", "idle")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        if TRAY_AVAILABLE:
            self.root.bind("<Unmap>", self._handle_window_state)
        self._update_runtime()

    def _make_maximized(self):
        def _zoom():
            try:
                self.root.state("zoomed")
            except Exception:
                try:
                    self.root.attributes("-zoomed", True)
                except Exception:
                    try:
                        w = self.root.winfo_screenwidth()
                        h = self.root.winfo_screenheight()
                        self.root.geometry(f"{w}x{h}+0+0")
                    except Exception:
                        pass

        try:
            self.root.update_idletasks()
        except Exception:
            pass
        _zoom()
        self.root.after(150, _zoom)
        try:
            self.root.state("zoomed")
        except Exception:
            try:
                self.root.attributes("-zoomed", True)
            except Exception:
                pass

    def _find_config_path(self):
        candidates = [
            self.base_dir / "config.json",
            self.code_dir / "config.json",
        ]
        existing = [path for path in candidates if path.exists()]
        self.ignored_config_paths = []
        if existing:
            selected = existing[0]
            self.ignored_config_paths = [path for path in existing[1:] if path != selected]
            return selected
        return candidates[0]

    def _load_config(self):
        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return dict(self.defaults)
                merged = {**self.defaults, **data}
                default_paths = self.defaults.get("paths", {})
                if not isinstance(default_paths, dict):
                    default_paths = {}
                data_paths = data.get("paths", {})
                if not isinstance(data_paths, dict):
                    data_paths = {}
                merged["paths"] = {**default_paths, **data_paths}
                return merged
        except Exception:
            return dict(self.defaults)

    def _persist_config(self):
        target_dir = self.config_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix="config-", suffix=".json", dir=target_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
                json.dump(self.config, temp_file, ensure_ascii=False, indent=4)
            Path(temp_path).replace(self.config_path)
        except Exception:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass
            raise

    def _build_vote_selectors(self, custom_selectors):
        defaults = [
            (By.CSS_SELECTOR, "a[data-action='vote']"),
            (By.CSS_SELECTOR, "button[data-action='vote']"),
            (By.CSS_SELECTOR, "a[href*='/vote'][role='button']"),
            (By.XPATH, "//a[contains(translate(., 'VOTE', 'vote'), 'vote')]"),
            (By.XPATH, "//button[contains(translate(., 'VOTE', 'vote'), 'vote')]"),
            (
                By.XPATH,
                "//*[@id='distroListContainer']//a[contains(@class,'vote') or contains(@href,'/vote')]",
            ),
        ]
        selectors = list(defaults)
        for raw in custom_selectors or []:
            if not isinstance(raw, str):
                continue
            lower = raw.lower()
            if lower.startswith("xpath:"):
                selectors.append((By.XPATH, raw.split(":", 1)[1].strip()))
            elif lower.startswith("css:"):
                selectors.append((By.CSS_SELECTOR, raw.split(":", 1)[1].strip()))
            else:
                selectors.append((By.CSS_SELECTOR, raw.strip()))
        return selectors

    def _extract_origin(self, url):
        """Extract origin from URL for storage clearing.

        Args:
            url: Target URL string

        Returns:
            Origin string or None if extraction fails
        """
        if not url:  # Explicit null guard
            return None
        try:
            parsed = urlparse(url)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            pass
        return None

    def _normalize_user_agents(self, agents):
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

    def _pick_user_agent(self):
        pool = self.custom_user_agents or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        ]
        if not pool or not self.use_random_user_agent:
            return None
        return random.choice(pool)

    def _resolve_logs_dir(self):
        log_path = self.paths.get("logs") or "logs"
        path = Path(log_path)
        if not path.is_absolute():
            path = self.base_dir / path
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path, None
        except Exception as exc:
            fallback = Path(tempfile.mkdtemp(prefix="votryx-logs-"))
            warning = (
                f"Log klasoru '{path}' olusturulamadi ({exc}); gecici '{fallback}' kullaniliyor."
            )
            return fallback, warning

    def _build_logger(self):
        logger = logging.getLogger("Votryx")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        file_handler = RotatingFileHandler(
            self.log_dir / "votryx.log", encoding="utf-8", maxBytes=512 * 1024, backupCount=3
        )
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def _wait_for_document_ready(self, driver, timeout=None):
        deadline = time.time() + (timeout or self.timeout_seconds)
        while time.time() < deadline and not self._stop_event.is_set():
            try:
                state = driver.execute_script("return document.readyState")
                if state in ("interactive", "complete"):
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    def _apply_stealth_patches(self, driver):
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
        except Exception as exc:
            self.logger.warning("Stealth ayarları uygulanamadı: %s", exc)

    def _load_brand_image(self):
        """Try to load the official VOTRYX logo.

        Falls back to vector mark if not available.
        Attempts multiple logo variants for optimal display.
        """
        candidates = [
            self.base_dir / "docs" / "screenshots" / "votryx-logo-transparent.png",
            self.base_dir / "docs" / "screenshots" / "votryx-logo-2-transparent.png",
            self.base_dir / "docs" / "screenshots" / "votryx-logo-3-dark.png",
            self.base_dir / "docs" / "screenshots" / "votryx-logo-4.png.png",
        ]
        for candidate in candidates:
            if candidate.exists():
                try:
                    image = tk.PhotoImage(file=str(candidate))
                    try:
                        width = int(image.width())
                        height = int(image.height())
                        scale = max(1, math.ceil(max(width, height) / 96))
                        if scale > 1:
                            image = image.subsample(scale, scale)
                    except Exception:
                        pass
                    return image
                except Exception as exc:
                    self.logger.warning("Logo '%s' yüklenemedi: %s", candidate.name, exc)
        return None

    def _load_hero_image(self):
        """Load hero/banner for welcome screen if available.

        Tries multiple banner options for best visual impact.
        """
        candidates = [
            self.base_dir / "docs" / "screenshots" / "votryx-banner-dark.png",
            self.base_dir / "docs" / "screenshots" / "votryx-banner-2-dark.png",
        ]
        for candidate in candidates:
            if candidate.exists():
                try:
                    return tk.PhotoImage(file=str(candidate))
                except Exception as exc:
                    self.logger.warning("Hero görseli '%s' yüklenemedi: %s", candidate.name, exc)
        return None

    def _build_icon_image(self, size=48):
        """Build a simple geometric icon for header/title bar.

        Uses brand colors for visual consistency.
        """
        # Icon design constants
        BORDER_INSET = 2
        TOP_ACCENT_RATIO = 0.40
        BOTTOM_ACCENT_START = 0.60
        # Checkmark coordinates as ratios of size
        CHECK_LEFT_X1 = 0.22
        CHECK_LEFT_Y1 = 0.46
        CHECK_LEFT_X2 = 0.34
        CHECK_LEFT_Y2 = 0.72
        CHECK_RIGHT_X1 = 0.32
        CHECK_RIGHT_Y1 = 0.66
        CHECK_RIGHT_X2 = 0.80
        CHECK_RIGHT_Y2 = 0.78

        icon = tk.PhotoImage(width=size, height=size)
        # Background gradient effect
        icon.put(self.colors["panel"], to=(0, 0, size, size))
        icon.put(
            self.colors["card"],
            to=(BORDER_INSET, BORDER_INSET, size - BORDER_INSET, size - BORDER_INSET),
        )
        # Top accent band (cyan)
        icon.put(self.colors["accent2"], to=(0, 0, size, int(size * TOP_ACCENT_RATIO)))
        # Bottom accent band (orange)
        icon.put(self.colors["accent"], to=(0, int(size * BOTTOM_ACCENT_START), size, size))
        # Core dark area for contrast
        core = "#0c162a"
        # Stylized checkmark/tick
        icon.put(
            core,
            to=(
                int(size * CHECK_LEFT_X1),
                int(size * CHECK_LEFT_Y1),
                int(size * CHECK_LEFT_X2),
                int(size * CHECK_LEFT_Y2),
            ),
        )
        icon.put(
            core,
            to=(
                int(size * CHECK_RIGHT_X1),
                int(size * CHECK_RIGHT_Y1),
                int(size * CHECK_RIGHT_X2),
                int(size * CHECK_RIGHT_Y2),
            ),
        )
        return icon

    def _draw_brand_mark(self, canvas, size=60):
        canvas.delete("all")
        inset = 2
        canvas.create_oval(
            inset,
            inset,
            size - inset,
            size - inset,
            fill=self.colors["card"],
            outline=self.colors["accent2"],
            width=2,
        )
        canvas.create_arc(
            inset,
            inset,
            size - inset,
            size - inset,
            start=35,
            extent=240,
            fill=self.colors["accent"],
            outline="",
        )
        canvas.create_line(
            size * 0.30,
            size * 0.55,
            size * 0.42,
            size * 0.70,
            size * 0.70,
            size * 0.34,
            fill=self.colors["accent2"],
            width=5,
            smooth=True,
            capstyle="round",
            joinstyle="round",
        )
        canvas.create_text(
            size * 0.52,
            size * 0.78,
            text="VX",
            fill=self.colors["bg"],
            font=("Bahnschrift SemiBold", 11),
        )

    def _build_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        title_font = ("Bahnschrift SemiBold", 20)

        style.configure("Main.TFrame", background=self.colors["bg"], padding=0)
        style.configure("Panel.TFrame", background=self.colors["panel"])
        try:
            style.configure(
                "Card.TFrame",
                background=self.colors["card"],
                borderwidth=1,
                relief="flat",
                bordercolor=self.colors["border"],
                padding=12,
            )
        except tk.TclError:
            style.configure(
                "Card.TFrame",
                background=self.colors["card"],
                borderwidth=1,
                relief="flat",
                padding=12,
            )
        style.configure(
            "TLabelFrame",
            background=self.colors["panel"],
            foreground=self.colors["text"],
            borderwidth=0,
        )
        style.configure(
            "TLabelFrame.Label",
            background=self.colors["panel"],
            foreground=self.colors["text"],
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Title.TLabel",
            font=title_font,
            background=self.colors["bg"],
            foreground=self.colors["text"],
        )
        style.configure(
            "StatLabel.TLabel",
            font=("Segoe UI", 11),
            background=self.colors["card"],
            foreground=self.colors["muted"],
        )
        style.configure(
            "StatValue.TLabel",
            font=("Bahnschrift SemiBold", 22),
            background=self.colors["card"],
            foreground=self.colors["text"],
        )
        style.configure(
            "Status.TLabel",
            font=("Bahnschrift SemiBold", 12),
            background=self.colors["panel"],
            foreground=self.colors["text"],
        )
        style.configure(
            "Helper.TLabel",
            font=("Bahnschrift", 9),
            background=self.colors["panel"],
            foreground=self.colors["muted"],
        )
        style.configure(
            "FieldLabel.TLabel",
            font=("Bahnschrift SemiBold", 10),
            background=self.colors["panel"],
            foreground=self.colors["text"],
        )
        style.configure(
            "Badge.TLabel",
            font=("Bahnschrift SemiBold", 10),
            background=self.colors["card"],
            foreground=self.colors["text"],
            padding=(10, 6),
        )
        style.configure(
            "TNotebook",
            background=self.colors["panel"],
            borderwidth=0,
            tabmargins=(0, 0, 0, 0),
        )
        style.configure(
            "TNotebook.Tab",
            font=("Bahnschrift SemiBold", 10),
            padding=(12, 6),
            background=self.colors["card"],
            foreground=self.colors["text"],
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.colors["accent2"]), ("active", "#1d2d46")],
            foreground=[("selected", "#0f172a"), ("active", self.colors["text"])],
        )

        def button_style(
            name, bg, fg, active=None, disabled=None, border=None, padding=10, bold=True
        ):
            active = active or bg
            disabled = disabled or "#1f2937"
            font = ("Bahnschrift SemiBold", 11) if bold else ("Bahnschrift", 10)
            kwargs = {
                "font": font,
                "background": bg,
                "foreground": fg,
                "padding": padding,
                "relief": "flat",
                "borderwidth": 0,
            }
            if border:
                kwargs.update({"bordercolor": border, "focuscolor": border, "lightcolor": border})
            try:
                style.configure(name, **kwargs)
            except tk.TclError:
                kwargs.pop("bordercolor", None)
                kwargs.pop("focuscolor", None)
                kwargs.pop("lightcolor", None)
                style.configure(name, **kwargs)
            try:
                style.map(
                    name,
                    background=[("active", active), ("disabled", disabled)],
                    foreground=[("disabled", "#9ca3af"), ("pressed", fg)],
                    focuscolor=[("focus", border or self.colors["accent2"])],
                    bordercolor=[("focus", border or self.colors["accent2"])],
                )
            except tk.TclError:
                style.map(
                    name,
                    background=[("active", active), ("disabled", disabled)],
                    foreground=[("disabled", "#9ca3af"), ("pressed", fg)],
                )

        button_style(
            "Accent.TButton",
            self.colors["accent"],
            "#0f172a",
            active=self.colors["accent2"],
            disabled="#1f2a3d",
        )
        button_style(
            "Ghost.TButton",
            self.colors["card"],
            self.colors["text"],
            active="#1f2f4a",
            disabled="#1f2a3d",
            border=self.colors["border"],
            bold=False,
            padding=9,
        )
        button_style(
            "Outline.TButton",
            self.colors["panel"],
            self.colors["text"],
            active=self.colors["card"],
            disabled="#1f2a3d",
            border=self.colors["accent2"],
            bold=False,
            padding=9,
        )
        button_style(
            "Danger.TButton", self.colors["danger"], "#0f172a", active="#e11d48", disabled="#7f1d1d"
        )
        style.configure(
            "Switch.TCheckbutton",
            background=self.colors["panel"],
            foreground=self.colors["text"],
            font=("Bahnschrift", 10),
        )
        style.map("Switch.TCheckbutton", background=[("active", "#1f2937")])
        try:
            style.configure(
                "TEntry",
                fieldbackground=self.colors["panel"],
                foreground=self.colors["text"],
                insertcolor=self.colors["text"],
                bordercolor=self.colors["card"],
                padding=6,
            )
        except tk.TclError:
            style.configure(
                "TEntry",
                fieldbackground=self.colors["panel"],
                foreground=self.colors["text"],
                insertcolor=self.colors["text"],
                padding=6,
            )
        try:
            style.map(
                "TEntry",
                fieldbackground=[("focus", "#111a2d")],
                bordercolor=[("focus", self.colors["accent2"])],
            )
        except tk.TclError:
            style.map("TEntry", fieldbackground=[("focus", "#111a2d")])
        style.configure(
            "Section.TLabel",
            font=("Bahnschrift SemiBold", 12),
            background=self.colors["bg"],
            foreground=self.colors["text"],
        )
        style.configure(
            "Pill.TLabel",
            font=("Bahnschrift SemiBold", 9),
            background="#182645",
            foreground=self.colors["accent"],
            padding=(12, 5),
        )
        style.configure(
            "TNotebook",
            background=self.colors["panel"],
            borderwidth=0,
            tabmargins=(0, 0, 0, 0),
        )
        style.configure(
            "TNotebook.Tab",
            font=("Bahnschrift SemiBold", 10),
            padding=(12, 6),
            background=self.colors["card"],
            foreground=self.colors["text"],
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.colors["accent2"]), ("active", "#1d2d46")],
            foreground=[("selected", "#0f172a"), ("active", self.colors["text"])],
        )

    def _build_boot_error_screen(self, exc: Exception, tb: str) -> None:
        try:
            for child in list(self.root.winfo_children()):
                child.destroy()
        except Exception:
            pass

        bg = self.colors.get("bg", "#0b1224") if hasattr(self, "colors") else "#0b1224"
        fg = self.colors.get("text", "#e6edf7") if hasattr(self, "colors") else "#e6edf7"
        muted = self.colors.get("muted", "#a5b4ce") if hasattr(self, "colors") else "#a5b4ce"
        card = self.colors.get("card", "#13213b") if hasattr(self, "colors") else "#13213b"

        try:
            self.root.configure(bg=bg)
        except Exception:
            pass

        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

        wrapper = tk.Frame(self.root, bg=bg)
        wrapper.pack(fill="both", expand=True, padx=24, pady=24)
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(3, weight=1)

        tk.Label(
            wrapper,
            text="VOTRYX UI baslatilamadi",
            bg=bg,
            fg=fg,
            font=("Segoe UI", 16, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")

        tk.Label(
            wrapper,
            text=f"Hata: {exc}",
            bg=bg,
            fg=muted,
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
            wraplength=960,
        ).grid(row=1, column=0, sticky="ew", pady=(8, 10))

        tk.Label(
            wrapper,
            text=f"Log: {self.log_dir / 'votryx.log'}",
            bg=bg,
            fg=muted,
            font=("Consolas", 9),
            anchor="w",
        ).grid(row=2, column=0, sticky="ew", pady=(0, 10))

        details = tk.Text(
            wrapper,
            bg=card,
            fg=fg,
            insertbackground=fg,
            relief="flat",
            highlightthickness=1,
            highlightbackground=card,
            font=("Consolas", 9),
            wrap="none",
        )
        details.grid(row=3, column=0, sticky="nsew")
        try:
            details.insert("1.0", tb.strip())
            details.configure(state="disabled")
        except Exception:
            pass

        btns = tk.Frame(wrapper, bg=bg)
        btns.grid(row=4, column=0, sticky="e", pady=(12, 0))
        tk.Button(btns, text="Log klasorunu ac", command=self.open_logs).pack(
            side="left", padx=(0, 8)
        )
        tk.Button(btns, text="Kapat", command=self.root.destroy).pack(side="left")

    def _build_ui(self):
        if ControlPanelView is None:
            self.logger.warning("ControlPanelView import failed; using legacy UI")
            self._build_ui_legacy()
            return
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ControlPanelView(self, self.root)
        main.grid(row=0, column=0, sticky="nsew")
        self.main = main
        self.root.bind("<Configure>", self._on_root_resize)
        self._set_form_state(False)
        self._apply_responsive_layout(compact=self.root.winfo_width() < 1200)
        self.log_message("UI: control panel ready")

    def _build_ui_legacy(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        view_stack = ttk.Frame(self.root, style="Main.TFrame")
        view_stack.grid(row=0, column=0, sticky="nsew")
        view_stack.columnconfigure(0, weight=1)
        view_stack.rowconfigure(0, weight=1)
        self.view_stack = view_stack

        main = ttk.Frame(view_stack, style="Main.TFrame", padding=16)
        main.grid(row=0, column=0, sticky="nsew")
        self.main = main
        self.root.bind("<Configure>", self._on_root_resize)

        main.columnconfigure(0, weight=2)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=0, minsize=120)
        main.rowconfigure(1, weight=0, minsize=140)
        main.rowconfigure(2, weight=1, minsize=300)
        main.rowconfigure(3, weight=0, minsize=80)
        main.rowconfigure(4, weight=0)

        header = ttk.Frame(main, style="Main.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        header.columnconfigure(2, weight=1)
        if self.brand_image:
            logo_widget: tk.Widget = tk.Label(
                header,
                image=self.brand_image,
                bg=self.colors["bg"],
                bd=0,
                highlightthickness=0,
            )
        else:
            logo_widget = tk.Canvas(
                header,
                width=64,
                height=64,
                bg=self.colors["bg"],
                highlightthickness=0,
                bd=0,
            )
            self._draw_brand_mark(logo_widget, size=64)
        logo_widget.grid(row=0, column=0, rowspan=2, padx=(0, 16), pady=(0, 0), sticky="w")
        title_block = ttk.Frame(header, style="Main.TFrame")
        title_block.grid(row=0, column=1, rowspan=2, sticky="w", padx=(0, 12))
        title = ttk.Label(title_block, text="VOTRYX - DistroKid Spotlight", style="Title.TLabel")
        title.grid(row=0, column=0, sticky="w", pady=(0, 2))
        pill_frame = ttk.Frame(title_block, style="Main.TFrame")
        pill_frame.grid(row=0, column=1, padx=(10, 0), sticky="w")
        ttk.Label(pill_frame, text="Headless hazır", style="Pill.TLabel").grid(
            row=0, column=0, padx=(0, 6)
        )
        ttk.Label(pill_frame, text="Batch oy", style="Pill.TLabel").grid(
            row=0, column=1, padx=(0, 6)
        )
        ttk.Label(pill_frame, text="Log kaydı", style="Pill.TLabel").grid(row=0, column=2)
        subtitle = ttk.Label(
            title_block,
            text="Stabil, hızlı, şeffaf otomatik oy",
            foreground=self.colors["muted"],
            background=self.colors["bg"],
            font=("Segoe UI", 11),
        )
        subtitle.grid(row=1, column=0, pady=(2, 2), sticky="w")
        tagline = ttk.Label(
            title_block,
            text="Başlat ve unut: otomatik sürücü kontrolü, batch oy ve güvenli loglama",
            foreground=self.colors["muted"],
            background=self.colors["bg"],
            font=("Segoe UI", 10),
        )
        tagline.grid(row=2, column=0, pady=(0, 0), sticky="w")
        self.state_badge = tk.Label(
            header,
            text="Bekliyor",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Bahnschrift SemiBold", 11),
            padx=14,
            pady=8,
        )
        self.state_badge.grid(row=0, column=2, rowspan=2, sticky="e", padx=(0, 0))

        # Stats
        self.stats_wrapper = ttk.LabelFrame(
            main, text="Gösterge Paneli", style="Panel.TFrame", padding=10
        )
        self.stats_wrapper.grid(
            row=1, column=0, columnspan=2, sticky="nsew", padx=(0, 0), pady=(6, 6)
        )
        self.stats_wrapper.columnconfigure(0, weight=1)
        self.stats_wrapper.rowconfigure(0, weight=1)
        stats_frame = ttk.Frame(self.stats_wrapper, style="Panel.TFrame")
        stats_frame.grid(row=0, column=0, sticky="nsew")
        for i in range(self.STAT_CARDS_COUNT):
            stats_frame.columnconfigure(i, weight=1, minsize=180)
        stats_frame.rowconfigure(0, weight=1)

        self._make_stat_card(stats_frame, 0, 0, "Toplam Oy", "0", "count")
        self._make_stat_card(stats_frame, 0, 1, "Hata", "0", "errors")
        self._make_stat_card(stats_frame, 0, 2, "Durum", "Bekliyor", "status")
        self._make_stat_card(stats_frame, 0, 3, "Süre", "00:00:00", "runtime")

        # Settings + Log side by side (desktop)
        settings_shell = ttk.Frame(main, style="Panel.TFrame")
        settings_shell.grid(row=2, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        settings_shell.columnconfigure(0, weight=1)
        settings_shell.rowconfigure(0, weight=1)

        log_shell = ttk.Frame(main, style="Panel.TFrame")
        log_shell.grid(row=2, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))
        log_shell.columnconfigure(0, weight=1)
        log_shell.rowconfigure(0, weight=1)

        settings = ttk.LabelFrame(settings_shell, text="Ayarlar", style="Panel.TFrame", padding=14)
        settings.grid(row=0, column=0, sticky="nsew")
        settings.columnconfigure(0, weight=1)
        settings.rowconfigure(0, weight=1)

        settings_nb = ttk.Notebook(settings, style="TNotebook")
        settings_nb.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        settings.columnconfigure(0, weight=1)
        settings.rowconfigure(0, weight=1)
        self.general_tab = ttk.Frame(settings_nb, style="Panel.TFrame", padding=10)
        self.advanced_tab = ttk.Frame(settings_nb, style="Panel.TFrame", padding=10)
        general_tab = self.general_tab
        advanced_tab = self.advanced_tab
        general_tab.columnconfigure(1, weight=1)
        advanced_tab.columnconfigure(1, weight=1)
        settings_nb.add(general_tab, text="Genel")
        settings_nb.add(advanced_tab, text="Gelişmiş")
        general_tab.columnconfigure((0, 1), weight=1)
        url_block = ttk.Frame(general_tab, style="Panel.TFrame")
        url_block.grid(row=0, column=0, columnspan=2, sticky="ew")
        url_block.columnconfigure(1, weight=1)
        ttk.Label(
            url_block,
            text="Hedef URL",
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=0, column=0, sticky="w", pady=(4, 0), padx=(0, 8))
        self.url_entry = ttk.Entry(url_block)
        self.url_entry.insert(0, self.target_url)
        self.url_entry.grid(row=0, column=1, sticky="ew", pady=(4, 0))
        ttk.Label(
            url_block,
            text="Oylama sayfasının bağlantısı",
            style="Helper.TLabel",
            wraplength=520,
        ).grid(row=1, column=1, sticky="w", pady=(0, 6))

        general_grid = ttk.Frame(general_tab, style="Panel.TFrame")
        general_grid.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(6, 0))
        general_grid.columnconfigure((0, 2), weight=0)
        general_grid.columnconfigure((1, 3), weight=1)

        def add_field(grid, row_idx, col_base, label_text, default_value, helper_text):
            ttk.Label(
                grid,
                text=label_text,
                background=self.colors["panel"],
                foreground=self.colors["text"],
            ).grid(row=row_idx * 2, column=col_base, sticky="w", pady=(8, 0), padx=(0, 10))
            entry = ttk.Entry(grid, width=12)
            entry.insert(0, str(default_value))
            entry.grid(row=row_idx * 2, column=col_base + 1, sticky="ew", pady=(8, 0))
            ttk.Label(
                grid,
                text=helper_text,
                style="Helper.TLabel",
                wraplength=240,
            ).grid(row=row_idx * 2 + 1, column=col_base + 1, sticky="w", pady=(2, 10))
            return entry

        self.pause_entry = add_field(
            general_grid,
            0,
            0,
            "Oy aralığı (sn)",
            self.pause_between_votes,
            "Her oy arasında bekleme süresi",
        )
        self.batch_entry = add_field(
            general_grid, 0, 2, "Batch (kaç oy)", self.batch_size, "Tek seferde verilecek oy sayısı"
        )
        self.timeout_entry = add_field(
            general_grid,
            1,
            0,
            "Zaman aşımı (sn)",
            self.timeout_seconds,
            "Oy butonu için bekleme sınırı",
        )
        self.max_errors_entry = add_field(
            general_grid,
            1,
            2,
            "Maks hata",
            self.max_errors,
            "Bu sayıya ulaşınca bekleme ve yeniden deneme",
        )
        self.backoff_entry = add_field(
            general_grid, 2, 0, "Backoff (sn)", self.backoff_seconds, "Hata sonrası ilk bekleme"
        )
        self.backoff_cap_entry = add_field(
            general_grid,
            2,
            2,
            "Backoff üst sınır",
            self.backoff_cap_seconds,
            "Maksimum bekleme sınırı",
        )
        self.parallel_entry = add_field(
            general_grid,
            3,
            0,
            "Paralel pencere",
            self.parallel_workers,
            "Aynı anda açılacak tarayıcı sayısı",
        )

        toggles = ttk.Frame(general_tab, style="Panel.TFrame")
        toggles.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        toggles.columnconfigure((0, 1), weight=1)
        self.headless_var = tk.BooleanVar(value=self.headless)
        self.headless_check = ttk.Checkbutton(
            toggles,
            text="Görünmez (headless) çalıştır",
            variable=self.headless_var,
            style="Switch.TCheckbutton",
        )
        self.headless_check.grid(row=0, column=0, sticky="w", padx=(0, 16), pady=(0, 4))
        self.auto_driver_var = tk.BooleanVar(value=self.use_selenium_manager)
        self.auto_driver_check = ttk.Checkbutton(
            toggles,
            text="ChromeDriver'ı Selenium Manager yönetsin",
            variable=self.auto_driver_var,
            style="Switch.TCheckbutton",
        )
        self.auto_driver_check.grid(row=0, column=1, sticky="w", pady=(0, 4))
        ttk.Label(
            toggles,
            text="Headless kapalıysa tarayıcıyı izleyebilirsiniz; Selenium Manager uyumsuz sürücüleri indirir.",
            style="Helper.TLabel",
            wraplength=520,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

        # Gelişmiş sekme
        self.random_ua_check = ttk.Checkbutton(
            advanced_tab,
            text="Rastgele user-agent kullan",
            variable=self.random_ua_var,
            style="Switch.TCheckbutton",
        )
        self.random_ua_check.grid(row=0, column=0, columnspan=2, sticky="w", pady=(4, 2))
        ttk.Label(
            advanced_tab,
            text="Açıkken liste veya varsayılan havuzdan UA seçilir; kapalıysa Chrome varsayılanı kullanılır.",
            style="Helper.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self.block_images_check = ttk.Checkbutton(
            advanced_tab,
            text="Görselleri engelle (daha hızlı yükleme)",
            variable=self.block_images_var,
            style="Switch.TCheckbutton",
        )
        self.block_images_check.grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 0))
        ttk.Label(
            advanced_tab,
            text="Açıkken sayfa görselleri yüklenmez; kapalıysa varsayılan yükleme kullanılır.",
            style="Helper.TLabel",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(
            advanced_tab,
            text="User-Agent listesi (satır satır)",
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=4, column=0, sticky="nw", pady=(4, 0), padx=(0, 8))
        self.ua_text = scrolledtext.ScrolledText(
            advanced_tab,
            height=4,
            width=36,
            background=self.colors["panel"],
            foreground=self.colors["text"],
            insertbackground=self.colors["text"],
            font=("Consolas", 9),
            borderwidth=1,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.colors["card"],
        )
        self.ua_text.grid(row=4, column=1, sticky="ew", pady=(4, 0))
        ttk.Label(
            advanced_tab,
            text="Boş bırakılırsa varsayılan UA havuzu kullanılır.",
            style="Helper.TLabel",
        ).grid(row=5, column=1, sticky="w", pady=(0, 8))
        for line in self.custom_user_agents:
            self.ua_text.insert(tk.END, f"{line}\n")

        ttk.Label(
            advanced_tab,
            text="Oy buton seçicileri (satır satır CSS/XPath)",
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=6, column=0, sticky="nw", pady=(4, 0), padx=(0, 8))
        self.selectors_text = scrolledtext.ScrolledText(
            advanced_tab,
            height=4,
            width=36,
            background=self.colors["panel"],
            foreground=self.colors["text"],
            insertbackground=self.colors["text"],
            font=("Consolas", 9),
            borderwidth=1,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.colors["card"],
        )
        self.selectors_text.grid(row=6, column=1, sticky="ew", pady=(4, 0))
        selectors_helper = (
            "Örnekler: a[data-action='vote'], button[data-action='vote'], "
            "xpath://button[contains(.,'vote')]"
        )
        ttk.Label(self.advanced_tab, text=selectors_helper, style="Helper.TLabel").grid(
            row=7, column=1, sticky="w", pady=(0, 8)
        )
        for line in self.config.get("vote_selectors", []):
            self.selectors_text.insert(tk.END, f"{line}\n")

        self.settings_frame = settings
        actions = ttk.Frame(settings, style="Panel.TFrame")
        actions.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        actions.columnconfigure((0, 1), weight=1)
        self.apply_btn = ttk.Button(
            actions,
            text="Ayarları Uygula",
            command=self.apply_settings,
            style="Ghost.TButton",
        )
        self.apply_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=3)
        self.defaults_btn = ttk.Button(
            actions,
            text="Varsayılanları Yükle",
            command=self.reset_to_defaults,
            style="Ghost.TButton",
        )
        self.defaults_btn.grid(row=0, column=1, sticky="ew", ipady=3)

        self.actions_frame = ttk.LabelFrame(main, text="Eylemler", style="Panel.TFrame", padding=12)
        self.actions_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.actions_frame.columnconfigure(0, weight=1)
        controls = ttk.Frame(self.actions_frame, style="Panel.TFrame", padding=(0, 0))
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.start_btn = ttk.Button(
            controls, text="Başlat", command=self.start_bot, style="Accent.TButton"
        )
        self.start_btn.grid(row=0, column=0, padx=6, pady=6, sticky="ew", ipady=4)
        self.stop_btn = ttk.Button(
            controls,
            text="Durdur",
            command=self.stop_bot,
            style="Ghost.TButton",
            state=tk.DISABLED,
        )
        self.stop_btn.grid(row=0, column=1, padx=6, pady=6, sticky="ew", ipady=4)
        self.preflight_btn = ttk.Button(
            controls, text="Ön kontrol", command=self.run_preflight, style="Ghost.TButton"
        )
        self.preflight_btn.grid(row=0, column=2, padx=6, pady=6, sticky="ew", ipady=4)
        self.logs_btn = ttk.Button(
            controls, text="Log klasörünü aç", command=self.open_logs, style="Ghost.TButton"
        )
        self.logs_btn.grid(row=0, column=3, padx=6, pady=6, sticky="ew", ipady=4)
        self.reset_btn = ttk.Button(
            controls, text="Sayaclari sifirla", command=self.reset_counters, style="Ghost.TButton"
        )
        self.reset_btn.grid(row=0, column=4, padx=6, pady=6, sticky="ew", ipady=4)

        # Add minimize to tray button if available
        if TRAY_AVAILABLE:
            self.tray_btn = ttk.Button(
                controls,
                text="Gizle (Arka Plan)",
                command=self._minimize_to_tray,
                style="Outline.TButton",
            )
            self.tray_btn.grid(row=0, column=5, padx=6, pady=6, sticky="ew", ipady=4)

        log_frame = ttk.LabelFrame(log_shell, text="Log", style="Panel.TFrame", padding=12)
        log_frame.grid(row=0, column=0, sticky="nsew")
        log_frame.rowconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_frame = log_frame
        log_controls = ttk.Frame(log_frame, style="Panel.TFrame")
        log_controls.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        log_controls.columnconfigure(2, weight=1)
        self.success_badge = tk.Label(
            log_controls,
            text="Başarılı: 0",
            bg=self.colors["success"],
            fg="#0f172a",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=4,
        )
        self.success_badge.grid(row=0, column=0, padx=(0, 6), sticky="w")
        self.failure_badge = tk.Label(
            log_controls,
            text="Hata: 0",
            bg=self.colors["error"],
            fg="#0f172a",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=4,
        )
        self.failure_badge.grid(row=0, column=1, padx=(0, 12), sticky="w")
        auto_check = ttk.Checkbutton(
            log_controls,
            text="Otomatik kaydır",
            variable=self.autoscroll_var,
            style="Switch.TCheckbutton",
            command=self._render_log,
        )
        auto_check.grid(row=0, column=2, sticky="e", padx=(0, 6))
        error_check = ttk.Checkbutton(
            log_controls,
            text="Sadece hatalar",
            variable=self.errors_only_var,
            style="Switch.TCheckbutton",
            command=self.toggle_errors_only,
        )
        error_check.grid(row=0, column=3, sticky="e")

        self.log_area = scrolledtext.ScrolledText(
            self.log_frame,
            width=60,
            height=18,
            background="#0b1220",
            foreground=self.colors["text"],
            insertbackground=self.colors["text"],
            font=("Consolas", 10),
            borderwidth=1,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.colors["card"],
        )
        self.log_area.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        self.log_area.tag_configure("info", foreground=self.colors["text"])
        self.log_area.tag_configure("success", foreground=self.colors["success"])
        self.log_area.tag_configure("error", foreground=self.colors["error"])
        self.log_area.tag_configure("muted", foreground=self.colors["muted"])
        clear_btn = ttk.Button(
            log_frame, text="Log temizle", command=self.clear_log, style="Ghost.TButton"
        )
        clear_btn.grid(row=2, column=0, sticky="e")
        self.log_frame = log_frame
        self._set_form_state(False)
        self._apply_responsive_layout(compact=self.root.winfo_width() < 1200)
        self._build_welcome_overlay()
        self._show_welcome()

    def _make_stat_card(self, parent, row, col, title, value, key):
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        parent.rowconfigure(row, weight=1)
        parent.columnconfigure(col, weight=1)
        accent_bar = tk.Frame(card, bg=self.colors["accent2"], width=5, height=64)
        accent_bar.grid(row=0, column=0, rowspan=2, sticky="nsw", padx=(0, 12))
        ttk.Label(card, text=title, style="StatLabel.TLabel").grid(
            row=0, column=1, sticky="w", pady=(0, 4)
        )
        label = ttk.Label(card, text=value, style="StatValue.TLabel")
        label.grid(row=1, column=1, sticky="w")
        if key == "count":
            self.count_label = label
        elif key == "errors":
            self.error_label = label
        elif key == "status":
            self.status_label = label
        elif key == "runtime":
            self.runtime_label = label

    def _apply_responsive_layout(self, compact: bool):
        def _exists(widget) -> bool:
            if not widget:
                return False
            try:
                return bool(widget.winfo_exists())
            except Exception:
                return False

        def _grid_target(widget):
            if not widget:
                return None
            parent = getattr(widget, "master", None)
            if parent is None or parent is self.main:
                return widget
            return parent

        if not self.ui_ready or not all(
            [
                _exists(self.main),
                _exists(self.stats_wrapper),
                _exists(self.settings_frame),
                _exists(self.log_frame),
                _exists(self.actions_frame),
            ]
        ):
            return
        if getattr(self, "_is_compact_layout", None) == compact:
            return
        self._is_compact_layout = compact
        try:
            settings_target = _grid_target(self.settings_frame)
            log_target = _grid_target(self.log_frame)
            if compact:
                self.main.columnconfigure(0, weight=1)
                self.main.columnconfigure(1, weight=0)
                self.main.rowconfigure(0, weight=0, minsize=120)
                self.main.rowconfigure(1, weight=0, minsize=140)
                self.main.rowconfigure(2, weight=1, minsize=250)
                self.main.rowconfigure(3, weight=1, minsize=250)
                self.main.rowconfigure(4, weight=0, minsize=80)
                self.stats_wrapper.grid_configure(row=1, column=0, columnspan=2, padx=(0, 0))
                if settings_target and _exists(settings_target):
                    settings_target.grid_configure(row=2, column=0, columnspan=2, padx=(0, 0))
                if log_target and _exists(log_target):
                    log_target.grid_configure(row=3, column=0, columnspan=2, padx=(0, 0))
                self.actions_frame.grid_configure(row=4, column=0, columnspan=2, padx=(0, 0))
            else:
                self.main.columnconfigure(0, weight=2, minsize=500)
                self.main.columnconfigure(1, weight=1, minsize=350)
                self.main.rowconfigure(0, weight=0, minsize=120)
                self.main.rowconfigure(1, weight=0, minsize=140)
                self.main.rowconfigure(2, weight=1, minsize=300)
                self.main.rowconfigure(3, weight=0, minsize=80)
                self.main.rowconfigure(4, weight=0)
                self.stats_wrapper.grid_configure(row=1, column=0, columnspan=2, padx=(0, 0))
                if settings_target and _exists(settings_target):
                    settings_target.grid_configure(row=2, column=0, columnspan=1, padx=(0, 8))
                if log_target and _exists(log_target):
                    log_target.grid_configure(row=2, column=1, columnspan=1, padx=(8, 0))
                self.actions_frame.grid_configure(row=3, column=0, columnspan=2, padx=(0, 0))
        except tk.TclError:
            return

    def _on_root_resize(self, event):
        if not self.ui_ready:
            return
        self._apply_responsive_layout(compact=event.width < 1200)

    def _build_welcome_overlay(self):
        if self.welcome_frame:
            try:
                self.welcome_frame.destroy()
            except Exception:
                pass
        parent = self.view_stack or self.root
        self.welcome_frame = tk.Frame(parent, bg=self.colors["bg"])
        self.welcome_frame.grid(row=0, column=0, sticky="nsew")

        wrapper = ttk.Frame(self.welcome_frame, style="Main.TFrame", padding=40)
        wrapper.pack(fill="both", expand=True)
        wrapper.columnconfigure(1, weight=1)
        wrapper.rowconfigure(0, weight=1)

        if self.hero_image:
            hero_widget: tk.Widget = tk.Label(
                wrapper, image=self.hero_image, bg=self.colors["bg"], bd=0, highlightthickness=0
            )
        elif self.brand_image:
            hero_widget = tk.Label(
                wrapper, image=self.brand_image, bg=self.colors["bg"], bd=0, highlightthickness=0
            )
        else:
            hero_widget = tk.Canvas(
                wrapper, width=360, height=280, bg=self.colors["bg"], highlightthickness=0, bd=0
            )
            self._draw_brand_mark(hero_widget, size=220)
        hero_widget.grid(row=0, column=0, sticky="nsew", padx=(0, 32))

        info = ttk.Frame(wrapper, style="Main.TFrame")
        info.grid(row=0, column=1, sticky="nsew")
        info.columnconfigure(0, weight=1)

        ttk.Label(info, text="VOTRYX - DistroKid Spotlight", style="Title.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )
        ttk.Label(
            info,
            text="Stabil, hızlı, şeffaf otomatik oy",
            foreground=self.colors["muted"],
            background=self.colors["bg"],
            font=("Segoe UI", 12),
        ).grid(row=1, column=0, sticky="w", pady=(0, 16))
        bullets = [
            "Chromedriver/Chrome ön kontrol, batch/parallel oy",
            "Loglama, ekran görüntüsü, backoff ve zaman aşımı korumaları",
            "Sekmeli ayarlar, gelişmiş UA ve selector yönetimi",
            (
                "Arka plan çalışma desteği - gizle ve çalışmaya devam et"
                if TRAY_AVAILABLE
                else "Arka plan çalışma desteği yüklenmedi"
            ),
        ]
        for idx, text in enumerate(bullets):
            ttk.Label(
                info,
                text=f"• {text}",
                foreground=self.colors["text"],
                background=self.colors["bg"],
                font=("Segoe UI", 10),
            ).grid(row=2 + idx, column=0, sticky="w", pady=(0, 6))

        cta = ttk.Button(
            info, text="Kontrol Paneline Gir", style="Accent.TButton", command=self._show_app
        )
        cta.grid(row=2 + len(bullets), column=0, sticky="w", pady=(18, 6), ipady=4)
        sub = ttk.Button(
            info, text="Log klasörünü aç", style="Ghost.TButton", command=self.open_logs
        )
        sub.grid(row=3 + len(bullets), column=0, sticky="w", pady=(0, 6), ipady=4)

        # Add loading indicator
        loading_frame = ttk.Frame(info, style="Main.TFrame")
        loading_frame.grid(row=4 + len(bullets), column=0, sticky="w", pady=(20, 0))

        self.loading_label = ttk.Label(
            loading_frame,
            text="",
            foreground=self.colors["accent2"],
            background=self.colors["bg"],
            font=("Segoe UI", 9),
        )
        self.loading_label.pack()

    def _animate_loading(self, step=0):
        """Animate loading dots on welcome screen."""
        if not hasattr(self, "loading_label"):
            return

        try:
            if self.welcome_frame and self.welcome_frame.winfo_exists():
                dots = "." * (step % 4)
                self.loading_label.config(text=f"Hazırlanıyor{dots}")
                self.root.after(400, lambda: self._animate_loading(step + 1))
        except Exception:
            pass

    def _show_welcome(self):
        if self.welcome_frame:
            self.log_message("UI: welcome ekrani gosterildi")
            try:
                self.welcome_frame.grid()
                self.welcome_frame.tkraise()
            except Exception:
                pass
            self._animate_loading()

    def _show_app(self):
        """Transition from welcome screen to main app."""
        self.log_message("UI: kontrol paneli gecisi baslatildi")
        self._show_main()
        try:
            self.root.after(600, self._ensure_main_visible)
        except tk.TclError:
            pass

    def _show_main(self):
        """Show the main control panel and remove the welcome overlay."""
        self.log_message("UI: kontrol paneli gorunur hale getiriliyor")
        if self.welcome_frame:
            try:
                self.welcome_frame.destroy()
            except Exception:
                try:
                    self.welcome_frame.grid_remove()
                except Exception:
                    pass
            self.welcome_frame = None
        try:
            if self.main and self.main.winfo_exists():
                self.main.grid()
                self.main.tkraise()
        except Exception:
            pass
        try:
            self.root.update_idletasks()
        except Exception:
            pass
        self._apply_responsive_layout(compact=self.root.winfo_width() < 1200)

    def _ensure_main_visible(self):
        if not self.ui_ready:
            return
        main_visible = False
        try:
            if self.main and self.main.winfo_exists():
                main_visible = bool(self.main.winfo_ismapped())
        except Exception:
            main_visible = False
        if self.welcome_frame and self.welcome_frame.winfo_exists():
            self.log_message("UI: welcome ekrani kaldiriliyor (watchdog)", level="error")
            self._show_main()
            return
        if not main_visible:
            self.log_message("UI: panel gorunur degil, yeniden gosteriliyor", level="error")
            self._show_main()

    def _fade_out_welcome(self, alpha=1.0):
        """Gradually fade out welcome screen."""
        if not self.welcome_frame or not self.welcome_frame.winfo_exists():
            self._show_main()
            return
        if alpha <= 0:
            self._show_main()
            return

        try:
            next_alpha = max(0, alpha - 0.2)
            self.root.after(30, lambda: self._fade_out_welcome(next_alpha))
        except Exception:
            self._show_main()

    def _schedule(self, func):
        if not self.ui_ready:
            return
        try:
            self.root.after(0, func)
        except tk.TclError:
            pass

    def _update_runtime(self):
        if not self.ui_ready:
            return
        if self.start_time and self.is_running:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.runtime_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        try:
            self.root.after(1000, self._update_runtime)
        except tk.TclError:
            pass

    def _create_temp_profile_dir(self):
        try:
            return Path(tempfile.mkdtemp(prefix="profile-", dir=self.temp_root))
        except Exception as exc:
            self.log_message(f"Geçici profil oluşturulamadı: {exc}", level="error")
            return None

    def _discard_profile_dir(self, profile_dir):
        if profile_dir and Path(profile_dir).exists():
            shutil.rmtree(profile_dir, ignore_errors=True)

    def _register_driver(self, driver, profile_dir=None):
        with self._driver_lock:
            self.active_drivers.add(driver)
            if profile_dir:
                self.driver_profiles[driver] = profile_dir

    def _unregister_driver(self, driver):
        profile_dir = None
        with self._driver_lock:
            self.active_drivers.discard(driver)
            profile_dir = self.driver_profiles.pop(driver, None)
        self._discard_profile_dir(profile_dir)

    def _clear_browser_state(self, driver):
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

    def _teardown_driver(self, driver):
        try:
            driver.quit()
        except Exception:
            pass
        self._unregister_driver(driver)

    def _cleanup_drivers(self):
        with self._driver_lock:
            drivers = list(self.active_drivers)
        for driver in drivers:
            self._teardown_driver(driver)

    def _cleanup_temp_profiles(self):
        self._cleanup_drivers()
        with self._driver_lock:
            remaining = list(self.driver_profiles.values())
            self.driver_profiles.clear()
        for path in remaining:
            self._discard_profile_dir(path)
        if self.temp_root.exists():
            shutil.rmtree(self.temp_root, ignore_errors=True)

    def _create_tray_icon(self):
        """Create system tray icon for background operation.

        Returns:
            pystray.Icon instance or None if unavailable or creation fails
        """
        if not TRAY_AVAILABLE:
            return None

        try:
            # Fallback colors in case UI hasn't initialized
            colors = getattr(
                self,
                "colors",
                {
                    "bg": "#0b1224",
                    "card": "#13213b",
                    "accent2": "#23c4ff",
                    "accent": "#ff7a1a",
                },
            )

            # Create a simple icon image
            icon_size = 64
            image = Image.new("RGB", (icon_size, icon_size), colors.get("bg", "#0b1224"))
            draw = ImageDraw.Draw(image)

            # Draw a simple circular icon with brand colors
            draw.ellipse(
                [4, 4, icon_size - 4, icon_size - 4],
                fill=colors.get("card", "#13213b"),
                outline=colors.get("accent2", "#23c4ff"),
            )
            draw.arc(
                [4, 4, icon_size - 4, icon_size - 4],
                start=35,
                end=275,
                fill=colors.get("accent", "#ff7a1a"),
                width=8,
            )

            # Create menu with current state
            menu = self._create_tray_menu()
            return pystray.Icon("votryx", image, "VOTRYX", menu)
        except Exception as exc:
            self.logger.warning("Tray icon oluşturulamadı: %s", exc)
            return None

    def _create_tray_menu(self):
        """Create tray icon menu with current bot state.

        Returns:
            pystray.Menu instance
        """
        return pystray.Menu(
            pystray.MenuItem("Göster", self._show_from_tray, default=True),
            pystray.MenuItem("Durdur" if self.is_running else "Başlat", self._toggle_bot_from_tray),
            pystray.MenuItem("Çıkış", self._quit_from_tray),
        )

    def _show_from_tray(self, icon=None, item=None):
        """Show window from system tray."""
        self.is_minimized_to_tray = False
        self.root.after(0, lambda: (self.root.deiconify(), self.root.focus_force()))

    def _toggle_bot_from_tray(self, icon=None, item=None):
        """Toggle bot state from system tray."""
        if self.is_running:
            self.root.after(0, self.stop_bot)
        else:
            self.root.after(0, self.start_bot)

    def _quit_from_tray(self, icon=None, item=None):
        """Quit application from system tray."""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.on_close)

    def _minimize_to_tray(self):
        """Minimize window to system tray.

        If system tray is not available, logs an error and returns without action.
        Creates tray icon on first minimization.
        """
        if not TRAY_AVAILABLE:
            self.log_message("Sistem tepsisi desteği yok (pystray yüklenmemiş)", level="error")
            return

        try:
            self.is_minimized_to_tray = True
            self.root.withdraw()

            if not self.tray_icon:
                self.tray_icon = self._create_tray_icon()
                if self.tray_icon:
                    threading.Thread(target=self.tray_icon.run, daemon=True).start()
                else:
                    self.log_message("Tray icon oluşturulamadı", level="error")
                    # Restore window if tray icon creation failed
                    self.is_minimized_to_tray = False
                    self.root.deiconify()
                    return

            self.log_message("Arka planda çalışmaya devam ediyor")
        except Exception as exc:
            self.logger.exception("Tray minimize hatası", exc_info=exc)
            self.log_message(f"Arka plana geçilemedi: {exc}", level="error")
            # Restore window on error
            self.is_minimized_to_tray = False
            try:
                self.root.deiconify()
            except Exception:
                pass

    def _handle_window_state(self, event=None):
        """Handle window state changes for tray minimize support.

        Args:
            event: Tkinter event (optional)
        """
        try:
            # Check if window is being iconified (minimized)
            if self.root.state() == "iconic" and TRAY_AVAILABLE:
                self.root.after(100, self._minimize_to_tray)
        except Exception as exc:
            # Silently fail for window state checks to avoid UI disruption
            self.logger.debug("Window state check hatası: %s", exc)

    def log_message(self, message, level="info"):
        """Add message to application log with timestamp.

        Args:
            message: Log message text
            level: Severity level (info, success, error)
        """
        # Guard: validate message is not None
        if message is None:
            message = ""

        # Guard: validate level is in allowed values
        if level not in ("info", "success", "error"):
            level = "info"

        timestamp = datetime.now().strftime("%H:%M:%S")

        def append():
            if not (self.errors_only_var.get() and level != "error"):
                self._insert_log_line(timestamp, message, level)
            self._update_log_counts_badges()

        self.log_records.append((timestamp, level, message))
        if len(self.log_records) > self.log_history_limit:
            self.log_records = self.log_records[-self.log_history_limit :]
        if level == "error":
            self.failure_count += 1
            self.logger.error(message)
        else:
            if level == "success":
                self.success_count += 1
            self.logger.info(message)
        self._schedule(append)

    def update_status(self, text, tone=None):
        """Update status label with new message and visual tone.

        Args:
            text: Status message to display
            tone: Visual styling (running, idle, error, success)
        """
        # Guard: validate text is not None
        if text is None:
            text = "Bekliyor"

        def apply():
            self.status_label.config(text=text)
            badge_tone = tone or ("running" if "Çalış" in text or "Oy ver" in text else "idle")
            self._set_state_badge(text, badge_tone)

        self._schedule(apply)

    def increment_count(self):
        """Increment successful vote counter and update UI."""
        self.vote_count += 1
        self._schedule(
            lambda: (
                self.count_label.config(text=str(self.vote_count)),
                self._refresh_stat_colors(),
            )
        )

    def increment_error(self):
        """Increment error counter and update UI."""
        self.error_count += 1
        self._schedule(
            lambda: (
                self.error_label.config(text=str(self.error_count)),
                self._refresh_stat_colors(),
            )
        )

    def clear_log(self):
        """Clear log display and reset log counters."""
        self.log_records.clear()
        self.success_count = 0
        self.failure_count = 0
        self.log_area.delete(1.0, tk.END)
        self._update_log_counts_badges()
        self.log_message("Log temizlendi")

    def reset_counters(self):
        """Reset vote and error counters to zero."""
        if self.is_running:
            self.log_message("Bot çalişirken sayaçlar sifirlanamaz.", level="error")
            return
        self.vote_count = 0
        self.error_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.start_time = None
        self.count_label.config(text="0")
        self.error_label.config(text="0")
        self.runtime_label.config(text="00:00:00")
        self._update_log_counts_badges()
        self._refresh_stat_colors()
        self.log_message("Sayaçlar sifirlandi.")

    def _set_state_badge(self, text, tone="idle"):
        colors = {
            "running": (self.colors["accent2"], "#0f172a"),
            "success": (self.colors["success"], "#0f172a"),
            "stopped": (self.colors["error"], "#0f172a"),
            "idle": (self.colors["card"], self.colors["text"]),
        }
        bg, fg = colors.get(tone, colors["idle"])
        self.state_badge.config(text=text, bg=bg, fg=fg)

        # Start pulse animation if running
        if tone == "running":
            self._pulse_state_badge(step=0)

    def _pulse_state_badge(self, step=0):
        """Subtle pulse animation for running state badge."""
        if not self.is_running:
            return

        try:
            # Simple opacity-like effect by alternating between two similar colors
            if step % 2 == 0:
                self.state_badge.config(bg=self.colors["accent2"])
            else:
                self.state_badge.config(bg="#1ea7d8")  # Slightly lighter shade

            self.root.after(800, lambda: self._pulse_state_badge(step + 1))
        except Exception:
            pass

    def _update_log_counts_badges(self):
        self.success_badge.config(text=f"Başarılı: {self.success_count}")
        self.failure_badge.config(text=f"Hata: {self.failure_count}")

    def _refresh_stat_colors(self):
        count_color = self.colors["success"] if self.vote_count else self.colors["text"]
        error_color = self.colors["error"] if self.error_count else self.colors["text"]
        self.count_label.config(foreground=count_color)
        self.error_label.config(foreground=error_color)

    def _set_form_state(self, running: bool):
        state_flag = ["disabled"] if running else ["!disabled"]
        for entry in [
            self.url_entry,
            self.pause_entry,
            self.batch_entry,
            self.timeout_entry,
            self.max_errors_entry,
            self.backoff_entry,
            self.backoff_cap_entry,
            self.parallel_entry,
        ]:
            entry.state(state_flag)
        for btn in [self.apply_btn, self.defaults_btn, self.preflight_btn, self.reset_btn]:
            btn.state(state_flag)
        for check in [
            self.headless_check,
            self.auto_driver_check,
            getattr(self, "random_ua_check", None),
            getattr(self, "block_images_check", None),
        ]:
            if running:
                if check:
                    check.state(["disabled"])
            else:
                if check:
                    check.state(["!disabled"])
        if running:
            self.selectors_text.config(state=tk.DISABLED)
            if hasattr(self, "ua_text"):
                self.ua_text.config(state=tk.DISABLED)
        else:
            self.selectors_text.config(state=tk.NORMAL)
            if hasattr(self, "ua_text"):
                self.ua_text.config(state=tk.NORMAL)

    def _insert_log_line(self, timestamp, message, level):
        tag = "info"
        if level == "error":
            tag = "error"
        elif level == "success":
            tag = "success"
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        if self.autoscroll_var.get():
            self.log_area.see(tk.END)

    def _render_log(self):
        def render():
            self.log_area.delete(1.0, tk.END)
            for ts, lvl, msg in self.log_records:
                if self.errors_only_var.get() and lvl != "error":
                    continue
                self._insert_log_line(ts, msg, lvl)
            self._update_log_counts_badges()

        self._schedule(render)

    def toggle_errors_only(self):
        """Toggle error-only filter for log display."""
        self._render_log()

    def _resolve_driver_path(self):
        candidates = []
        driver_cfg = self.paths.get("driver")
        if driver_cfg:
            driver_path = Path(driver_cfg)
            if not driver_path.is_absolute():
                driver_path = self.base_dir / driver_path
            candidates.append(driver_path)
        candidates.append(self.base_dir / "chromedriver.exe")
        candidates.append(self.code_dir / "chromedriver.exe")
        for path in candidates:
            if path and path.exists():
                return path
        return candidates[0] if candidates else None

    def _resolve_chrome_path(self):
        chrome_cfg = self.paths.get("chrome")
        candidates = []
        if chrome_cfg:
            chrome_path = Path(chrome_cfg)
            if not chrome_path.is_absolute():
                chrome_path = self.base_dir / chrome_path
            candidates.append(chrome_path)
        candidates.append(Path(r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"))
        candidates.append(Path(r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"))
        for path in candidates:
            if path.exists():
                return path
        return candidates[0] if candidates else None

    def _get_version_info(self, binary_path: Path, label: str):
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
        except Exception as exc:
            self.log_message(f"{label} versiyon okunamadı: {exc}", level="error")
            return None, None

    def _check_version_compatibility(self, driver_path: Path, chrome_path: Path):
        driver_out, driver_major = self._get_version_info(driver_path, "ChromeDriver")
        chrome_out, chrome_major = self._get_version_info(chrome_path, "Chrome")
        if driver_major and chrome_major and driver_major != chrome_major:
            msg = (
                f"Sürüm uyumsuz: ChromeDriver {driver_out} vs Chrome {chrome_out}. "
                "Chrome sürümünüzle eşleşen driver'ı indirip chromedriver.exe ile değiştirin."
            )
            self.log_message(msg, level="error")
            return False
        return True

    def _validate_paths(self, show_message=True):
        driver_path = None if self.use_selenium_manager else self._resolve_driver_path()
        chrome_path = self._resolve_chrome_path()
        problems = []
        if not self.use_selenium_manager and (not driver_path or not driver_path.exists()):
            problems.append(
                "chromedriver bulunamadı. config.json'daki 'paths.driver' yolunu kontrol edin."
            )
        if not chrome_path or not chrome_path.exists():
            if self.use_selenium_manager:
                self.log_message(
                    "Chrome yolu bulunamadı; Selenium Manager Chrome for Testing deneyecek.",
                    level="info",
                )
            else:
                problems.append("Chrome bulunamadı. 'paths.chrome' yolunu kontrol edin.")
        if problems:
            if show_message:
                messagebox.showerror("Yol Hatası", "\n".join(problems))
            for msg in problems:
                self.log_message(msg, level="error")
            return False
        if not self.use_selenium_manager and not self._check_version_compatibility(
            driver_path, chrome_path
        ):
            if show_message:
                messagebox.showerror(
                    "Sürüm Uyumsuzluğu",
                    "ChromeDriver ve Chrome sürümleri farklı. Lütfen sürümü eşleştirin.",
                )
            return False
        self.driver_path = str(driver_path) if driver_path else None
        self.chrome_path = str(chrome_path) if chrome_path and chrome_path.exists() else None
        if self.use_selenium_manager:
            self.log_message("ChromeDriver Selenium Manager tarafından otomatik yönetilecek.")
        else:
            self.log_message(f"Sürücü: {self.driver_path}")
        if self.chrome_path:
            self.log_message(f"Chrome: {self.chrome_path}")
        return True

    def _validate_config_integrity(self) -> bool:
        """Validate configuration values are within acceptable ranges.

        Returns:
            True if configuration is valid, False otherwise
        """
        # Validate timeout
        if self.timeout_seconds <= 0:
            self.log_message("Timeout değeri pozitif olmalı", level="error")
            return False

        # Validate pause duration
        if self.pause_between_votes < 0:
            self.log_message("Oy aralığı negatif olamaz", level="error")
            return False

        # Validate batch size
        if self.batch_size <= 0:
            self.log_message("Batch boyutu pozitif olmalı", level="error")
            return False

        # Validate parallel workers
        if self.parallel_workers < 1 or self.parallel_workers > 10:
            self.log_message("Paralel worker sayısı 1-10 arasında olmalı", level="error")
            return False

        # Validate backoff values
        if self.backoff_seconds <= 0 or self.backoff_cap_seconds <= 0:
            self.log_message("Backoff süreleri pozitif olmalı", level="error")
            return False

        if self.backoff_cap_seconds < self.backoff_seconds:
            self.log_message("Backoff üst sınırı başlangıç değerinden küçük olamaz", level="error")
            return False

        # Validate target URL
        if not self.target_url or not self.target_url.strip():
            self.log_message("Hedef URL boş olamaz", level="error")
            return False

        return True

    def get_chrome_options(self, profile_dir=None):
        """Build Chrome options with configured flags and profile.

        Args:
            profile_dir: Optional path to user profile directory

        Returns:
            Configured Options instance
        """
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
        user_agent = self._pick_user_agent()
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
                "profile.managed_default_content_settings.images": 2 if self.block_images else 1,
            },
        )
        return chrome_options

    def create_driver(self, profile_dir=None):
        """Create and initialize ChromeDriver instance.

        Args:
            profile_dir: Optional profile directory path

        Returns:
            WebDriver instance or None on failure
        """
        options = self.get_chrome_options(profile_dir=profile_dir)
        try:
            if self.use_selenium_manager or not self.driver_path:
                driver = webdriver.Chrome(options=options)
            else:
                service = Service(executable_path=self.driver_path)
                driver = webdriver.Chrome(service=service, options=options)
            self._apply_stealth_patches(driver)
            return driver
        except WebDriverException as exc:
            self.log_message(f"ChromeDriver başlatılamadı: {exc}", level="error")
            if not self.use_selenium_manager:
                self.log_message("Selenium Manager ile otomatik indirme deneniyor...", level="info")
                try:
                    driver = webdriver.Chrome(options=options)
                    self._apply_stealth_patches(driver)
                    return driver
                except Exception as exc2:
                    self.log_message(f"Selenium Manager da başarısız: {exc2}", level="error")
            return None

    def start_bot(self):
        """Start voting automation in background thread."""
        if self.is_running:
            return
        if not self._update_settings_from_form(persist=True, notify=False):
            return
        if not self._validate_config_integrity():
            messagebox.showerror("Yapılandırma Hatası", "Lütfen yapılandırmayı kontrol edin.")
            return
        if not self._validate_paths(show_message=True):
            return
        self.is_running = True
        self._stop_event.clear()
        self.start_time = time.time()
        self.log_message("Bot başlatıldı")
        self.update_status("Çalışıyor", tone="running")
        self.runtime_label.config(text="00:00:00")
        self.start_btn.config(state=tk.DISABLED, text="Çalışıyor...")
        self.stop_btn.config(state=tk.NORMAL)
        self._set_form_state(True)
        # Update window title to show running status
        self.root.title("VOTRYX - DistroKid Spotlight [ÇALIŞIYOR]")
        self.worker = threading.Thread(target=self.run_bot, daemon=True)
        self.worker.start()

    def stop_bot(self):
        """Stop voting automation and cleanup resources."""
        if not self.is_running:
            return
        self.log_message("Bot durduruluyor...")
        self.is_running = False
        self._stop_event.set()
        self._cleanup_drivers()
        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=1.0)
        self.update_status("Durduruldu", tone="stopped")
        self.start_btn.config(state=tk.NORMAL, text="Başlat")
        self.stop_btn.config(state=tk.DISABLED)
        self._set_form_state(False)
        # Restore window title
        self.root.title("VOTRYX - DistroKid Spotlight")

    def run_bot(self):
        """Execute main bot loop with error handling and backoff."""
        consecutive_errors = 0
        backoff_delay = self.backoff_seconds
        while not self._stop_event.is_set():
            batch_ok = self.run_batch()
            if batch_ok:
                consecutive_errors = 0
                backoff_delay = self.backoff_seconds
            else:
                consecutive_errors += 1
            if consecutive_errors >= self.max_errors:
                wait_for = min(backoff_delay, self.backoff_cap_seconds)
                self.log_message(
                    f"Art arda {consecutive_errors} hata alındı, {wait_for} sn bekleniyor ve yeniden denenecek.",
                    level="error",
                )
                consecutive_errors = 0
                if not self._sleep_with_checks(wait_for):
                    break
                backoff_delay = min(backoff_delay * 2, self.backoff_cap_seconds)
            jitter = random.uniform(-0.3, 0.3)
            pause = max(0.5, self.pause_between_votes + jitter)
            if not self._sleep_with_checks(pause):
                break
        self.is_running = False
        self._cleanup_drivers()
        self._schedule(lambda: self.update_status("Durduruldu", tone="stopped"))
        self._schedule(lambda: self.start_btn.config(state=tk.NORMAL, text="Başlat"))
        self._schedule(lambda: self.stop_btn.config(state=tk.DISABLED))
        self._schedule(lambda: self._set_form_state(False))

    def run_batch(self):
        """Execute a batch of votes in parallel workers."""
        self.update_status("Oy veriliyor", tone="running")
        successes = 0
        failures = 0
        total = self.batch_size
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = []
            for i in range(total):
                if self._stop_event.is_set():
                    break
                futures.append(executor.submit(self._prepare_vote_session, i))
            for idx, future in enumerate(as_completed(futures), start=1):
                try:
                    session = future.result()
                except Exception as exc:
                    self.logger.exception("Oy hazırlık hatası", exc_info=exc)
                    session = None
                if not session:
                    self.increment_error()
                    failures += 1
                    continue
                driver, vote_button, _ = session
                if self._stop_event.is_set():
                    self._teardown_driver(driver)
                    continue
                if self._complete_vote(driver, vote_button, idx, total):
                    successes += 1
                else:
                    failures += 1

        if successes == 0:
            self.log_message(
                f"Batch tamamlanamadı. Başarılı: {successes}, Hata: {failures}", level="error"
            )
            return False
        if failures:
            self.log_message(
                f"Batch kısmen tamamlandı. Başarılı: {successes}, Hata: {failures}",
                level="success",
            )
        else:
            self.log_message(
                f"Batch tamamlandı. Başarılı: {successes}, Hata: {failures}", level="success"
            )
        self.update_status("Bekliyor", tone="idle")
        return True

    def _complete_vote(self, driver, vote_button, idx, total):
        try:
            vote_button.click()
            self.log_message(f"Oy verildi (pencere {idx}/{total})", level="success")
            self.increment_count()
            return True
        except Exception:
            try:
                driver.refresh()
                wait = WebDriverWait(driver, self.timeout_seconds)
                refreshed_btn = self._locate_vote_button(driver, wait)
                refreshed_btn.click()
                self.log_message(
                    f"Oy verildi (yeniden deneme, pencere {idx}/{total})",
                    level="success",
                )
                self.increment_count()
                return True
            except TimeoutException:
                self.log_message("Oy butonu zaman aşımına uğradı.", level="error")
                self.increment_error()
            except Exception as exc:
                self.logger.exception("Oy verme hatası", exc_info=exc)
                self.log_message(f"Beklenmeyen hata: {exc}", level="error")
                self.increment_error()
        finally:
            self._clear_browser_state(driver)
            self._teardown_driver(driver)
        return False

    def _prepare_vote_session(self, batch_index):
        profile_dir = self._create_temp_profile_dir()
        driver = self.create_driver(profile_dir=profile_dir)
        if not driver:
            self._discard_profile_dir(profile_dir)
            return None
        self._register_driver(driver, profile_dir)
        keep_driver = False
        if self._stop_event.is_set():
            self._teardown_driver(driver)
            return None
        driver.set_page_load_timeout(self.timeout_seconds)
        wait = WebDriverWait(driver, self.timeout_seconds)
        try:
            driver.get(self.target_url)
            self._wait_for_document_ready(driver, timeout=self.timeout_seconds)
            vote_button = self._locate_vote_button(driver, wait)
            keep_driver = True
            return driver, vote_button, profile_dir
        except TimeoutException:
            self.log_message("Oy butonu zaman aşımına uğradı (hazırlık).", level="error")
        except Exception as exc:
            self.logger.exception("Oy hazırlık hatası", exc_info=exc)
            self.log_message(f"Beklenmeyen hata (hazırlık): {exc}", level="error")
        finally:
            if not keep_driver:
                self._teardown_driver(driver)
        return None

    def _locate_vote_button(self, driver, wait):
        last_exc = None
        for by, value in self.vote_selectors:
            if self._stop_event.is_set():
                break
            try:
                button = wait.until(EC.element_to_be_clickable((by, value)))
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                except Exception:
                    pass
                return button
            except Exception as exc:
                last_exc = exc
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot = self.log_dir / f"vote_fail_{timestamp}.png"
        try:
            driver.save_screenshot(screenshot)
            self.log_message(f"Oy butonu bulunamadı, ekran görüntüsü: {screenshot}", level="error")
        except Exception:
            self.log_message("Oy butonu bulunamadı, ekran görüntüsü alınamadı.", level="error")
        if last_exc:
            raise last_exc
        return None

    def _sleep_with_checks(self, seconds):
        steps = max(1, int(seconds * 10))
        for _ in range(steps):
            if self._stop_event.is_set():
                return False
            time.sleep(0.1)
        return True

    def run_preflight(self):
        """Run preflight checks and display results."""
        if self._validate_paths(show_message=True):
            messagebox.showinfo("Ön kontrol", "Yollar ve ayarlar geçerli görünüyor.")
            self.log_message("Ön kontrol başarılı")

    def reset_to_defaults(self):
        """Reset all configuration fields to default values."""
        defaults = dict(self.defaults)
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, defaults["target_url"])
        self.pause_entry.delete(0, tk.END)
        self.pause_entry.insert(0, str(defaults["pause_between_votes"]))
        self.batch_entry.delete(0, tk.END)
        self.batch_entry.insert(0, str(defaults["batch_size"]))
        self.timeout_entry.delete(0, tk.END)
        self.timeout_entry.insert(0, str(defaults["timeout_seconds"]))
        self.max_errors = defaults["max_errors"]
        self.max_errors_entry.delete(0, tk.END)
        self.max_errors_entry.insert(0, str(defaults["max_errors"]))
        self.backoff_seconds = defaults["backoff_seconds"]
        self.backoff_entry.delete(0, tk.END)
        self.backoff_entry.insert(0, str(defaults["backoff_seconds"]))
        self.backoff_cap_seconds = defaults["backoff_cap_seconds"]
        self.backoff_cap_entry.delete(0, tk.END)
        self.backoff_cap_entry.insert(0, str(defaults["backoff_cap_seconds"]))
        self.parallel_workers = defaults["parallel_workers"]
        self.parallel_entry.delete(0, tk.END)
        self.parallel_entry.insert(0, str(defaults["parallel_workers"]))
        self.headless_var.set(defaults["headless"])
        self.use_selenium_manager = defaults["use_selenium_manager"]
        self.auto_driver_var.set(defaults["use_selenium_manager"])
        self.use_random_user_agent = defaults["use_random_user_agent"]
        self.random_ua_var.set(defaults["use_random_user_agent"])
        self.block_images = defaults["block_images"]
        self.block_images_var.set(defaults["block_images"])
        self.custom_user_agents = defaults.get("user_agents", [])
        if hasattr(self, "ua_text"):
            self.ua_text.config(state=tk.NORMAL)
            self.ua_text.delete("1.0", tk.END)
            for line in self.custom_user_agents:
                self.ua_text.insert(tk.END, f"{line}\n")
        self.vote_selectors = self._build_vote_selectors(defaults.get("vote_selectors"))
        self.selectors_text.config(state=tk.NORMAL)
        self.selectors_text.delete("1.0", tk.END)
        for line in defaults.get("vote_selectors", []):
            self.selectors_text.insert(tk.END, f"{line}\n")
        self.log_message("Varsayılan ayarlar yüklendi.")
        self.apply_settings()

    def apply_settings(self):
        """Apply configuration changes from UI form."""
        return self._update_settings_from_form(persist=True, notify=True)

    def _update_settings_from_form(self, persist=False, notify=True):
        try:
            pause = float(self.pause_entry.get())
            batch = max(1, int(self.batch_entry.get()))
            timeout_val = max(5, int(self.timeout_entry.get()))
            max_err = max(1, int(self.max_errors_entry.get()))
            backoff_val = float(self.backoff_entry.get())
            backoff_cap = float(self.backoff_cap_entry.get())
            parallel = max(1, min(10, int(self.parallel_entry.get())))
            selector_lines = [
                line.strip()
                for line in self.selectors_text.get("1.0", tk.END).splitlines()
                if line.strip()
            ]
            ua_lines = [
                line.strip()
                for line in self.ua_text.get("1.0", tk.END).splitlines()
                if line.strip()
            ]
            ua_lines = self._normalize_user_agents(ua_lines)

        except ValueError:
            messagebox.showerror("Hata", "Sayısal alanlar geçerli ve pozitif olmalı.")
            self.log_message("Ayarlar okunamadı: sayısal alan hatalı.", level="error")
            return False

        if pause <= 0:
            messagebox.showerror("Hata", "Oy aralığı 0'dan büyük olmalı.")
            self.log_message("Geçersiz oy aralığı değeri girildi.", level="error")
            return False
        if backoff_val <= 0 or backoff_cap <= 0:
            messagebox.showerror("Hata", "Backoff süreleri 0'dan büyük olmalı.")
            self.log_message("Geçersiz backoff değeri girildi.", level="error")
            return False
        if backoff_cap < backoff_val:
            messagebox.showerror("Hata", "Backoff üst sınırı başlangıç değerinden küçük olamaz.")
            self.log_message("Geçersiz backoff üst sınırı girildi.", level="error")
            return False

        url = self.url_entry.get().strip()
        if not url or not url.startswith(("http://", "https://")):
            messagebox.showerror("Hata", "Geçerli bir hedef URL girin (http/https ile).")
            self.log_message("Geçersiz hedef URL girildi.", level="error")
            return False

        self.target_url = url
        self.target_origin = self._extract_origin(self.target_url)
        self.pause_between_votes = pause
        self.batch_size = batch
        self.timeout_seconds = timeout_val
        self.max_errors = max_err
        self.backoff_seconds = backoff_val
        self.backoff_cap_seconds = backoff_cap
        self.parallel_workers = parallel
        self.headless = bool(self.headless_var.get())
        self.use_selenium_manager = bool(self.auto_driver_var.get())
        self.use_random_user_agent = bool(self.random_ua_var.get())
        self.block_images = bool(self.block_images_var.get())
        self.custom_user_agents = ua_lines
        self.config["target_url"] = self.target_url
        self.config["pause_between_votes"] = self.pause_between_votes
        self.config["batch_size"] = self.batch_size
        self.config["max_errors"] = self.max_errors
        self.config["parallel_workers"] = self.parallel_workers
        self.config["headless"] = self.headless
        self.config["timeout_seconds"] = self.timeout_seconds
        self.config["use_selenium_manager"] = self.use_selenium_manager
        self.config["use_random_user_agent"] = self.use_random_user_agent
        self.config["block_images"] = self.block_images
        self.config["user_agents"] = self.custom_user_agents
        self.config["vote_selectors"] = selector_lines
        self.config["backoff_seconds"] = self.backoff_seconds
        self.config["backoff_cap_seconds"] = self.backoff_cap_seconds
        self.config.setdefault("paths", self.paths)
        self.config["paths"].setdefault("driver", self.paths.get("driver", ""))
        self.config["paths"].setdefault("chrome", self.paths.get("chrome", ""))
        self.config["paths"].setdefault("logs", self.paths.get("logs", "logs"))
        self.vote_selectors = self._build_vote_selectors(self.config.get("vote_selectors"))

        if persist:
            try:
                self._persist_config()
                if notify:
                    self.log_message("Ayarlar kaydedildi.")
                    messagebox.showinfo("Ayarlar", "Ayarlar güncellendi.")
            except Exception as exc:
                self.log_message(f"Ayarlar kaydedilemedi: {exc}", level="error")
                messagebox.showerror("Hata", f"Ayarlar kaydedilemedi: {exc}")
                return False
        return True

    def open_logs(self):
        """Open log directory in system file browser."""
        try:
            if platform.system() == "Windows" and hasattr(os, "startfile"):
                os.startfile(self.log_dir)
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(self.log_dir)], check=False)
            else:
                subprocess.run(["xdg-open", str(self.log_dir)], check=False)
        except Exception:
            messagebox.showinfo("Log klasörü", str(self.log_dir))

    def on_close(self):
        """Handle application close event with cleanup."""
        self.ui_ready = False
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.stop_bot()
        self._cleanup_temp_profiles()
        self.root.destroy()


def main():
    """Application entry point."""
    root = tk.Tk()
    app = VotryxApp(root)  # noqa: F841 - app instance must be kept alive
    root.mainloop()


if __name__ == "__main__":
    main()

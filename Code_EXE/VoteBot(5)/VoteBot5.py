import json
import logging
import os
import random
import subprocess
import threading
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class VoteBot5:
    def __init__(self, root):
        self.root = root
        self.root.title("VoteBot 5 - DistroKid Spotlight")
        self.root.geometry("1080x760")
        self.root.minsize(960, 680)

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
            "vote_selectors": [],
            "backoff_seconds": 5,
            "backoff_cap_seconds": 60,
        }
        self.config_path = self._find_config_path()
        self.config = self._load_config()
        self.paths = self.config.setdefault("paths", {})

        self.target_url = self.config.get(
            "target_url", "https://distrokid.com/spotlight/hasanarthuraltunta/vote/"
        )
        self.pause_between_votes = float(self.config.get("pause_between_votes", 3))
        self.batch_size = max(1, int(self.config.get("batch_size", 1)))
        self.headless = bool(self.config.get("headless", True))
        self.timeout_seconds = int(self.config.get("timeout_seconds", 15))
        self.max_errors = max(1, int(self.config.get("max_errors", 3)))
        self.parallel_workers = max(1, min(10, int(self.config.get("parallel_workers", 2))))
        self.use_selenium_manager = bool(self.config.get("use_selenium_manager", False))
        self.vote_selectors = self._build_vote_selectors(self.config.get("vote_selectors"))
        self.backoff_seconds = float(self.config.get("backoff_seconds", 5))
        self.backoff_cap_seconds = float(self.config.get("backoff_cap_seconds", 60))

        self.driver_path = None
        self.chrome_path = None

        self.is_running = False
        self.vote_count = 0
        self.error_count = 0
        self.start_time = None
        self.worker = None
        self._stop_event = threading.Event()
        self._driver_lock = threading.Lock()
        self.active_drivers = set()
        self.log_records = []
        self.log_history_limit = 500
        self.success_count = 0
        self.failure_count = 0
        self.autoscroll_var = tk.BooleanVar(value=True)
        self.errors_only_var = tk.BooleanVar(value=False)

        self.log_dir = self._resolve_logs_dir()
        self.logger = self._build_logger()
        if getattr(self, "ignored_config_paths", []):
            ignored = ", ".join(str(p) for p in self.ignored_config_paths)
            self.logger.info(
                "Birden fazla config bulundu. Kullanılan: %s, yok sayılan: %s",
                self.config_path,
                ignored,
            )

        self.colors = {
            "bg": "#0f172a",
            "panel": "#0b1220",
            "card": "#111827",
            "border": "#1f2937",
            "accent": "#f59e0b",
            "accent2": "#22d3ee",
            "text": "#e5e7eb",
            "muted": "#94a3b8",
            "error": "#f87171",
            "success": "#34d399",
            "danger": "#ef4444",
        }

        self.brand_icon = self._build_icon_image()
        self.root.iconphoto(False, self.brand_icon)

        self._build_styles()
        self._build_ui()
        self._set_state_badge("Bekliyor", "idle")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._update_runtime()

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
                merged = {**self.defaults, **data}
                merged["paths"] = {**self.defaults.get("paths", {}), **data.get("paths", {})}
                return merged
        except Exception:
            return dict(self.defaults)

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

    def _resolve_logs_dir(self):
        log_path = self.paths.get("logs") or "logs"
        path = Path(log_path)
        if not path.is_absolute():
            path = self.base_dir / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _build_logger(self):
        logger = logging.getLogger("VoteBot5")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        file_handler = RotatingFileHandler(
            self.log_dir / "votebot5.log", encoding="utf-8", maxBytes=512 * 1024, backupCount=3
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
                if state == "complete":
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
                driver.execute_cdp_cmd(
                    "Network.setUserAgentOverride", {"userAgent": user_agent}
                )
        except Exception as exc:
            self.logger.warning("Stealth ayarları uygulanamadı: %s", exc)

    def _build_icon_image(self, size=48):
        # Build a simple geometric icon for header/title bar.
        icon = tk.PhotoImage(width=size, height=size)
        icon.put(self.colors["bg"], to=(0, 0, size, size))
        icon.put(self.colors["card"], to=(1, 1, size - 1, size - 1))
        icon.put(self.colors["accent2"], to=(0, 0, size, int(size * 0.35)))
        icon.put(self.colors["accent"], to=(0, int(size * 0.65), size, size))
        check_color = "#0f172a"
        icon.put(
            check_color,
            to=(
                int(size * 0.30),
                int(size * 0.50),
                int(size * 0.38),
                int(size * 0.70),
            ),
        )
        icon.put(
            check_color,
            to=(
                int(size * 0.38),
                int(size * 0.64),
                int(size * 0.78),
                int(size * 0.74),
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
            text="V5",
            fill="#0f172a",
            font=("Segoe UI", 11, "bold"),
        )

    def _build_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Main.TFrame", background=self.colors["bg"])
        style.configure("Panel.TFrame", background=self.colors["panel"])
        style.configure(
            "Card.TFrame",
            background=self.colors["card"],
            borderwidth=1,
            relief="flat",
            bordercolor=self.colors["border"],
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
            font=("Segoe UI", 18, "bold"),
            background=self.colors["bg"],
            foreground=self.colors["text"],
        )
        style.configure(
            "StatLabel.TLabel",
            font=("Segoe UI", 12),
            background=self.colors["card"],
            foreground=self.colors["muted"],
        )
        style.configure(
            "StatValue.TLabel",
            font=("Segoe UI", 20, "bold"),
            background=self.colors["card"],
            foreground=self.colors["text"],
        )
        style.configure(
            "Status.TLabel",
            font=("Segoe UI", 12, "bold"),
            background=self.colors["panel"],
            foreground=self.colors["text"],
        )
        style.configure(
            "Helper.TLabel",
            font=("Segoe UI", 9),
            background=self.colors["panel"],
            foreground=self.colors["muted"],
        )
        style.configure(
            "FieldLabel.TLabel",
            font=("Segoe UI", 10, "bold"),
            background=self.colors["panel"],
            foreground=self.colors["text"],
        )
        style.configure(
            "Badge.TLabel",
            font=("Segoe UI", 10, "bold"),
            background=self.colors["card"],
            foreground=self.colors["text"],
            padding=(10, 6),
        )
        def button_style(name, bg, fg, active=None, disabled=None, border=None, padding=8, bold=True):
            active = active or bg
            disabled = disabled or "#1f2937"
            font = ("Segoe UI", 11, "bold") if bold else ("Segoe UI", 10)
            kwargs = {
                "font": font,
                "background": bg,
                "foreground": fg,
                "padding": padding,
                "relief": "flat",
                "borderwidth": 0,
            }
            if border:
                kwargs.update({"bordercolor": border, "focuscolor": border})
            style.configure(name, **kwargs)
            style.map(
                name,
                background=[("active", active), ("disabled", disabled)],
                foreground=[("disabled", "#9ca3af")],
            )

        button_style("Accent.TButton", self.colors["accent"], "#0f172a", active=self.colors["accent2"], disabled="#6b7280")
        button_style("Ghost.TButton", self.colors["panel"], self.colors["text"], active="#1f2937", disabled="#1f2937", bold=False, padding=7)
        button_style("Outline.TButton", self.colors["panel"], self.colors["text"], active=self.colors["card"], disabled="#1f2937", border=self.colors["accent2"], bold=False, padding=7)
        button_style("Danger.TButton", self.colors["danger"], "#0f172a", active="#dc2626", disabled="#7f1d1d")
        style.configure(
            "Switch.TCheckbutton",
            background=self.colors["panel"],
            foreground=self.colors["text"],
            font=("Segoe UI", 10),
        )
        style.map("Switch.TCheckbutton", background=[("active", "#1f2937")])
        style.configure(
            "TEntry",
            fieldbackground=self.colors["panel"],
            foreground=self.colors["text"],
            insertcolor=self.colors["text"],
            bordercolor=self.colors["card"],
            padding=6,
        )
        style.map(
            "TEntry",
            fieldbackground=[("focus", "#111a2d")],
            bordercolor=[("focus", self.colors["accent2"])],
        )
        style.configure(
            "Section.TLabel",
            font=("Segoe UI", 12, "bold"),
            background=self.colors["bg"],
            foreground=self.colors["text"],
        )
        style.configure(
            "Pill.TLabel",
            font=("Segoe UI", 9, "bold"),
            background="#17233b",
            foreground=self.colors["accent2"],
            padding=(10, 4),
        )

    def _build_ui(self):
        main = ttk.Frame(self.root, style="Main.TFrame", padding=16)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(2, weight=1)

        header = ttk.Frame(main, style="Main.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        header.columnconfigure(2, weight=1)
        logo_canvas = tk.Canvas(
            header,
            width=60,
            height=60,
            bg=self.colors["bg"],
            highlightthickness=0,
            bd=0,
        )
        self._draw_brand_mark(logo_canvas, size=60)
        logo_canvas.grid(row=0, column=0, rowspan=2, padx=(0, 12), pady=(0, 8), sticky="w")
        title_block = ttk.Frame(header, style="Main.TFrame")
        title_block.grid(row=0, column=1, rowspan=2, sticky="w")
        title = ttk.Label(title_block, text="VoteBot 5 - DistroKid Spotlight", style="Title.TLabel")
        title.grid(row=0, column=0, sticky="w")
        pill_frame = ttk.Frame(title_block, style="Main.TFrame")
        pill_frame.grid(row=0, column=1, padx=(10, 0), sticky="w")
        ttk.Label(pill_frame, text="Headless hazır", style="Pill.TLabel").grid(row=0, column=0, padx=(0, 6))
        ttk.Label(pill_frame, text="Batch oy", style="Pill.TLabel").grid(row=0, column=1, padx=(0, 6))
        ttk.Label(pill_frame, text="Log kaydı", style="Pill.TLabel").grid(row=0, column=2)
        subtitle = ttk.Label(
            title_block,
            text="Stabil, hızlı, şeffaf otomatik oy",
            foreground=self.colors["muted"],
            background=self.colors["bg"],
            font=("Segoe UI", 11),
        )
        subtitle.grid(row=1, column=0, pady=(2, 6), sticky="w")
        tagline = ttk.Label(
            title_block,
            text="Başlat ve unut: otomatik sürücü kontrolü, batch oy ve güvenli loglama",
            foreground=self.colors["muted"],
            background=self.colors["bg"],
            font=("Segoe UI", 10),
        )
        tagline.grid(row=2, column=0, sticky="w")
        self.state_badge = tk.Label(
            header,
            text="Bekliyor",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=6,
        )
        self.state_badge.grid(row=0, column=2, rowspan=2, sticky="e")

        stats_wrapper = ttk.LabelFrame(main, text="Gösterge Paneli", style="Panel.TFrame", padding=12)
        stats_wrapper.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        stats_wrapper.columnconfigure(0, weight=1)
        stats_frame = ttk.Frame(stats_wrapper, style="Panel.TFrame")
        stats_frame.grid(row=0, column=0, sticky="nsew")
        stats_frame.columnconfigure((0, 1, 2, 3), weight=1)

        self._make_stat_card(stats_frame, 0, 0, "Toplam Oy", "0", "count")
        self._make_stat_card(stats_frame, 0, 1, "Hata", "0", "errors")
        self._make_stat_card(stats_frame, 0, 2, "Durum", "Bekliyor", "status")
        self._make_stat_card(stats_frame, 0, 3, "Süre", "00:00:00", "runtime")

        settings = ttk.LabelFrame(main, text="Ayarlar", style="Panel.TFrame", padding=12)
        settings.grid(row=1, column=1, sticky="nsew")
        settings.columnconfigure(1, weight=1)

        ttk.Label(
            settings,
            text="Hedef URL",
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=0, column=0, sticky="w", pady=(4, 0), padx=(0, 8))
        self.url_entry = ttk.Entry(settings)
        self.url_entry.insert(0, self.target_url)
        self.url_entry.grid(row=0, column=1, sticky="ew", pady=(4, 0))
        ttk.Label(
            settings,
            text="Oylama sayfasının bağlantısı",
            style="Helper.TLabel",
        ).grid(row=1, column=1, sticky="w", pady=(0, 6))

        ttk.Label(
            settings,
            text="Oy aralığı (sn)",
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=2, column=0, sticky="w", pady=(4, 0), padx=(0, 8))
        self.pause_entry = ttk.Entry(settings, width=10)
        self.pause_entry.insert(0, str(self.pause_between_votes))
        self.pause_entry.grid(row=2, column=1, sticky="w", pady=(4, 0))
        ttk.Label(
            settings,
            text="Her batch sonrası bekleme süresi",
            style="Helper.TLabel",
        ).grid(row=3, column=1, sticky="w", pady=(0, 6))

        ttk.Label(
            settings,
            text="Batch (kaç oy)",
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=4, column=0, sticky="w", pady=(4, 0), padx=(0, 8))
        self.batch_entry = ttk.Entry(settings, width=10)
        self.batch_entry.insert(0, str(self.batch_size))
        self.batch_entry.grid(row=4, column=1, sticky="w", pady=(4, 0))
        ttk.Label(
            settings,
            text="Tek seferde verilecek oy sayısı",
            style="Helper.TLabel",
        ).grid(row=5, column=1, sticky="w", pady=(0, 6))

        ttk.Label(
            settings,
            text="Zaman aşımı (sn)",
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=6, column=0, sticky="w", pady=(4, 0), padx=(0, 8))
        self.timeout_entry = ttk.Entry(settings, width=10)
        self.timeout_entry.insert(0, str(self.timeout_seconds))
        self.timeout_entry.grid(row=6, column=1, sticky="w", pady=(4, 0))
        ttk.Label(
            settings,
            text="Oy butonu görünmezse bekleme sınırı",
            style="Helper.TLabel",
        ).grid(row=7, column=1, sticky="w", pady=(0, 8))

        ttk.Label(
            settings,
            text="Maks hata (art arda)",
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=8, column=0, sticky="w", pady=(4, 0), padx=(0, 8))
        self.max_errors_entry = ttk.Entry(settings, width=10)
        self.max_errors_entry.insert(0, str(self.max_errors))
        self.max_errors_entry.grid(row=8, column=1, sticky="w", pady=(4, 0))
        ttk.Label(
            settings,
            text="Bu sayıya ulaşıldığında bekleme ve yeniden deneme yapılır.",
            style="Helper.TLabel",
        ).grid(row=9, column=1, sticky="w", pady=(0, 8))

        ttk.Label(
            settings,
            text="Paralel pencere",
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=10, column=0, sticky="w", pady=(4, 0), padx=(0, 8))
        self.parallel_entry = ttk.Entry(settings, width=10)
        self.parallel_entry.insert(0, str(self.parallel_workers))
        self.parallel_entry.grid(row=10, column=1, sticky="w", pady=(4, 0))
        ttk.Label(
            settings,
            text="Aynı anda açılacak tarayıcı sayısı (her biri tek oy).",
            style="Helper.TLabel",
        ).grid(row=11, column=1, sticky="w", pady=(0, 8))

        self.headless_var = tk.BooleanVar(value=self.headless)
        self.headless_check = ttk.Checkbutton(
            settings,
            text="Görünmez (headless) çalıştır",
            variable=self.headless_var,
            style="Switch.TCheckbutton",
        )
        self.headless_check.grid(row=12, column=0, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Label(
            settings,
            text="Kapalıysa tarayıcıyı görerek izleyebilirsiniz.",
            style="Helper.TLabel",
        ).grid(row=13, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.auto_driver_var = tk.BooleanVar(value=self.use_selenium_manager)
        self.auto_driver_check = ttk.Checkbutton(
            settings,
            text="ChromeDriver'ı Selenium Manager yönetsin",
            variable=self.auto_driver_var,
            style="Switch.TCheckbutton",
        )
        self.auto_driver_check.grid(row=14, column=0, columnspan=2, sticky="w", pady=(2, 0))
        ttk.Label(
            settings,
            text="Driver yoksa/uyumsuzsa otomatik indirir (internet gerekir).",
            style="Helper.TLabel",
        ).grid(row=15, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(
            settings,
            text="Oy buton seçicileri (satır satır CSS/XPath)",
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=16, column=0, sticky="nw", pady=(4, 0), padx=(0, 8))
        self.selectors_text = scrolledtext.ScrolledText(
            settings,
            height=4,
            width=40,
            background=self.colors["panel"],
            foreground=self.colors["text"],
            insertbackground=self.colors["text"],
            font=("Consolas", 9),
            borderwidth=1,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.colors["card"],
        )
        self.selectors_text.grid(row=16, column=1, sticky="ew", pady=(4, 0))
        selectors_helper = (
            "Örnekler: a[data-action='vote'], button[data-action='vote'], "
            "xpath://button[contains(.,'vote')]"
        )
        ttk.Label(settings, text=selectors_helper, style="Helper.TLabel").grid(
            row=17, column=1, sticky="w", pady=(0, 8)
        )
        for line in self.config.get("vote_selectors", []):
            self.selectors_text.insert(tk.END, f"{line}\n")

        actions = ttk.Frame(settings, style="Panel.TFrame")
        actions.grid(row=18, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        actions.columnconfigure((0, 1), weight=1)
        self.apply_btn = ttk.Button(
            actions,
            text="Ayarları Uygula",
            command=self.apply_settings,
            style="Ghost.TButton",
        )
        self.apply_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.defaults_btn = ttk.Button(
            actions,
            text="Varsayılanları Yükle",
            command=self.reset_to_defaults,
            style="Ghost.TButton",
        )
        self.defaults_btn.grid(row=0, column=1, sticky="ew")

        controls_wrap = ttk.LabelFrame(main, text="Eylemler", style="Panel.TFrame", padding=10)
        controls_wrap.grid(row=2, column=0, sticky="ew", padx=(0, 12), pady=(8, 0))
        controls_wrap.columnconfigure(0, weight=1)
        controls = ttk.Frame(controls_wrap, style="Panel.TFrame", padding=(0, 0))
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure((0, 1, 2, 3), weight=1)

        self.start_btn = ttk.Button(
            controls, text="Başlat", command=self.start_bot, style="Accent.TButton"
        )
        self.start_btn.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        self.stop_btn = ttk.Button(
            controls,
            text="Durdur",
            command=self.stop_bot,
            style="Ghost.TButton",
            state=tk.DISABLED,
        )
        self.stop_btn.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        self.preflight_btn = ttk.Button(
            controls, text="Ön kontrol", command=self.run_preflight, style="Ghost.TButton"
        )
        self.preflight_btn.grid(row=0, column=2, padx=4, pady=4, sticky="ew")
        self.logs_btn = ttk.Button(
            controls, text="Log klasörünü aç", command=self.open_logs, style="Ghost.TButton"
        )
        self.logs_btn.grid(row=0, column=3, padx=4, pady=4, sticky="ew")

        log_frame = ttk.LabelFrame(main, text="Log", style="Panel.TFrame", padding=12)
        log_frame.grid(row=2, column=1, sticky="nsew")
        log_frame.rowconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)

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
            log_frame,
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
        clear_btn = ttk.Button(log_frame, text="Log temizle", command=self.clear_log, style="Ghost.TButton")
        clear_btn.grid(row=2, column=0, sticky="e")
        self._set_form_state(False)

    def _make_stat_card(self, parent, row, col, title, value, key):
        card = ttk.Frame(parent, style="Card.TFrame", padding=12)
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        parent.rowconfigure(row, weight=1)
        parent.columnconfigure(col, weight=1)
        accent_bar = tk.Frame(card, bg=self.colors["accent2"], width=4, height=60)
        accent_bar.grid(row=0, column=0, rowspan=2, sticky="nsw", padx=(0, 10))
        ttk.Label(card, text=title, style="StatLabel.TLabel").grid(row=0, column=1, sticky="w")
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

    def _schedule(self, func):
        self.root.after(0, func)

    def _update_runtime(self):
        if self.start_time and self.is_running:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.runtime_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.root.after(1000, self._update_runtime)

    def _register_driver(self, driver):
        with self._driver_lock:
            self.active_drivers.add(driver)

    def _unregister_driver(self, driver):
        with self._driver_lock:
            self.active_drivers.discard(driver)

    def _cleanup_drivers(self):
        with self._driver_lock:
            drivers = list(self.active_drivers)
            self.active_drivers.clear()
        for driver in drivers:
            try:
                driver.quit()
            except Exception:
                pass

    def log_message(self, message, level="info"):
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
        def apply():
            self.status_label.config(text=text)
            badge_tone = tone or ("running" if "Çalış" in text or "Oy ver" in text else "idle")
            self._set_state_badge(text, badge_tone)

        self._schedule(apply)

    def increment_count(self):
        self.vote_count += 1
        self._schedule(
            lambda: (
                self.count_label.config(text=str(self.vote_count)),
                self._refresh_stat_colors(),
            )
        )

    def increment_error(self):
        self.error_count += 1
        self._schedule(
            lambda: (
                self.error_label.config(text=str(self.error_count)),
                self._refresh_stat_colors(),
            )
        )

    def clear_log(self):
        self.log_records.clear()
        self.success_count = 0
        self.failure_count = 0
        self.log_area.delete(1.0, tk.END)
        self._update_log_counts_badges()
        self.log_message("Log temizlendi")

    def _set_state_badge(self, text, tone="idle"):
        colors = {
            "running": (self.colors["accent2"], "#0f172a"),
            "success": (self.colors["success"], "#0f172a"),
            "stopped": (self.colors["error"], "#0f172a"),
            "idle": (self.colors["card"], self.colors["text"]),
        }
        bg, fg = colors.get(tone, colors["idle"])
        self.state_badge.config(text=text, bg=bg, fg=fg)

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
        for btn in [self.apply_btn, self.defaults_btn, self.preflight_btn]:
            btn.state(state_flag)
        for check in [self.headless_check, self.auto_driver_check]:
            if running:
                check.state(["disabled"])
            else:
                check.state(["!disabled"])
        if running:
            self.selectors_text.config(state=tk.DISABLED)
        else:
            self.selectors_text.config(state=tk.NORMAL)

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
            problems.append("chromedriver bulunamadı. config.json'daki 'paths.driver' yolunu kontrol edin.")
        if not chrome_path or not chrome_path.exists():
            if self.use_selenium_manager:
                self.log_message(
                    "Chrome yolu bulunamadı; Selenium Manager Chrome for Testing deneyecek.", level="info"
                )
            else:
                problems.append("Chrome bulunamadı. 'paths.chrome' yolunu kontrol edin.")
        if problems:
            if show_message:
                messagebox.showerror("Yol Hatası", "\n".join(problems))
            for msg in problems:
                self.log_message(msg, level="error")
            return False
        if not self.use_selenium_manager and not self._check_version_compatibility(driver_path, chrome_path):
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

    def get_chrome_options(self):
        chrome_options = Options()
        if self.chrome_path:
            chrome_options.binary_location = self.chrome_path
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--remote-allow-origins=*")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--log-level=3")
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
            },
        )
        return chrome_options

    def create_driver(self):
        options = self.get_chrome_options()
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
        if self.is_running:
            return
        if not self._update_settings_from_form(persist=True, notify=False):
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
        self.worker = threading.Thread(target=self.run_bot, daemon=True)
        self.worker.start()

    def stop_bot(self):
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

    def run_bot(self):
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
        self.update_status("Oy veriliyor", tone="running")
        successes = 0
        failures = 0
        prepared = []
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = []
            for i in range(self.batch_size):
                if self._stop_event.is_set():
                    break
                futures.append(executor.submit(self._prepare_vote_session, i))
            for future in as_completed(futures):
                if self._stop_event.is_set():
                    break
                try:
                    session = future.result()
                except Exception as exc:
                    self.logger.exception("Oy hazırlık hatası", exc_info=exc)
                    session = None
                if session:
                    prepared.append(session)
                else:
                    self.increment_error()
                    failures += 1

        if self._stop_event.is_set():
            for driver, _ in prepared:
                try:
                    driver.quit()
                except Exception:
                    pass
                self._unregister_driver(driver)
            return False

        for idx, (driver, vote_button) in enumerate(prepared, start=1):
            if self._stop_event.is_set():
                break
            try:
                vote_button.click()
                self.log_message(
                    f"Oy verildi (pencere {idx}/{self.batch_size})", level="success"
                )
                self.increment_count()
                successes += 1
            except Exception:
                try:
                    driver.refresh()
                    wait = WebDriverWait(driver, self.timeout_seconds)
                    refreshed_btn = self._locate_vote_button(driver, wait)
                    refreshed_btn.click()
                    self.log_message(
                        f"Oy verildi (yeniden deneme, pencere {idx}/{self.batch_size})",
                        level="success",
                    )
                    self.increment_count()
                    successes += 1
                except TimeoutException:
                    self.log_message("Oy butonu zaman aşımına uğradı.", level="error")
                    self.increment_error()
                    failures += 1
                except Exception as exc:
                    self.logger.exception("Oy verme hatası", exc_info=exc)
                    self.log_message(f"Beklenmeyen hata: {exc}", level="error")
                    self.increment_error()
                    failures += 1
            finally:
                try:
                    driver.quit()
                except Exception:
                    pass
                self._unregister_driver(driver)

        if successes == 0:
            self.log_message(f"Batch tamamlanamadı. Başarılı: {successes}, Hata: {failures}", level="error")
            return False
        if failures:
            self.log_message(
                f"Batch kısmen tamamlandı. Başarılı: {successes}, Hata: {failures}",
                level="success",
            )
        else:
            self.log_message(f"Batch tamamlandı. Başarılı: {successes}, Hata: {failures}", level="success")
        self.update_status("Bekliyor", tone="idle")
        return True

    def _prepare_vote_session(self, batch_index):
        driver = self.create_driver()
        if not driver:
            return None
        self._register_driver(driver)
        keep_driver = False
        if self._stop_event.is_set():
            try:
                driver.quit()
            except Exception:
                pass
            self._unregister_driver(driver)
            return None
        driver.set_page_load_timeout(self.timeout_seconds)
        wait = WebDriverWait(driver, self.timeout_seconds)
        try:
            driver.get(self.target_url)
            self._wait_for_document_ready(driver, timeout=self.timeout_seconds)
            vote_button = self._locate_vote_button(driver, wait)
            keep_driver = True
            return driver, vote_button
        except TimeoutException:
            self.log_message("Oy butonu zaman aşımına uğradı (hazırlık).", level="error")
        except Exception as exc:
            self.logger.exception("Oy hazırlık hatası", exc_info=exc)
            self.log_message(f"Beklenmeyen hata (hazırlık): {exc}", level="error")
        finally:
            if not keep_driver:
                try:
                    driver.quit()
                except Exception:
                    pass
                self._unregister_driver(driver)
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
        if self._validate_paths(show_message=True):
            messagebox.showinfo("Ön kontrol", "Yollar ve ayarlar geçerli görünüyor.")
            self.log_message("Ön kontrol başarılı")

    def reset_to_defaults(self):
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
        self.vote_selectors = self._build_vote_selectors(defaults.get("vote_selectors"))
        self.backoff_seconds = defaults["backoff_seconds"]
        self.backoff_cap_seconds = defaults["backoff_cap_seconds"]
        self.selectors_text.config(state=tk.NORMAL)
        self.selectors_text.delete("1.0", tk.END)
        for line in defaults.get("vote_selectors", []):
            self.selectors_text.insert(tk.END, f"{line}\n")
        self.log_message("Varsayılan ayarlar yüklendi.")
        self.apply_settings()

    def apply_settings(self):
        return self._update_settings_from_form(persist=True, notify=True)

    def _update_settings_from_form(self, persist=False, notify=True):
        try:
            pause = float(self.pause_entry.get())
            batch = max(1, int(self.batch_entry.get()))
            timeout_val = max(5, int(self.timeout_entry.get()))
            max_err = max(1, int(self.max_errors_entry.get()))
            parallel = max(1, min(10, int(self.parallel_entry.get())))
            selector_lines = [
                line.strip()
                for line in self.selectors_text.get("1.0", tk.END).splitlines()
                if line.strip()
            ]
        except ValueError:
            messagebox.showerror("Hata", "Sayısal alanlar geçerli ve pozitif olmalı.")
            self.log_message("Ayarlar okunamadı: sayısal alan hatalı.", level="error")
            return False

        if pause <= 0:
            messagebox.showerror("Hata", "Oy aralığı 0'dan büyük olmalı.")
            self.log_message("Geçersiz oy aralığı değeri girildi.", level="error")
            return False

        url = self.url_entry.get().strip()
        if not url or not url.startswith(("http://", "https://")):
            messagebox.showerror("Hata", "Geçerli bir hedef URL girin (http/https ile).")
            self.log_message("Geçersiz hedef URL girildi.", level="error")
            return False

        self.target_url = url
        self.pause_between_votes = pause
        self.batch_size = batch
        self.timeout_seconds = timeout_val
        self.max_errors = max_err
        self.parallel_workers = parallel
        self.headless = bool(self.headless_var.get())
        self.use_selenium_manager = bool(self.auto_driver_var.get())
        self.config["target_url"] = self.target_url
        self.config["pause_between_votes"] = self.pause_between_votes
        self.config["batch_size"] = self.batch_size
        self.config["max_errors"] = self.max_errors
        self.config["parallel_workers"] = self.parallel_workers
        self.config["headless"] = self.headless
        self.config["timeout_seconds"] = self.timeout_seconds
        self.config["use_selenium_manager"] = self.use_selenium_manager
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
                with self.config_path.open("w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=4)
                if notify:
                    self.log_message("Ayarlar kaydedildi.")
                    messagebox.showinfo("Ayarlar", "Ayarlar güncellendi.")
            except Exception as exc:
                self.log_message(f"Ayarlar kaydedilemedi: {exc}", level="error")
                messagebox.showerror("Hata", f"Ayarlar kaydedilemedi: {exc}")
                return False
        return True

    def open_logs(self):
        try:
            os.startfile(self.log_dir)
        except Exception:
            messagebox.showinfo("Log klasörü", str(self.log_dir))

    def on_close(self):
        self.stop_bot()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = VoteBot5(root)
    root.mainloop()


if __name__ == "__main__":
    main()

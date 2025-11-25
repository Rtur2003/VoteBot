import json
import logging
import os
import subprocess
import threading
import time
from datetime import datetime
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
        self.config_path = self._find_config_path()
        self.config = self._load_config()
        self.paths = self.config.setdefault("paths", {})

        self.target_url = self.config.get(
            "target_url", "https://distrokid.com/spotlight/hasanarthuraltunta/vote/"
        )
        self.pause_between_votes = float(self.config.get("pause_between_votes", 3))
        self.batch_size = max(1, int(self.config.get("batch_size", 1)))
        self.max_errors = max(1, int(self.config.get("max_errors", 3)))
        self.headless = bool(self.config.get("headless", True))
        self.timeout_seconds = int(self.config.get("timeout_seconds", 15))

        self.driver_path = None
        self.chrome_path = None

        self.is_running = False
        self.vote_count = 0
        self.error_count = 0
        self.start_time = None
        self.worker = None
        self._stop_event = threading.Event()

        self.log_dir = self._resolve_logs_dir()
        self.logger = self._build_logger()

        self.colors = {
            "bg": "#0f172a",
            "panel": "#0b1220",
            "card": "#111827",
            "accent": "#f59e0b",
            "accent2": "#22d3ee",
            "text": "#e5e7eb",
            "muted": "#94a3b8",
            "error": "#f87171",
            "success": "#34d399",
        }

        self._build_styles()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._update_runtime()

    def _find_config_path(self):
        candidates = [
            self.base_dir / "config.json",
            self.code_dir / "config.json",
        ]
        for path in candidates:
            if path.exists():
                return path
        return candidates[0]

    def _load_config(self):
        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "paths": {},
                "target_url": "https://distrokid.com/spotlight/hasanarthuraltunta/vote/",
                "pause_between_votes": 3,
                "batch_size": 1,
                "max_errors": 3,
                "headless": True,
                "timeout_seconds": 15,
            }

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
        file_handler = logging.FileHandler(self.log_dir / "votebot5.log", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def _build_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Main.TFrame", background=self.colors["bg"])
        style.configure("Panel.TFrame", background=self.colors["panel"])
        style.configure("Card.TFrame", background=self.colors["card"])
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
            "Accent.TButton",
            font=("Segoe UI", 11, "bold"),
            background=self.colors["accent"],
            foreground="#0f172a",
            padding=8,
        )
        style.map(
            "Accent.TButton",
            background=[("active", self.colors["accent2"]), ("disabled", "#6b7280")],
        )
        style.configure(
            "Ghost.TButton",
            font=("Segoe UI", 10),
            background=self.colors["panel"],
            foreground=self.colors["text"],
            padding=6,
        )
        style.map(
            "Ghost.TButton",
            background=[("active", "#1f2937"), ("disabled", "#1f2937")],
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
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        title = ttk.Label(header, text="VoteBot 5 – DistroKid Spotlight", style="Title.TLabel")
        title.grid(row=0, column=0, sticky="w")
        subtitle = ttk.Label(
            header,
            text="Stabil, hızlı, şeffaf otomatik oy",
            foreground=self.colors["muted"],
            background=self.colors["bg"],
            font=("Segoe UI", 11),
        )
        subtitle.grid(row=1, column=0, pady=(2, 12), sticky="w")

        stats_frame = ttk.Frame(main, style="Main.TFrame")
        stats_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
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
            text="Hedef URL:",
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=0, column=0, sticky="w", pady=4, padx=(0, 8))
        self.url_entry = ttk.Entry(settings)
        self.url_entry.insert(0, self.target_url)
        self.url_entry.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(
            settings,
            text="Oy aralığı (sn):",
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=1, column=0, sticky="w", pady=4, padx=(0, 8))
        self.pause_entry = ttk.Entry(settings, width=8)
        self.pause_entry.insert(0, str(self.pause_between_votes))
        self.pause_entry.grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(
            settings,
            text="Batch (kaç oy):",
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=2, column=0, sticky="w", pady=4, padx=(0, 8))
        self.batch_entry = ttk.Entry(settings, width=8)
        self.batch_entry.insert(0, str(self.batch_size))
        self.batch_entry.grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(
            settings,
            text="Zaman aşımı (sn):",
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=3, column=0, sticky="w", pady=4, padx=(0, 8))
        self.timeout_entry = ttk.Entry(settings, width=8)
        self.timeout_entry.insert(0, str(self.timeout_seconds))
        self.timeout_entry.grid(row=3, column=1, sticky="w", pady=4)

        self.headless_var = tk.BooleanVar(value=self.headless)
        headless_check = ttk.Checkbutton(
            settings,
            text="Görünmez (headless) çalıştır",
            variable=self.headless_var,
        )
        headless_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=4)

        apply_btn = ttk.Button(
            settings,
            text="Ayarları Uygula",
            command=self.apply_settings,
            style="Ghost.TButton",
        )
        apply_btn.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        controls = ttk.Frame(main, style="Main.TFrame", padding=(0, 8))
        controls.grid(row=2, column=0, sticky="ew", padx=(0, 12))
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

        log_frame = ttk.LabelFrame(main, text="Log", style="Panel.TFrame", padding=8)
        log_frame.grid(row=2, column=1, sticky="nsew")
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_area = scrolledtext.ScrolledText(
            log_frame,
            width=60,
            height=18,
            background="#0b1220",
            foreground=self.colors["text"],
            insertbackground=self.colors["text"],
            font=("Consolas", 10),
        )
        self.log_area.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        clear_btn = ttk.Button(log_frame, text="Log temizle", command=self.clear_log, style="Ghost.TButton")
        clear_btn.grid(row=1, column=0, sticky="e")

    def _make_stat_card(self, parent, row, col, title, value, key):
        card = ttk.Frame(parent, style="Card.TFrame", padding=12)
        card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        parent.rowconfigure(row, weight=1)
        parent.columnconfigure(col, weight=1)
        ttk.Label(card, text=title, style="StatLabel.TLabel").grid(row=0, column=0, sticky="w")
        label = ttk.Label(card, text=value, style="StatValue.TLabel")
        label.grid(row=1, column=0, sticky="w")
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

    def log_message(self, message, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")

        def append():
            self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_area.see(tk.END)

        self._schedule(append)
        if level == "error":
            self.logger.error(message)
        else:
            self.logger.info(message)

    def update_status(self, text):
        self._schedule(lambda: self.status_label.config(text=text))

    def increment_count(self):
        self.vote_count += 1
        self._schedule(lambda: self.count_label.config(text=str(self.vote_count)))

    def increment_error(self):
        self.error_count += 1
        self._schedule(lambda: self.error_label.config(text=str(self.error_count)))

    def clear_log(self):
        self.log_area.delete(1.0, tk.END)
        self.log_message("Log temizlendi")

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
        driver_path = self._resolve_driver_path()
        chrome_path = self._resolve_chrome_path()
        problems = []
        if not driver_path or not driver_path.exists():
            problems.append("chromedriver bulunamadı. config.json'daki 'paths.driver' yolunu kontrol edin.")
        if not chrome_path or not chrome_path.exists():
            problems.append("Chrome bulunamadı. 'paths.chrome' yolunu kontrol edin.")
        if problems:
            if show_message:
                messagebox.showerror("Yol Hatası", "\n".join(problems))
            for msg in problems:
                self.log_message(msg, level="error")
            return False
        if not self._check_version_compatibility(driver_path, chrome_path):
            if show_message:
                messagebox.showerror(
                    "Sürüm Uyumsuzluğu",
                    "ChromeDriver ve Chrome sürümleri farklı. Lütfen sürümü eşleştirin.",
                )
            return False
        self.driver_path = str(driver_path)
        self.chrome_path = str(chrome_path)
        self.log_message(f"Sürücü: {self.driver_path}")
        self.log_message(f"Chrome: {self.chrome_path}")
        return True

    def get_chrome_options(self):
        chrome_options = Options()
        chrome_options.binary_location = self.chrome_path
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        return chrome_options

    def create_driver(self):
        try:
            service = Service(executable_path=self.driver_path)
            return webdriver.Chrome(service=service, options=self.get_chrome_options())
        except WebDriverException as exc:
            self.log_message(f"ChromeDriver başlatılamadı: {exc}", level="error")
            return None

    def start_bot(self):
        if self.is_running:
            return
        if not self._validate_paths(show_message=True):
            return
        self.is_running = True
        self._stop_event.clear()
        self.start_time = time.time()
        self.log_message("Bot başlatıldı")
        self.update_status("Çalışıyor")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.worker = threading.Thread(target=self.run_bot, daemon=True)
        self.worker.start()

    def stop_bot(self):
        if not self.is_running:
            return
        self.log_message("Bot durduruluyor...")
        self.is_running = False
        self._stop_event.set()
        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=1.0)
        self.update_status("Durduruldu")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def run_bot(self):
        consecutive_errors = 0
        while not self._stop_event.is_set():
            batch_ok = self.run_batch()
            if batch_ok:
                consecutive_errors = 0
            else:
                consecutive_errors += 1
                self.increment_error()
            if consecutive_errors >= self.max_errors:
                self.log_message(
                    "Çok hata alındı, 5 saniye bekleniyor ve yeniden denenecek.",
                    level="error",
                )
                consecutive_errors = 0
                if not self._sleep_with_checks(5):
                    break
            if not self._sleep_with_checks(self.pause_between_votes):
                break
        self.is_running = False
        self._schedule(lambda: self.update_status("Durduruldu"))
        self._schedule(lambda: self.start_btn.config(state=tk.NORMAL))
        self._schedule(lambda: self.stop_btn.config(state=tk.DISABLED))

    def run_batch(self):
        self.update_status("Oy veriliyor")
        for i in range(self.batch_size):
            if self._stop_event.is_set():
                break
            driver = self.create_driver()
            if not driver:
                return False
            try:
                driver.get(self.target_url)
                wait = WebDriverWait(driver, self.timeout_seconds)
                vote_button = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            '//*[@id="distroListContainer"]/div[3]/div[3]/div[1]/div[1]/div[2]/div[2]/a[1]'
                        )
                    )
                )
                vote_button.click()
                self.log_message(f"Oy verildi (batch {i + 1}/{self.batch_size})", level="info")
                self.increment_count()
            except TimeoutException:
                self.log_message("Oy butonu zaman aşımına uğradı.", level="error")
                return False
            except Exception as exc:
                self.log_message(f"Beklenmeyen hata: {exc}", level="error")
                return False
            finally:
                driver.quit()
        self.update_status("Bekliyor")
        return True

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

    def apply_settings(self):
        try:
            pause = float(self.pause_entry.get())
            batch = max(1, int(self.batch_entry.get()))
            timeout_val = max(5, int(self.timeout_entry.get()))
        except ValueError:
            messagebox.showerror("Hata", "Sayısal alanlar geçerli bir sayı olmalı.")
            return
        self.target_url = self.url_entry.get().strip()
        self.pause_between_votes = pause
        self.batch_size = batch
        self.timeout_seconds = timeout_val
        self.headless = bool(self.headless_var.get())
        self.config["target_url"] = self.target_url
        self.config["pause_between_votes"] = self.pause_between_votes
        self.config["batch_size"] = self.batch_size
        self.config["max_errors"] = self.max_errors
        self.config["headless"] = self.headless
        self.config["timeout_seconds"] = self.timeout_seconds
        self.config.setdefault("paths", self.paths)
        self.config["paths"].setdefault("driver", self.paths.get("driver", ""))
        self.config["paths"].setdefault("chrome", self.paths.get("chrome", ""))
        try:
            with self.config_path.open("w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            self.log_message("Ayarlar kaydedildi.")
            messagebox.showinfo("Ayarlar", "Ayarlar güncellendi.")
        except Exception as exc:
            self.log_message(f"Ayarlar kaydedilemedi: {exc}", level="error")
            messagebox.showerror("Hata", f"Ayarlar kaydedilemedi: {exc}")

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

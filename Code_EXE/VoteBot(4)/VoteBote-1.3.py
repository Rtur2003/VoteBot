import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
import json
import sys
import os
import logging
from pathlib import Path

class EnhancedVoteBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced DistroKid Vote Bot")
        self.root.geometry("1024x768")
        self.root.minsize(1024, 768)
        
        # Default paths
        self.default_paths = {
            'chrome': r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            'driver': r"C:\Users\MONSTER\Desktop\VoteBot\chromedriver.exe",
            'logs': r"logs",
            'config': r"config.json"
        }
        
        # Variables
        self.num_parallel_browsers = 5  # Kaç tarayıcı çalıştırılacağı
        self.is_running = False
        self.vote_count = 0
        self.error_count = 0
        self.success_rate = 0.0
        self.current_thread = None
        self.start_time = None
        self.pause_between_votes = 3
        self.max_errors = 3
        self.target_url = "https://distrokid.com/spotlight/hasanarthuraltunta/vote/"
        
        # Load config
        self.load_config()
        
        # Setup logging
        self.setup_logging()
        
        # Create GUI
        self.create_styles()
        self.create_main_interface()
        
        # Start update timers
        self.update_runtime()
        self.update_stats()
        
    def setup_logging(self):
        log_dir = Path(self.default_paths['logs'])
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"votelog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
    def load_config(self):
        try:
            with open(self.default_paths['config'], 'r') as f:
                config = json.load(f)
                self.default_paths.update(config.get('paths', {}))
                self.pause_between_votes = config.get('pause_between_votes', 3)
                self.max_errors = config.get('max_errors', 3)
                self.target_url = config.get('target_url', self.target_url)
        except FileNotFoundError:
            self.save_config()
            
    def save_config(self):
        config = {
            'paths': self.default_paths,
            'pause_between_votes': self.pause_between_votes,
            'max_errors': self.max_errors,
            'target_url': self.target_url
        }
        with open(self.default_paths['config'], 'w') as f:
            json.dump(config, f, indent=4)
            
    def create_styles(self):
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Helvetica', 18, 'bold'))
        style.configure('Header.TLabel', font=('Helvetica', 14, 'bold'))
        style.configure('Stats.TLabel', font=('Helvetica', 12))
        style.configure('Control.TButton', font=('Helvetica', 11))
        style.configure('Status.TLabel', font=('Helvetica', 12, 'bold'))
        
    def create_main_interface(self):
        # Main container with padding
        self.main_container = ttk.Frame(self.root, padding="20")
        self.main_container.grid(row=0, column=0, sticky="nsew")
        
        # Create all sections
        self.create_header_section()
        self.create_status_section()
        self.create_settings_section()
        self.create_log_section()
        self.create_control_section()
        
        # Configure weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_container.columnconfigure(1, weight=1)
        self.main_container.rowconfigure(3, weight=1)
        
    def create_header_section(self):
        header_frame = ttk.Frame(self.main_container)
        header_frame.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        title = ttk.Label(header_frame, text="Enhanced DistroKid Vote Bot", style='Title.TLabel')
        title.pack(pady=(0, 10))
        
        subtitle = ttk.Label(header_frame, 
                           text="Automated Voting System with Advanced Controls",
                           style='Header.TLabel')
        subtitle.pack()
        
    def create_status_section(self):
        status_frame = ttk.LabelFrame(self.main_container, text="Statistics & Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Create 2x4 grid for stats
        for i in range(2):
            status_frame.columnconfigure(i*2+1, weight=1)
            
        # Vote Count
        ttk.Label(status_frame, text="Total Votes:", style='Stats.TLabel').grid(row=0, column=0, padx=5, pady=5)
        self.vote_label = ttk.Label(status_frame, text="0", style='Stats.TLabel')
        self.vote_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Error Count
        ttk.Label(status_frame, text="Errors:", style='Stats.TLabel').grid(row=0, column=2, padx=5, pady=5)
        self.error_label = ttk.Label(status_frame, text="0", style='Stats.TLabel')
        self.error_label.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Success Rate
        ttk.Label(status_frame, text="Success Rate:", style='Stats.TLabel').grid(row=1, column=0, padx=5, pady=5)
        self.success_label = ttk.Label(status_frame, text="0%", style='Stats.TLabel')
        self.success_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Runtime
        ttk.Label(status_frame, text="Runtime:", style='Stats.TLabel').grid(row=1, column=2, padx=5, pady=5)
        self.runtime_label = ttk.Label(status_frame, text="00:00:00", style='Stats.TLabel')
        self.runtime_label.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Status
        ttk.Label(status_frame, text="Status:", style='Stats.TLabel').grid(row=2, column=0, padx=5, pady=5)
        self.status_label = ttk.Label(status_frame, text="Ready", style='Status.TLabel')
        self.status_label.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="w")
        
    def create_settings_section(self):
        settings_frame = ttk.LabelFrame(self.main_container, text="Settings", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Chrome Path
        ttk.Label(settings_frame, text="Chrome Path:").grid(row=0, column=0, padx=5, pady=5)
        self.chrome_path_var = tk.StringVar(value=self.default_paths['chrome'])
        chrome_entry = ttk.Entry(settings_frame, textvariable=self.chrome_path_var, width=50)
        chrome_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(settings_frame, text="Browse", 
                  command=lambda: self.browse_file('chrome', 'chrome_path_var')).grid(row=0, column=2, padx=5)
        
        # Driver Path
        ttk.Label(settings_frame, text="Driver Path:").grid(row=1, column=0, padx=5, pady=5)
        self.driver_path_var = tk.StringVar(value=self.default_paths['driver'])
        driver_entry = ttk.Entry(settings_frame, textvariable=self.driver_path_var, width=50)
        driver_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(settings_frame, text="Browse", 
                  command=lambda: self.browse_file('driver', 'driver_path_var')).grid(row=1, column=2, padx=5)
        
        # URL Entry
        ttk.Label(settings_frame, text="Target URL:").grid(row=2, column=0, padx=5, pady=5)
        self.url_var = tk.StringVar(value=self.target_url)
        url_entry = ttk.Entry(settings_frame, textvariable=self.url_var, width=50)
        url_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Advanced Settings
        advanced_frame = ttk.Frame(settings_frame)
        advanced_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Pause Between Votes
        ttk.Label(advanced_frame, text="Pause Between Votes (sec):").grid(row=0, column=0, padx=5)
        self.pause_var = tk.StringVar(value=str(self.pause_between_votes))
        pause_spinbox = ttk.Spinbox(advanced_frame, from_=1, to=60, width=5, textvariable=self.pause_var)
        pause_spinbox.grid(row=0, column=1, padx=5)
        
        # Max Errors
        ttk.Label(advanced_frame, text="Max Consecutive Errors:").grid(row=0, column=2, padx=5)
        self.max_errors_var = tk.StringVar(value=str(self.max_errors))
        error_spinbox = ttk.Spinbox(advanced_frame, from_=1, to=10, width=5, textvariable=self.max_errors_var)
        error_spinbox.grid(row=0, column=3, padx=5)
        
    def create_log_section(self):
        log_frame = ttk.LabelFrame(self.main_container, text="Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        
        # Log Area
        self.log_area = scrolledtext.ScrolledText(log_frame, height=15, font=('Courier', 10))
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
    def create_control_section(self):
        control_frame = ttk.Frame(self.main_container, padding="10")
        control_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        # Control Buttons
        self.start_button = ttk.Button(control_frame, text="Start", command=self.start_bot, 
                                     style='Control.TButton', width=15)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_bot,
                                    style='Control.TButton', width=15, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        self.clear_button = ttk.Button(control_frame, text="Clear Log", command=self.clear_log,
                                     style='Control.TButton', width=15)
        self.clear_button.grid(row=0, column=2, padx=5)
        
        self.save_button = ttk.Button(control_frame, text="Save Settings", command=self.save_settings,
                                    style='Control.TButton', width=15)
        self.save_button.grid(row=0, column=3, padx=5)
        
    def browse_file(self, path_type, var_name):
        filetypes = [("Executable files", "*.exe")] if path_type in ['chrome', 'driver'] else [("All files", "*.*")]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            getattr(self, var_name).set(filename)
            self.default_paths[path_type] = filename
            
    def save_settings(self):
        try:
            self.pause_between_votes = int(self.pause_var.get())
            self.max_errors = int(self.max_errors_var.get())
            self.target_url = self.url_var.get()
            self.save_config()
            self.log_message("Settings saved successfully")
        except ValueError as e:
            messagebox.showerror("Error", "Invalid input in settings")
            
    def update_runtime(self):
        if self.start_time and self.is_running:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.runtime_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.root.after(1000, self.update_runtime)
        
    def update_stats(self):
        if self.vote_count > 0:
            success_rate = ((self.vote_count - self.error_count) / self.vote_count) * 100
            self.success_rate = round(success_rate, 2)
            self.success_label.config(text=f"{self.success_rate}%")
        self.root.after(5000, self.update_stats)
        
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_area.insert(tk.END, log_entry)
        self.log_area.see(tk.END)
        logging.info(message)
        
    def clear_log(self):
        self.log_area.delete(1.0, tk.END)
        self.log_message("Log cleared")
        
    def update_status(self, status):
        self.status_label.config(text=status)
        self.log_message(f"Status: {status}")
        
    def update_count(self):
        self.vote_count += 1
        self.vote_label.config(text=str(self.vote_count))
        
    def update_error_count(self):
        self.error_count += 1
        self.error_label.config(text=str(self.error_count))
        
    def get_chrome_options(self):
        chrome_options = Options()
        chrome_options.binary_location = self.chrome_path_var.get()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        return chrome_options
        
    def validate_settings(self):
        if not os.path.exists(self.chrome_path_var.get()):
            raise ValueError("Chrome executable not found")
        if not os.path.exists(self.driver_path_var.get()):
            raise ValueError("ChromeDriver not found")
        if not self.url_var.get().startswith("https://"):
            raise ValueError("Invalid URL format")
            
    def start_bot(self):
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.update_status("Çalışıyor")
        
        # Birden fazla thread başlat
        for i in range(self.num_parallel_browsers):
            thread = threading.Thread(target=self.bot_loop)
            thread.daemon = True
            thread.start()
            
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.update_status("Running")
            
            # Disable settings while running
            self.disable_settings()
            
            self.current_thread = threading.Thread(target=self.bot_loop)
            self.current_thread.daemon = True
            self.current_thread.start()
            
    def stop_bot(self):
        if self.is_running:
            self.is_running = False
            self.update_status("Stopping...")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            # Re-enable settings after stopping
            self.enable_settings()
            
    def disable_settings(self):
        for child in self.main_container.winfo_children():
            if isinstance(child, ttk.LabelFrame) and child.cget("text") == "Settings":
                for widget in child.winfo_children():
                    if isinstance(widget, (ttk.Entry, ttk.Spinbox, ttk.Button)):
                        widget.configure(state='disabled')
                        
    def enable_settings(self):
        for child in self.main_container.winfo_children():
            if isinstance(child, ttk.LabelFrame) and child.cget("text") == "Settings":
                for widget in child.winfo_children():
                    if isinstance(widget, (ttk.Entry, ttk.Spinbox, ttk.Button)):
                        widget.configure(state='normal')
                        
    def bot_loop(self):
        while self.is_running:
            browser = None
            try:
                # Tarayıcıyı başlat
                service = Service(executable_path=self.driver_path_var.get())
                browser = webdriver.Chrome(service=service, options=self.get_chrome_options())
                
                # Hedef URL'ye git
                browser.get(self.target_url)
                
                # Oy butonunu tıkla
                button = WebDriverWait(browser, 10).until(
                    EC.element_to_be_clickable((By.XPATH, 
                        '//*[@id="distroListContainer"]/div[3]/div[3]/div[1]/div[1]/div[2]/div[2]/a[1]'))
                )
                button.click()
                
                # Oy sayısını güncelle
                self.update_count()
                self.log_message("Oy başarıyla gönderildi.")
                
            except Exception as e:
                # Hata durumunda hata sayısını güncelle
                self.update_error_count()
                self.log_message(f"Hata: {e}")
                
            finally:
                # Tarayıcıyı kapat
                if browser:
                    try:
                        browser.quit()
                        self.log_message("Tarayıcı kapatıldı.")
                    except Exception as e:
                        self.log_message(f"Tarayıcı kapatılamadı: {e}")
                
                # Bekleme süresi
                time.sleep(self.pause_between_votes)



def main():
    try:
        root = tk.Tk()
        app = EnhancedVoteBotGUI(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        messagebox.showerror("Error", f"Application error: {str(e)}")
        
if __name__ == "__main__":
    main()
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
import sys
import os

class VoteBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DistroKid Vote Bot")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # Paths
        self.chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.driver_path = r"C:\Users\MONSTER\Desktop\VoteBot\chromedriver.exe"
        
        # Variables
        self.is_running = False
        self.vote_count = 0
        self.current_thread = None
        self.start_time = None
        self.error_count = 0
        
        # Create GUI elements
        self.create_styles()
        self.create_widgets()
        
    def create_styles(self):
        style = ttk.Style()
        style.configure('Stats.TLabel', font=('Helvetica', 14, 'bold'))
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('Big.TButton', font=('Helvetica', 12))

    def create_widgets(self):
        # Main container
        main_container = ttk.Frame(self.root, padding="20")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_container, text="DistroKid Oy Botunu", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Stats Frame
        stats_frame = ttk.LabelFrame(main_container, text="İstatistikler", padding="10")
        stats_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Stats Grid
        # Vote Count
        vote_title = ttk.Label(stats_frame, text="Toplam Oy:", style='Stats.TLabel')
        vote_title.grid(row=0, column=0, padx=10, pady=5)
        self.count_label = ttk.Label(stats_frame, text="0", style='Stats.TLabel')
        self.count_label.grid(row=0, column=1, padx=10, pady=5)
        
        # Error Count
        error_title = ttk.Label(stats_frame, text="Hata Sayısı:", style='Stats.TLabel')
        error_title.grid(row=0, column=2, padx=10, pady=5)
        self.error_label = ttk.Label(stats_frame, text="0", style='Stats.TLabel')
        self.error_label.grid(row=0, column=3, padx=10, pady=5)
        
        # Status
        status_title = ttk.Label(stats_frame, text="Durum:", style='Stats.TLabel')
        status_title.grid(row=1, column=0, padx=10, pady=5)
        self.status_label = ttk.Label(stats_frame, text="Bekleniyor", style='Stats.TLabel')
        self.status_label.grid(row=1, column=1, columnspan=3, padx=10, pady=5)
        
        # Runtime
        runtime_title = ttk.Label(stats_frame, text="Çalışma Süresi:", style='Stats.TLabel')
        runtime_title.grid(row=2, column=0, padx=10, pady=5)
        self.runtime_label = ttk.Label(stats_frame, text="00:00:00", style='Stats.TLabel')
        self.runtime_label.grid(row=2, column=1, columnspan=3, padx=10, pady=5)
        
        # Log Frame
        log_frame = ttk.LabelFrame(main_container, text="Log", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Log Area
        self.log_area = scrolledtext.ScrolledText(log_frame, width=70, height=15, font=('Courier', 10))
        self.log_area.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Control Frame
        control_frame = ttk.Frame(main_container, padding="10")
        control_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Buttons
        self.start_button = ttk.Button(control_frame, text="Başlat", command=self.start_bot, 
                                     style='Big.TButton', width=20)
        self.start_button.grid(row=0, column=0, padx=10)
        
        self.stop_button = ttk.Button(control_frame, text="Durdur", command=self.stop_bot,
                                    style='Big.TButton', width=20, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=10)
        
        self.clear_button = ttk.Button(control_frame, text="Log Temizle", command=self.clear_log,
                                     style='Big.TButton', width=20)
        self.clear_button.grid(row=0, column=2, padx=10)
        
        # Configure weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        main_container.rowconfigure(2, weight=1)
        
        # Start update timer
        self.update_runtime()
        
    def update_runtime(self):
        if self.start_time and self.is_running:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.runtime_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.root.after(1000, self.update_runtime)
        
    def clear_log(self):
        self.log_area.delete(1.0, tk.END)
        self.log_message("Log temizlendi")
        
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)
        
    def update_status(self, status):
        self.status_label.config(text=status)
        
    def update_count(self):
        self.vote_count += 1
        self.count_label.config(text=str(self.vote_count))
        
    def update_error_count(self):
        self.error_count += 1
        self.error_label.config(text=str(self.error_count))
        
    def start_bot(self):
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.update_status("Çalışıyor")
            self.current_thread = threading.Thread(target=self.bot_loop)
            self.current_thread.daemon = True
            self.current_thread.start()
            
    def stop_bot(self):
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Durduruluyor...")
        
    def get_chrome_options(self):
        chrome_options = Options()
        chrome_options.binary_location = self.chrome_path
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        return chrome_options
        
    def bot_loop(self):
        max_errors = 3
        consecutive_errors = 0
        
        while self.is_running:
            browser = None
            try:
                service = Service(executable_path=self.driver_path)
                browser = webdriver.Chrome(service=service, options=self.get_chrome_options())
                self.log_message("Tarayıcı başlatıldı")
                
                url = "https://distrokid.com/spotlight/hasanarthuraltunta/vote/"
                browser.get(url)
                self.log_message("Sayfa yüklendi")
                
                button = WebDriverWait(browser, 10).until(
                    EC.element_to_be_clickable((By.XPATH, 
                        '//*[@id="distroListContainer"]/div[3]/div[3]/div[1]/div[1]/div[2]/div[2]/a[1]'))
                )
                button.click()
                self.log_message("Oy verildi")
                self.update_count()
                consecutive_errors = 0
                
                time.sleep(3)
                
            except Exception as e:
                consecutive_errors += 1
                self.update_error_count()
                error_msg = f"Hata ({consecutive_errors}/{max_errors}): {str(e)}"
                self.log_message(error_msg)
                
                if consecutive_errors >= max_errors:
                    self.log_message("Çok fazla hata oluştu. Bot yeniden başlatılıyor...")
                    consecutive_errors = 0
                    time.sleep(5)
            finally:
                if browser:
                    browser.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = VoteBotGUI(root)
    root.mainloop()

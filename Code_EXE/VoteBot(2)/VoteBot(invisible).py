from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

class VoteBot:
    def __init__(self):
        # Tarayıcı ve ChromeDriver yolu
        self.chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.driver_path = r"C:\Users\MONSTER\Desktop\VoteBot\chromedriver.exe"

    # Chrome için görünmez mod ayarları
    def configure_chrome_options(self):
        options = Options()
        options.add_argument("--headless")  # Arka planda çalışır
        options.add_argument("--disable-gpu")  # GPU kullanımı devre dışı
        options.add_argument("--window-size=1920x1080")  # Standart ekran çözünürlüğü
        options.add_argument("--disable-extensions")  # Eklentileri devre dışı bırak
        options.add_argument("--no-sandbox")  # Güvenli alanı devre dışı bırak
        options.add_argument("--disable-dev-shm-usage")  # Paylaşımlı bellek kullanımını devre dışı bırak
        options.binary_location = self.chrome_path  # Chrome tarayıcı yolunu belirt
        return options

    # Selenium servisini başlat
    def create_browser(self):
        service = Service(self.driver_path)  # ChromeDriver'ın yüklendiği yol
        chrome_options = self.configure_chrome_options()
        return webdriver.Chrome(service=service, options=chrome_options)

    # URL ve XPath
    URL = "https://distrokid.com/spotlight/hasanarthuraltunta/vote/"
    NEXT_BUTTON_XPATH = '//*[@id="distroListContainer"]/div[3]/div[3]/div[1]/div[1]/div[2]/div[2]/a[1]'

    # Tarayıcı döngüsü
    def main(self):
        try:
            while True:
                # Tarayıcıyı başlat
                browser = self.create_browser()
                browser.get(self.URL)

                try:
                    # Butonun tıklanabilir olmasını bekle
                    button = WebDriverWait(browser, 10).until(
                        EC.element_to_be_clickable((By.XPATH, self.NEXT_BUTTON_XPATH))
                    )
                    button.click()  # Butona tıkla
                    print("Butona tıklama başarılı!")
                    time.sleep(3)  # Tıklama sonrası bekleme süresi

                except Exception as e:
                    print(f"Buton işlemi sırasında hata oluştu: {e}")
                finally:
                    # Tarayıcıyı kapat
                    browser.quit()
                    print("Tarayıcı kapatıldı.")
                
                # Bir sonraki döngüye geçmeden önce bekleme
                time.sleep(3)  # Döngü arasındaki bekleme süresi

        except Exception as e:
            print(f"Genel bir hata oluştu: {e}")

# Ana fonksiyonu çalıştır
if __name__ == "__main__":
    bot = VoteBot()
    bot.main()

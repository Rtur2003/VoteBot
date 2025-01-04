from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Döngüyü başlat
while True:
    # Tarayıcıyı başlat
    browser = webdriver.Chrome()

    # Tarayıcıyı küçült (alt sekmeye alma işlemi)
    browser.minimize_window()

    # Hedef URL'ye git
    url = "https://distrokid.com/spotlight/hasanarthuraltunta/vote/"
    browser.get(url)

    # Butonun XPath'ı
    NEXT_BUTTON_XPATH = '//*[@id="distroListContainer"]/div[3]/div[3]/div[1]/div[1]/div[2]/div[2]/a[1]'

    try:
        # Butonun görünür ve tıklanabilir olmasını bekle
        button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, NEXT_BUTTON_XPATH))
        )
        # Butona tıkla
        button.click()
        
        # Tıklama sonrası biraz bekle
        time.sleep(3)  # Bekleme süresini 3 saniye olarak ayarladım
    except Exception as e:
        print(f"Bir hata oluştu: {e}")

    # Tarayıcıyı kapat
    browser.quit()

    # Tarayıcı kapatıldıktan sonra döngü tekrar başa saracak
    time.sleep(3)  # Bir sonraki döngüye geçmeden önce 3 saniye bekle
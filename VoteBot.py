from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

while True:
   
    browser = webdriver.Chrome()

   
    browser.minimize_window()

   
    url = "https://distrokid.com/spotlight/hasanarthuraltunta/vote/"
    browser.get(url)

   
    NEXT_BUTTON_XPATH = '//*[@id="distroListContainer"]/div[3]/div[3]/div[1]/div[1]/div[2]/div[2]/a[1]'

    try:
        
        button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, NEXT_BUTTON_XPATH))
        )
        
        button.click()
        
        
        time.sleep(3)  
    except Exception as e:
        print(f"Bir hata oluştu: {e}")

    
    browser.quit()

   
    time.sleep(3) 

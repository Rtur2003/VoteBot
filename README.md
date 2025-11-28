# VoteBot 5

Profesyonel, GUI tabanlı DistroKid oy botu. Sürüm 5, yol/doğrulama kontrolleri, daha stabil Selenium akışı, modern arayüz ve ayrıntılı loglama ile yeniden yazıldı.

## Özellikler
- **Ön kontrol**: Chrome/ChromeDriver yolları ve sürüm uyumluluğu otomatik denetlenir.
- **Başlat/Durdur güvenliği**: İş parçacığı güvenli UI, temiz durdurma, durum göstergeleri.
- **Batch oy**: Ayarlanabilir batch sayısı ve oy aralığı; her oyda sürücü aç/kapat.
- **Paralel oy**: Aynı anda birden fazla pencere açarak batch süresini kısaltma (1-10 işçi).
- **Senkronsuz oy tıklaması**: Tüm pencereler açıldıktan sonra butonlar topluca tıklanır; yarım açılan pencereler diğerlerini engellemez.
- **Kapsamlı log**: UI log + `logs/votebot5.log` dosyası.
- **Temiz tema**: Koyu lacivert arka plan, amber/azure aksanlı kartlar.

## Gereksinimler
- Python 3.9+
- Google Chrome (kurulu)
- Chrome sürümünüzle uyumlu `chromedriver.exe`
- `pip install -r requirements.txt` (selenium, requests, discord.py)

## Kurulum
```bash
cd "C:\Users\MONSTER\Desktop\Yeni klasör\VoteBot"
pip install -r requirements.txt
```

### ChromeDriver
- Chrome sürümünüzü öğrenin: `chrome --version`
- Aynı major sürüme sahip ChromeDriver indirin (örn. Chrome 142 için `142.x` driver):  
  https://googlechromelabs.github.io/chrome-for-testing/
- İnen `chromedriver.exe`yi proje köküne koyun: `C:\Users\MONSTER\Desktop\Yeni klasör\VoteBot\chromedriver.exe`

## Yapılandırma
`config.json` (kök) veya `Code_EXE/VoteBot(5)/config.json`:
```json
{
  "paths": {
    "chrome": "C:\\\\Program Files\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe",
    "driver": "chromedriver.exe",
    "logs": "logs",
    "config": "config.json"
  },
  "target_url": "https://distrokid.com/spotlight/hasanarthuraltunta/vote/",
  "pause_between_votes": 3,
  "batch_size": 1,
  "max_errors": 3,
  "parallel_workers": 2,
  "headless": true,
  "timeout_seconds": 15
}
```
- `driver` ve `logs` göreli bırakılırsa kök klasöre göre çözümlenir.
- `parallel_workers`: Aynı anda açılacak pencere sayısı (1-10 arası).
- `headless` kapatırsanız tarayıcıyı görerek izleyebilirsiniz.

## Çalıştırma
```bash
python Code_EXE/VoteBot(5)/VoteBot5.py
```
1) **Ön kontrol**: Yollar ve sürümler uygunsa mesaj verir. Değilse sürümü/konumu düzeltin.  
2) **Başlat**: Bot çalışır, sayaçlar/log akar.  
3) **Durdur**: Temiz kapatma.  
4) Log klasörünü aç butonuyla `logs/votebot5.log`a hızlı erişim.

## Git
```bash
git remote add origin https://github.com/Rtur2003/VoteBot.git
git branch -M main
git pull --rebase origin main   # uzak geçmişi içe al
git push -u origin main
```

## Ekran Görüntüleri
`docs/screenshots/votebot5-ui.png` – ana arayüz (mevcut)

![VoteBot 5 UI](docs/screenshots/votebot5-ui.png)

Ek görseller için aynı klasöre dosya bırakabilirsiniz (ör. `votebot5-preflight.png`).

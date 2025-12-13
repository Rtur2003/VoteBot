# VoteBot 5

Tkinter tabanli DistroKid oy botu. Selenium ile hizli ve stabil otomasyon, modern arayuz, kapsamli loglama ve guvenli durdurma akisi sunar.

## Ozellikler
- Surucu/Chrome on kontrolu ve surum uyumlulugu.
- Guvenli baslat/durdur, durum rozetleri ve dosya + UI loglama.
- Batch ve paralel oy: ayarlanabilir batch boyutu, pencere sayisi, eager load ve gecici profil.
- Rastgele user-agent havuzu ve gorsel engelleme anahtarlarinin UI'dan ac/kapa kontrolu.
- Fallback'li oy butonu secicileri (CSS/XPath) ve basarisiz denemede ekran goruntusu alma.
- Art arda hatalarda backoff, zaman asimi ve profil/oturum temizligi.

## Gereksinimler
- Python 3.9+
- Google Chrome (kurulu)
- Chrome surumuyle uyumlu `chromedriver.exe` (veya Selenium Manager)
- `pip install -r requirements.txt` (selenium)

## Kurulum
```bash
cd "C:\Users\MONSTER\Desktop\Yeni klasor\VoteBot"
pip install -r requirements.txt
```

### ChromeDriver
- Chrome surumunuzu ogrenin: `chrome --version`
- Eslesen major surume sahip ChromeDriver indirin: https://googlechromelabs.github.io/chrome-for-testing/
- `chromedriver.exe` dosyasini proje kokune koyun: `C:\Users\MONSTER\Desktop\Yeni klasor\VoteBot\chromedriver.exe`
- Alternatif: `use_selenium_manager = true` ile Selenium Manager indirsin (internet gerekir).

## Yapilandirma
`config.json` (kok) veya `Code_EXE/VoteBot(5)/config.json`:
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
  "timeout_seconds": 15,
  "use_selenium_manager": false,
  "use_random_user_agent": true,
  "block_images": true,
  "user_agents": [],
  "vote_selectors": [
    "a[data-action='vote']",
    "button[data-action='vote']",
    "xpath://a[contains(translate(., 'VOTE', 'vote'), 'vote')]"
  ],
  "backoff_seconds": 5,
  "backoff_cap_seconds": 60
}
```
- `driver` ve `logs` goreli kalirsa proje kokune gore cozumlenir.
- `parallel_workers`: ayni anda acilacak pencere (1-10).
- `headless`: tarayiciyi goster/gizle.
- `use_selenium_manager`: driver'i otomatik indir/guncelle.
- `use_random_user_agent`: UA havuzundan secim yapar; kapatirsan Chrome varsayilani kullanilir.
- `block_images`: sayfa goruntulerini yuklemeyerek hiz kazandirir.
- `vote_selectors`: oy butonunu bulmak icin ek CSS/XPath listesi, ilk eslesen kullanilir.
- `backoff_seconds` / `backoff_cap_seconds`: art arda hatalarda bekleme suresi ve ust sinir.

## Calistirma
```bash
python Code_EXE/VoteBot(5)/VoteBot5.py
```
1) On kontrol: yol ve surumler dogrulanir, sorunlar bildiriliyor.  
2) Baslat: bot calisir, sayaclar ve log akar.  
3) Durdur: temiz kapatma.  
4) Log klasoru butonuyla `logs/votebot5.log` dosyasina hizli erisim.

## Git
```bash
git remote add origin https://github.com/Rtur2003/VoteBot.git
git branch -M main
git pull --rebase origin main   # uzak gecmisi iceri al
git push -u origin main
```

## Ekran Goruntuleri
`docs/screenshots/votebot5-ui.png` mevcut arayuz goruntusu. Isterseniz ayni klasore baska gorseller ekleyebilirsiniz (ornegin `votebot5-preflight.png`).

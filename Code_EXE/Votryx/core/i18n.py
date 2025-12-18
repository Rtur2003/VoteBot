"""Internationalization module for VOTRYX UI strings."""


class UIStrings:
    """Turkish UI strings separated from application logic."""

    # Application title and branding
    APP_TITLE = "VOTRYX - DistroKid Spotlight"
    APP_SUBTITLE = "Stabil, hızlı, şeffaf otomatik oy"
    APP_TAGLINE = (
        "Başlat ve unut: otomatik sürücü kontrolü, batch oy ve güvenli loglama"
    )

    # Status labels
    STATUS_WAITING = "Bekliyor"
    STATUS_RUNNING = "Çalışıyor"
    STATUS_STOPPED = "Durduruldu"
    STATUS_VOTING = "Oy veriliyor"

    # Pill labels
    PILL_HEADLESS_READY = "Headless hazır"
    PILL_BATCH_VOTING = "Batch oy"
    PILL_LOG_RECORDING = "Log kaydı"

    # Dashboard section
    SECTION_DASHBOARD = "Gösterge Paneli"
    STAT_TOTAL_VOTES = "Toplam Oy"
    STAT_ERRORS = "Hata"
    STAT_STATUS = "Durum"
    STAT_RUNTIME = "Süre"

    # Settings section
    SECTION_SETTINGS = "Ayarlar"
    TAB_GENERAL = "Genel"
    TAB_ADVANCED = "Gelişmiş"

    # General settings
    FIELD_TARGET_URL = "Hedef URL"
    HELPER_TARGET_URL = "Oylama sayfasının bağlantısı"
    FIELD_VOTE_INTERVAL = "Oy aralığı (sn)"
    HELPER_VOTE_INTERVAL = "Her oy arasında bekleme süresi"
    FIELD_BATCH_SIZE = "Batch (kaç oy)"
    HELPER_BATCH_SIZE = "Tek seferde verilecek oy sayısı"
    FIELD_TIMEOUT = "Zaman aşımı (sn)"
    HELPER_TIMEOUT = "Oy butonu için bekleme sınırı"
    FIELD_MAX_ERRORS = "Maks hata"
    HELPER_MAX_ERRORS = "Bu sayıya ulaşınca bekleme ve yeniden deneme"
    FIELD_BACKOFF = "Backoff (sn)"
    HELPER_BACKOFF = "Hata sonrası ilk bekleme"
    FIELD_BACKOFF_CAP = "Backoff üst sınır"
    HELPER_BACKOFF_CAP = "Maksimum bekleme sınırı"
    FIELD_PARALLEL_WINDOWS = "Paralel pencere"
    HELPER_PARALLEL_WINDOWS = "Aynı anda açılacak tarayıcı sayısı"

    # Toggle options
    TOGGLE_HEADLESS = "Görünmez (headless) çalıştır"
    TOGGLE_SELENIUM_MANAGER = "ChromeDriver'ı Selenium Manager yönetsin"
    HELPER_HEADLESS_SELENIUM = (
        "Headless kapalıysa tarayıcıyı izleyebilirsiniz; "
        "Selenium Manager uyumsuz sürücüleri indirir."
    )

    # Advanced settings
    TOGGLE_RANDOM_UA = "Rastgele user-agent kullan"
    HELPER_RANDOM_UA = (
        "Açıkken liste veya varsayılan havuzdan UA seçilir; "
        "kapalıysa Chrome varsayılanı kullanılır."
    )
    TOGGLE_BLOCK_IMAGES = "Görselleri engelle (daha hızlı yükleme)"
    HELPER_BLOCK_IMAGES = (
        "Açıkken sayfa görselleri yüklenmez; "
        "kapalıysa varsayılan yükleme kullanılır."
    )
    FIELD_USER_AGENTS = "User-Agent listesi (satır satır)"
    HELPER_USER_AGENTS = "Boş bırakılırsa varsayılan UA havuzu kullanılır."
    FIELD_VOTE_SELECTORS = "Oy buton seçicileri (satır satır CSS/XPath)"
    HELPER_VOTE_SELECTORS = (
        "Örnekler: a[data-action='vote'], button[data-action='vote'], "
        "xpath://button[contains(.,'vote')]"
    )

    # Action buttons
    BTN_APPLY_SETTINGS = "Ayarları Uygula"
    BTN_LOAD_DEFAULTS = "Varsayılanları Yükle"
    BTN_START = "Başlat"
    BTN_STOP = "Durdur"
    BTN_PREFLIGHT = "Ön kontrol"
    BTN_OPEN_LOGS = "Log klasörünü aç"
    BTN_RESET_COUNTERS = "Sayaclari sifirla"
    BTN_RUNNING = "Çalışıyor..."

    # Log section
    SECTION_LOG = "Log"
    BADGE_SUCCESS = "Başarılı: {count}"
    BADGE_ERROR = "Hata: {count}"
    TOGGLE_AUTOSCROLL = "Otomatik kaydır"
    TOGGLE_ERRORS_ONLY = "Sadece hatalar"
    BTN_CLEAR_LOG = "Log temizle"

    # Welcome screen
    WELCOME_TITLE = "VOTRYX - DistroKid Spotlight"
    WELCOME_SUBTITLE = "Stabil, hızlı, şeffaf otomatik oy"
    WELCOME_BULLET_1 = "Chromedriver/Chrome ön kontrol, batch/parallel oy"
    WELCOME_BULLET_2 = (
        "Loglama, ekran görüntüsü, backoff ve zaman aşımı korumaları"
    )
    WELCOME_BULLET_3 = "Sekmeli ayarlar, gelişmiş UA ve selector yönetimi"
    BTN_ENTER_CONTROL_PANEL = "Kontrol Paneline Gir"

    # Messages
    MSG_BOT_STARTED = "Bot başlatıldı"
    MSG_BOT_STOPPING = "Bot durduruluyor..."
    MSG_LOG_CLEARED = "Log temizlendi"
    MSG_COUNTERS_RESET = "Sayaçlar sifirlandi."
    MSG_SETTINGS_SAVED = "Ayarlar kaydedildi."
    MSG_SETTINGS_APPLIED = "Ayarlar güncellendi."
    MSG_DEFAULTS_LOADED = "Varsayılan ayarlar yüklendi."
    MSG_PREFLIGHT_SUCCESS = "Ön kontrol başarılı"
    MSG_VOTE_SUCCESS = "Oy verildi (pencere {idx}/{total})"
    MSG_VOTE_SUCCESS_RETRY = "Oy verildi (yeniden deneme, pencere {idx}/{total})"
    MSG_BATCH_COMPLETE = "Batch tamamlandı. Başarılı: {success}, Hata: {failure}"
    MSG_BATCH_PARTIAL = (
        "Batch kısmen tamamlandı. Başarılı: {success}, Hata: {failure}"
    )
    MSG_BATCH_FAILED = "Batch tamamlanamadı. Başarılı: {success}, Hata: {failure}"
    MSG_CONSECUTIVE_ERRORS = (
        "Art arda {count} hata alındı, {wait} sn bekleniyor ve yeniden denenecek."
    )

    # Error messages
    ERR_CANNOT_RESET_WHILE_RUNNING = "Bot çalişirken sayaçlar sifirlanamaz."
    ERR_VOTE_BUTTON_TIMEOUT = "Oy butonu zaman aşımına uğradı."
    ERR_VOTE_BUTTON_TIMEOUT_PREP = "Oy butonu zaman aşımına uğradı (hazırlık)."
    ERR_VOTE_BUTTON_NOT_FOUND = "Oy butonu bulunamadı, ekran görüntüsü: {path}"
    ERR_VOTE_BUTTON_NO_SCREENSHOT = (
        "Oy butonu bulunamadı, ekran görüntüsü alınamadı."
    )
    ERR_UNEXPECTED = "Beklenmeyen hata: {error}"
    ERR_UNEXPECTED_PREP = "Beklenmeyen hata (hazırlık): {error}"
    ERR_INVALID_NUMBER_FIELDS = "Sayısal alanlar geçerli ve pozitif olmalı."
    ERR_INVALID_VOTE_INTERVAL = "Oy aralığı 0'dan büyük olmalı."
    ERR_INVALID_BACKOFF = "Backoff süreleri 0'dan büyük olmalı."
    ERR_INVALID_BACKOFF_CAP = (
        "Backoff üst sınırı başlangıç değerinden küçük olamaz."
    )
    ERR_INVALID_URL = "Geçerli bir hedef URL girin (http/https ile)."
    ERR_SETTINGS_NOT_READ = "Ayarlar okunamadı: sayısal alan hatalı."
    ERR_SETTINGS_NOT_SAVED = "Ayarlar kaydedilemedi: {error}"
    ERR_CONFIG_SAVE_FAILED = "Ayarlar kaydedilemedi: {error}"

    # Info messages
    INFO_CHROME_NOT_FOUND = (
        "Chrome yolu bulunamadı; Selenium Manager Chrome for Testing deneyecek."
    )
    INFO_SELENIUM_MANAGER = (
        "ChromeDriver Selenium Manager tarafından otomatik yönetilecek."
    )
    INFO_DRIVER_PATH = "Sürücü: {path}"
    INFO_CHROME_PATH = "Chrome: {path}"
    INFO_MULTIPLE_CONFIGS = (
        "Birden fazla config bulundu. Kullanılan: {used}, yok sayılan: {ignored}"
    )

    # Dialog titles
    DIALOG_ERROR = "Hata"
    DIALOG_SETTINGS = "Ayarlar"
    DIALOG_PREFLIGHT = "Ön kontrol"
    DIALOG_LOG_FOLDER = "Log klasörü"
    DIALOG_PATH_ERROR = "Yol Hatası"
    DIALOG_VERSION_MISMATCH = "Sürüm Uyumsuzluğu"

    # Dialog messages
    DIALOG_PATHS_VALID = "Yollar ve ayarlar geçerli görünüyor."
    DIALOG_VERSION_MISMATCH_MSG = (
        "ChromeDriver ve Chrome sürümleri farklı. Lütfen sürümü eşleştirin."
    )

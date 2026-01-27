# OIS Grade Checker 🎓

İstanbul Atlas Üniversitesi OIS sisteminden notlarını otomatik kontrol eden ve değişiklik olduğunda Telegram'dan bildirim gönderen bot.

## Özellikler

- 🔐 OIS'e otomatik giriş (CAPTCHA çözümü dahil)
- 📊 Not değişikliği takibi
- 📱 Telegram bot komutları
- ⏰ 5 dakikada bir otomatik kontrol

## Kurulum

### 1. Gereksinimler

**Tesseract OCR kurulumu:**

- **Windows:** [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) adresinden indir
- **Linux:** `sudo apt install tesseract-ocr`
- **macOS:** `brew install tesseract`

### 2. Python Bağımlılıkları

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

`.env.example` dosyasını `.env` olarak kopyala ve değerleri doldur:

```bash
cp .env.example .env
```

```env
OIS_USERNAME=240501021  # Öğrenci Numarası
OIS_PASSWORD=your_password
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=123456789
CHECK_INTERVAL=300  # saniye (5 dakika)
```

**Telegram bilgilerini bulmak:**

1. [@BotFather](https://t.me/BotFather)'a git → `/mybots` → Bot Token'ı al
2. Botuna bir mesaj at
3. `https://api.telegram.org/bot<TOKEN>/getUpdates` adresini aç → Chat ID'yi bul

### 4. Çalıştır

```bash
python main.py
```

## Telegram Komutları

| Komut | Açıklama |
|-------|----------|
| `/start` | Monitoring'i başlat |
| `/stop` | Monitoring'i durdur |
| `/status` | Mevcut durum bilgisi |
| `/check` | Anlık not kontrolü |

## Deploy

Proje Docker ile deploy edilmeye hazır. `Dockerfile` Tesseract ve Playwright'ı otomatik kurar.

### Railway.app (Önerilen)

1. GitHub'a push et
2. [Railway.app](https://railway.app)'e git
3. "New Project" → "Deploy from GitHub repo"
4. Environment variables ekle:
   - `OIS_USERNAME`
   - `OIS_PASSWORD`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
5. Deploy!

### Render.com

1. GitHub'a push et
2. [Render.com](https://render.com)'a git
3. "New Web Service" → Docker seç
4. Environment variables ekle
5. Deploy!

> ⚠️ Render ücretsiz tier'da 15 dk sonra uyuyor. [UptimeRobot](https://uptimerobot.com) ile ping at.

### Docker (Manuel)

```bash
docker build -t ois-checker .
docker run -d --env-file .env ois-checker
```

## Lisans

MIT

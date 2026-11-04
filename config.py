import os
from dotenv import load_dotenv

# .env faylini o'qish (agar mavjud bo'lsa)
load_dotenv()

# Bot Token (BotFather'dan olingan)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Asosiy Admin ID (Sizning ID raqamingiz)
ADMIN_ID = int(os.getenv("ADMIN_ID", 8913846037))

# PostgreSQL Database URL
# Misol: postgresql://user:password@localhost:5432/music_hub_db
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/music_hub")

# Admin Panel 2-Bosqichli Tasdiqlash PIN kodi
ADMIN_PIN = "1202"

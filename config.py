import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 8913846037))

# Agar DATABASE_URL topilmasa, avtomatik xato beradi va lokalga yugurmaydi
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DIQQAT: DATABASE_URL topilmadi! Fly.io Secrets ga DATABASE_URL ni kiriting.")

ADMIN_PIN = "1202"

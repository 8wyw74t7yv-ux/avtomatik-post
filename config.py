import os
from dotenv import load_dotenv

# .env faylini o'qish uchun load_dotenv ishlatiladi
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("XATOLIK: .env faylida BOT_TOKEN topilmadi!")

import os
from dotenv import load

# .env faylini o'qish
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("XATOLIK: .env faylida BOT_TOKEN topilmadi!")

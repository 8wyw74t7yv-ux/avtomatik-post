import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import db

# Barcha handler modullarini import qilish
from handlers.start import start_router
from handlers.music import music_router
from handlers.effects import effects_router
from handlers.vault import vault_router
from handlers.business import business_router
from handlers.admin import admin_router

# Loggingni sozlash
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

async def main():
    # Bot obyektini yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()

    # 1. PostgreSQL bazasiga ulanish
    await db.connect()

    try:
        logger.info("Bot ishga tushmoqda...")
        # Eski update'larni o'tkazib yuborish
        await bot.delete_webhook(drop_pending_updates=True)
        
        # 2. Barcha handler router'larni Dispatcher'ga ulash (Tartib muhim!)
        dp.include_router(start_router)
        dp.include_router(music_router)
        dp.include_router(effects_router)
        dp.include_router(vault_router)
        dp.include_router(business_router)
        dp.include_router(admin_router)

        # Polling boshlash
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()
        logger.info("Bot to'xtatildi va baza ulanishi yopildi.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot qo'lda to'xtatildi.")

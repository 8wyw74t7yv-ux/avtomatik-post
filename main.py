import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import db

# Loggingni sozlash
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

async def main():
    # Bot obyektini yaratish (ParseMode HTML qilib belgilanadi)
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()

    # 1. PostgreSQL bazasiga ulanish
    await db.connect()

    try:
        logger.info("Bot ishga tushmoqda...")
        # Eski update'larni o'tkazib yuborish va Polling boshlash
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Bu yerda kelgusida boshqa handler router'lar ulanadi
        # dp.include_router(start_router)
        # dp.include_router(admin_router)
        # dp.include_router(music_router)

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

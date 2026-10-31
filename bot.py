import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from audio_processor import AudioProcessor

# Tokeningizni shu yerga yozing
TOKEN = "YOUR_BOT_TOKEN_HERE"

bot = Bot(token=TOKEN)
dp = Dispatcher()

os.makedirs("downloads", exist_ok=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🎧 **Professional Audio Botga xush kelibsiz!**\n\n"
        "Menga istalgan musiqa (audio fayl) yuboring, uni serverda tahrirlab beraman!"
    )

@dp.message(F.audio | F.document)
async def handle_audio(message: types.Message):
    file = message.audio or message.document
    file_id = file.file_id
    file_info = await bot.get_file(file_id)
    
    input_path = f"downloads/{file_id}.mp3"
    output_path = f"downloads/out_{file_id}.mp3"
    
    # Faylni yuklab olish
    await bot.download(file_info, destination=input_path)
    
    await message.answer("⚙️ Audio qayta ishlanmoqda (Hozircha test uchun Reverse qilindi)...")
    
    # Processor orqali ishlov berish (Masalan: Orqaga aylantirish)
    processor = AudioProcessor(input_path)
    processor.reverse_audio(output_path)
    
    # Tayyor faylni yuborish
    await message.answer_audio(
        types.FSInputFile(output_path), 
        caption="✅ Tayyor! Serverda qayta ishlandi."
    )
    
    # Serverni tozalash (Fayllarni o'chirish)
    if os.path.exists(input_path): os.remove(input_path)
    if os.path.exists(output_path): os.remove(output_path)

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN
from audio_engine import ProAudioEngine

# Loggingni sozlash
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

os.makedirs("downloads", exist_ok=True)
os.makedirs("processed", exist_ok=True)

# FSM holatlari (Foydalanuvchi qaysi audioni tahrirlayotganini saqlash uchun)
class AudioStates(StatesGroup):
    waiting_for_effect = State()

def get_effects_keyboard():
    """Professional Inline menyu"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔥 Bass Boost (+15dB)", callback_data="eff_bass")
    builder.button(text="⚡ Tezlikni Oshirish (1.25x)", callback_data="eff_speed")
    builder.button(text="📻 Radio / Telefon Effekti", callback_data="eff_radio")
    builder.button(text="🔄 Orqaga Aylantirish (Reverse)", callback_data="eff_reverse")
    builder.button(text="🏛 Reverb (Eko / Xona)", callback_data="eff_reverb")
    builder.adjust(1) # Har bir qatorga bittadan tugma
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🎧 **Professional Audio DJ Botga xush kelibsiz!**\n\n"
        "Menga istalgan musiqa yoki audio fayl yuboring, uni professional darajada tahrirlab beraman!"
    )

@dp.message(F.audio | F.document)
async def handle_audio_file(message: types.Message, state: FSMContext):
    file = message.audio or message.document
    
    # Fayl formatini tekshirish
    if not file.file_name or not file.file_name.lower().endswith(('.mp3', '.wav', '.m4a', '.ogg', '.flac')):
        await message.answer("❌ Iltimos, to'g'ri formatdagi audio fayl (MP3, WAV, FLAC) yuboring!")
        return

    msg = await message.answer("📥 Audio serverga yuklab olinmoqda...")
    
    file_info = await bot.get_file(file.file_id)
    input_path = f"downloads/{message.from_user.id}_{file.file_id}.mp3"
    output_path = f"processed/{message.from_user.id}_{file.file_id}.mp3"
    
    await bot.download(file_info, destination=input_path)
    
    # Holatga fayl yo'llarini saqlab qo'yamiz
    await state.update_data(input_path=input_path, output_path=output_path)
    await state.set_state(AudioStates.waiting_for_effect)
    
    await msg.edit_text(
        "🎛 **Audio muvaffaqiyatli qabul qilindi!**\n\nQuyidagi professional effektlardan birini tanlang:",
        reply_markup=get_effects_keyboard()
    )

@dp.callback_query(AudioStates.waiting_for_effect, F.data.startswith("eff_"))
async def process_audio_effect(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    input_path = data.get("input_path")
    output_path = data.get("output_path")
    
    effect_type = callback.data.split("_")[1]
    
    await callback.message.edit_text("⚙️ Serverda professional darajada qayta ishlanmoqda...")
    
    try:
        if effect_type == "bass":
            ProAudioEngine.apply_bass_boost(input_path, output_path, gain_db=18)
        elif effect_type == "speed":
            ProAudioEngine.change_speed_and_pitch(input_path, output_path, tempo=1.25)
        elif effect_type == "radio":
            ProAudioEngine.apply_radio_filter(input_path, output_path)
        elif effect_type == "reverse":
            ProAudioEngine.reverse_audio(input_path, output_path)
        elif effect_type == "reverb":
            ProAudioEngine.apply_reverb(input_path, output_path)
        
        # Tayyor faylni yuborish
        await callback.message.answer_audio(
            types.FSInputFile(output_path),
            caption="✅ **Tayyor!** Professional audio serverda muvaffaqiyatli ishlandi."
        )
        await callback.message.delete()
        
    except Exception as e:
        await callback.message.answer(f"❌ Xatolik yuz berdi: {str_ := str(e)}")
    
    finally:
        # Vaqtincha kirish faylini tozalash (Chiqish faylini foydalanuvchi olgach o'chirish uchun alohida ham qilish mumkin)
        if os.path.exists(input_path): 
            os.remove(input_path)
        if os.path.exists(output_path): 
            os.remove(output_path)
        await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

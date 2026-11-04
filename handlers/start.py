from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, CommandObject
from database import db
from config import ADMIN_ID

start_router = Router()

@start_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    user = message.from_user
    
    # Foydalanuvchini bazaga qo'shish / yangilash
    await db.add_user(user.id, user.username, user.full_name)
    
    # 1. Bot qanday ishlashini ko'rsatuvchi tushuntirish va misol
    welcome_text = (
        f"Salom, <b>{user.first_name}</b>! 🎵\n\n"
        "Men sizning shaxsiy <b>Music Hub & Auto-Pilot</b> botingizman.\n"
        "Serverimizda hech qanday ortiqcha xotira band qilinmaydi — barcha musiqalar Telegram bulutida xavfsiz saqlanadi (`file_id`).\n\n"
        "💡 <b>Bot qanday ishlaydi? (Misol):</b>\n"
        "1. Menga istalgan <b>audio yoki qo'shiq</b> yuboring.\n"
        "2. Bot uni qabul qiladi va quyidagi menyu orqali unga **50+ dan ortiq professional effektlar** qo'shishingiz, uni kesishingiz yoki vizual videoga aylantirishingiz mumkin!\n\n"
        "Marhamat, hozircha bitta musiqa yuborib ko'ring! 👇"
    )

    # Asosiy klaviatura
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎧 Mening Pleylistim", callback_data="my_playlist"),
         InlineKeyboardButton(text="🌐 Telegram Business Ulash", callback_data="business_setup")],
        [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="settings"),
         InlineKeyboardButton(text="💡 Yordam & Qo'llanma", callback_data="help")]
    ])

    # Agar admin bo'lsa, Admin Panel tugmasini qo'shamiz
    if user.id == ADMIN_ID:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🔐 Admin Panel", callback_data="admin_panel_auth")
        ])

    await message.answer(welcome_text, reply_markup=keyboard)

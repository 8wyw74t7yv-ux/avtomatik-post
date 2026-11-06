import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, CommandObject
from aiogram.exceptions import TelegramBadRequest
from database import db
from config import ADMIN_ID

logger = logging.getLogger(__name__)
start_router = Router()

async def check_forced_subscription(bot, user_id):
    """Majburiy obuna kanallarini tekshirish funksiyasi"""
    try:
        async with db.pool.acquire() as conn:
            channels = await conn.fetch("SELECT * FROM forced_channels;")
        
        if not channels:
            return True, []

        not_subscribed = []
        for ch in channels:
            try:
                # Kanalga a'zolikni tekshirish
                member = await bot.get_chat_member(chat_id=ch['channel_username'], user_id=user_id)
                if member.status in ['left', 'kicked']:
                    not_subscribed.append(ch)
            except Exception:
                # Agar kanal topilmasa yoki xatolik bo'lsa o'tkazib yuborish
                continue
                
        return len(not_subscribed) == 0, not_subscribed
    except Exception:
        return True, []


@start_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    user = message.from_user
    
    # Foydalanuvchini bazaga qo'shish / yangilash
    await db.add_user(user.id, user.username, user.full_name)

    # Majburiy obunani tekshirish
    is_subbed, missing_channels = await check_forced_subscription(message.bot, user.id)
    
    if not is_subbed:
        kb_channels = []
        for ch in missing_channels:
            kb_channels.append([InlineKeyboardButton(text=f"📢 {ch.get('channel_title', 'Homiy Kanal')}", url=f"https://t.me/{ch['channel_username'].lstrip('@')}")])
        
        kb_channels.append([InlineKeyboardButton(text="🔄 Tekshirish", callback_data="check_subscription")])
        
        await message.answer(
            "⚠️ <b>Botdan foydalanish uchun quyidagi homiy kanallarga a'zo bo'lishingiz shart:</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_channels)
        )
        return
    
    # 1. Bot qanday ishlashini ko'rsatuvchi tushuntirish va misol
    welcome_text = (
        f"Salom, <b>{user.first_name}</b>! 🎵\n\n"
        "Men sizning shaxsiy <b>Music Hub & Auto-Pilot</b> botingizman.\n"
        "Serverimizda hech qanday ortiqcha xotira band qilinmaydi — barcha musiqalar Telegram bulutida xavfsiz saqlanadi (`file_id`).\n\n"
        "💡 <b>Bot qanday ishlaydi? (Misol):</b>\n"
        "1. Menga istalgan <b>audio yoki qo'shiq</b> yuboring.\n"
        "2. Bot uni qabul qiladi va quyidagi menyu orqali unga **51 ta professional effektlar** qo'shishingiz yoki uni kesishingiz mumkin!\n\n"
        "Marhamat, menyudan kerakli bo'limni tanlang yoki musiqa yuboring! 👇"
    )

    # Asosiy klaviatura
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎧 Mening Pleylistim", callback_data="my_playlist"),
            InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="settings")
        ],
        [
            InlineKeyboardButton(text="💡 Yordam & Qo'llanma", callback_data="help"),
            InlineKeyboardButton(text="👨‍💻 Bot Yaratuvchisi", url="https://t.me/mrxruslann?text=Salom")
        ]
    ])

    # Agar admin bo'lsa, Admin Panel tugmasini qo'shamiz (Faqat ADMIN_ID: 8913846037)
    if user.id == ADMIN_ID:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🔐 Admin Panel", callback_data="admin_panel_auth")
        ])

    await message.answer(welcome_text, reply_markup=keyboard)


@start_router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    user = callback.from_user
    welcome_text = (
        f"<b>Music Hub Bosh Menyusi</b>\n\n"
        "Kerakli bo'limni tanlang:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎧 Mening Pleylistim", callback_data="my_playlist"),
            InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="settings")
        ],
        [
            InlineKeyboardButton(text="💡 Yordam & Qo'llanma", callback_data="help"),
            InlineKeyboardButton(text="👨‍💻 Bot Yaratuvchisi", url="https://t.me/mrxruslann?text=Salom")
        ]
    ])

    if user.id == ADMIN_ID:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🔐 Admin Panel", callback_data="admin_panel_auth")
        ])

    try:
        await callback.message.edit_text(welcome_text, reply_markup=keyboard)
    except TelegramBadRequest:
        pass
    await callback.answer()


@start_router.callback_query(F.data == "check_subscription")
async def verify_sub_callback(callback: CallbackQuery):
    is_subbed, _ = await check_forced_subscription(callback.bot, callback.from_user.id)
    if is_subbed:
        await callback.message.delete()
        # Start xabarini qaytadan chaqiramiz
        await cmd_start(callback.message, None)
    else:
        await callback.answer("❌ Siz hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True)

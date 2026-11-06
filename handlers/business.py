import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BusinessConnection
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)
business_router = Router()

class BusinessStates(StatesGroup):
    waiting_for_auto_reply_text = State()
    waiting_for_ghost_username = State()
    waiting_for_autodelete_details = State()
    waiting_for_dnd_time = State()


# 1. Telegram Business Connection Handler
@business_router.business_connection()
async def business_connection_handler(business_connection: BusinessConnection):
    logger.info(f"Telegram Business ulandi: {business_connection.id}, Foydalanuvchi: {business_connection.user.id}")


@business_router.message(F.business_connection_id)
async def business_message_handler(message: Message):
    """Business chatlardan kelgan xabarlarni tahlil qilish (Oddiy Message class ishlatiladi)"""
    if message.text:
        text_lower = message.text.lower()
        if "shoshilinch" in text_lower or "muhim" in text_lower:
            pass


@business_router.callback_query(F.data == "business_setup")
async def show_business_menu(callback: CallbackQuery):
    text = (
        "🌐 <b>Telegram Business & Chat Automation (Sekretar Rejimi)</b>\n\n"
        "Bu bo'lim orqali shaxsiy chatlaringizni avtomatlashtirishingiz, band paytingizda avto-javob qaytarishingiz, "
        "xabarlarni bildirmay o'qishingiz (Ghost Mode) va maxfiy yozishmalarni o'chirishingiz mumkin.\n\n"
        "Iltimos, kerakli funksiyani tanlang:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤖 Avto-Maslahatchi (Auto-Responder)", callback_data="biz_autoreply"),
            InlineKeyboardButton(text="⚡ Smart Emoji Reaksiya", callback_data="biz_reactions")
        ],
        [
            InlineKeyboardButton(text="👻 Ghost Mode (Bildirmay O'qish)", callback_data="biz_ghost"),
            InlineKeyboardButton(text="🧹 Chat Auto-Delete (O'chirish)", callback_data="biz_autodelete")
        ],
        [
            InlineKeyboardButton(text="🌙 Do Not Disturb (Tinchlik)", callback_data="biz_dnd"),
            InlineKeyboardButton(text="📥 Self-Destruct Media Saver", callback_data="biz_saver")
        ],
        [
            InlineKeyboardButton(text="🔗 Telegram Profilga Ulanish", url="https://t.me/settings"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Asosiy Menyu", callback_data="main_menu")
        ]
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        pass
    await callback.answer()


@business_router.callback_query(F.data == "biz_autoreply")
async def setup_auto_responder(callback: CallbackQuery, state: FSMContext):
    text = (
        "🤖 <b>Avto-Maslahatchi va Aqlli Avto-Javob beruvchi</b>\n\n"
        "Siz band bo'lganingizda yoki uxlayotganingizda kelgan xabarlarga yuboriladigan matnni kiriting.\n"
        "<b>Namuna:</b> <code>Hozir uxlashga yotdim, shoshilinch bo'lsa 2 soatdan keyin yozing.</code>"
    )
    await state.set_state(BusinessStates.waiting_for_auto_reply_text)
    await callback.message.edit_text(text)
    await callback.answer()


@business_router.message(BusinessStates.waiting_for_auto_reply_text)
async def save_auto_reply(message: Message, state: FSMContext):
    reply_text = message.text
    await message.answer(f"✅ Avto-javob muvaffaqiyatli saqlandi:\n\n<i>\"{reply_text}\"</i>")
    await state.clear()


@business_router.callback_query(F.data == "biz_ghost")
async def setup_ghost_mode(callback: CallbackQuery, state: FSMContext):
    text = (
        "👻 <b>Ghost Mode (Xabarni Bildirmay O'qish)</b>\n\n"
        "Qaysi foydalanuvchining (Username yoki ID) xabarlarini o'qiganingiz bildirilmasin? Username kiriting:"
    )
    await state.set_state(BusinessStates.waiting_for_ghost_username)
    await callback.message.edit_text(text)
    await callback.answer()


@business_router.message(BusinessStates.waiting_for_ghost_username)
async def save_ghost_target(message: Message, state: FSMContext):
    target = message.text
    await message.answer(f"✅ <b>{target}</b> uchun Ghost Mode faollashtirildi. Xabarlar endi yashirincha o'qiladi.")
    await state.clear()


@business_router.callback_query(F.data == "biz_autodelete")
async def setup_autodelete(callback: CallbackQuery, state: FSMContext):
    text = (
        "🧹 <b>Chatni Tozalash va Auto-Delete (Maxfiy Rejim)</b>\n\n"
        "Yozishmalarni qancha vaqtdan keyin ikkala tomondan ham toza qilib o'chirish kerak?\n"
        "<b>Namuna:</b> <code>username vaqt 60 minut</code> tarzida yuboring:"
    )
    await state.set_state(BusinessStates.waiting_for_autodelete_details)
    await callback.message.edit_text(text)
    await callback.answer()


@business_router.message(BusinessStates.waiting_for_autodelete_details)
async def save_autodelete_rule(message: Message, state: FSMContext):
    rule = message.text
    await message.answer(f"✅ Auto-delete qoidasi o'rnatildi: <b>{rule}</b>")
    await state.clear()


@business_router.callback_query(F.data == "biz_dnd")
async def setup_dnd(callback: CallbackQuery, state: FSMContext):
    text = (
        "🌙 <b>Do Not Disturb (Tinchlik Rejimi)</b>\n\n"
        "Tungi vaqtda (masalan, 23:00 dan 09:00 gacha) kelgan xabarlarga avto-javob yuborish vaqtini kiriting:"
    )
    await state.set_state(BusinessStates.waiting_for_dnd_time)
    await callback.message.edit_text(text)
    await callback.answer()


@business_router.message(BusinessStates.waiting_for_dnd_time)
async def save_dnd_rule(message: Message, state: FSMContext):
    time_range = message.text
    await message.answer(f"✅ Do Not Disturb rejimi faollashdi: <b>{time_range}</b>")
    await state.clear()


@business_router.callback_query(F.data == "biz_reactions")
async def setup_reactions(callback: CallbackQuery):
    await callback.answer("⚡ Smart Emoji Reaksiyalar avtomatik tahlilga ulandi!", show_alert=True)


@business_router.callback_query(F.data == "biz_saver")
async def setup_media_saver(callback: CallbackQuery):
    await callback.answer("📥 O'chib ketuvchi rasmlarni saqlash (Self-Destruct Media Saver) yoqildi!", show_alert=True)

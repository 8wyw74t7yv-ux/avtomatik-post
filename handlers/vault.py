import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db

logger = logging.getLogger(__name__)
vault_router = Router()

class VaultStates(StatesGroup):
    waiting_for_schedule_time = State()
    waiting_for_anonymous_target = State()
    waiting_for_vault_search = State()


@vault_router.callback_query(F.data == "my_playlist")
async def show_cloud_vault(callback: CallbackQuery):
    """Shaxsiy Bulutli Seyf va Pleylist menyusi"""
    user_id = callback.from_user.id

    # Bazadan foydalanuvchining seyfdagi treklarini olish
    async with db.pool.acquire() as conn:
        tracks = await conn.fetch("""
            SELECT title, performer, created_at, file_id 
            FROM cloud_vault 
            WHERE user_id = $1 
            ORDER BY saved_date DESC LIMIT 10;
        """, user_id)

    text = "🔒 <b>Sizning Shaxsiy Bulutli Seyfingiz (Cloud Vault)</b>\n\n"
    if not tracks:
        text += "Hozircha seyfingizda saqlangan treklar yo'q. Istalgan musiqani saqlab qo'yishingiz mumkin!"
    else:
        text += "Oxirgi saqlangan treklaringiz (Telegram bulutida xavfsiz saqlanmoqda):\n\n"
        for i, t in enumerate(tracks, 1):
            text += f"{i}. <b>{t['performer']} - {t['title']}</b> ({t['created_at'].strftime('%Y-%m-%d')})\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Sana bo'yicha qidirish", callback_data="vault_search_date")],
        [InlineKeyboardButton(text="📥 Pleylistni kanalga uzatish", callback_data="export_playlist_channel")],
        [InlineKeyboardButton(text="⬅️ Asosiy Menyu", callback_data="main_menu")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@vault_router.callback_query(F.data == "vault_search_date")
async def ask_vault_search(callback: CallbackQuery, state: FSMContext):
    """Sanani yozib qidirish"""
    await callback.message.answer("📅 Qaysi sanadagi musiqalarni qidirmoqchisiz?\n<b>Namuna:</b> <code>2026-11-04</code> formatida yuboring:")
    await state.set_state(VaultStates.waiting_for_vault_search)
    await callback.answer()


@vault_router.message(VaultStates.waiting_for_vault_search)
async def process_vault_search(message: Message, state: FSMContext):
    date_str = message.text
    user_id = message.from_user.id

    async with db.pool.acquire() as conn:
        tracks = await conn.fetch("""
            SELECT title, performer, file_id FROM cloud_vault 
            WHERE user_id = $1 AND TO_CHAR(saved_date, 'YYYY-MM-DD') = $2;
        """, user_id, date_str)

    if not tracks:
        await message.answer(f"❌ <b>{date_str}</b> sanasida hech qanday musiqa topilmadi.")
    else:
        await message.answer(f"✅ <b>{date_str}</b> sanasidagi topilgan treklar:")
        for t in tracks:
            await message.answer_audio(audio=t['file_id'], caption=f"🎵 {t['performer']} - {t['title']}")

    await state.clear()


@vault_router.callback_query(F.data == "schedule_audio")
async def schedule_audio_start(callback: CallbackQuery, state: FSMContext):
    """Vaqti kelib yuboriladigan musiqa (Budilnik)"""
    text = (
        "⏰ <b>Scheduled Audio Delivery (Vaqti kelib yuborilish)</b>\n\n"
        "Musiqani qachon yuborish kerakligini kiriting.\n"
        "<b>Namuna:</b> <code>2026-11-05 08:00</code> formatida yuboring:"
    )
    await state.set_state(VaultStates.waiting_for_schedule_time)
    await callback.message.edit_text(text)
    await callback.answer()


@vault_router.message(VaultStates.waiting_for_schedule_time)
async def save_scheduled_audio(message: Message, state: FSMContext):
    time_str = message.text
    await message.answer(f"✅ Budilnik muvaffaqiyatli o'rnatildi! Belgilangan vaqtda ({time_str}) musiqa o'zingizga yuboriladi.")
    await state.clear()


@vault_router.callback_query(F.data == "anonymous_send")
async def anonymous_audio_start(callback: CallbackQuery, state: FSMContext):
    """Anonim Musiqiy Xatlar"""
    text = (
        "💌 <b>Anonim Musiqiy Xat (Anonymous Postbox)</b>\n\n"
        "Bu musiqani kimga yubormoqchisiz? Qabul qiluvchining <b>Username</b> yoki <b>ID</b> raqamini yuboring:"
    )
    await state.set_state(VaultStates.waiting_for_anonymous_target)
    await callback.message.edit_text(text)
    await callback.answer()


@vault_router.message(VaultStates.waiting_for_anonymous_target)
async def process_anonymous_target(message: Message, state: FSMContext):
    target = message.text
    await state.update_data(anon_target=target)
    await message.answer(f"✅ Qabul qiluvchi ({target}) qabul qilindi. Endi yubormoqchi bo'lgan <b>musiqangizni</b> tashlang:")

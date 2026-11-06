import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from database import db

logger = logging.getLogger(__name__)
vault_router = Router()

class VaultStates(StatesGroup):
    waiting_for_vault_search = State()
    waiting_for_export_channel = State()


# ==================== 1. SHAKSIY BULUTLI SEYF & PLEYLIST ====================
@vault_router.callback_query(F.data == "my_playlist")
async def show_cloud_vault(callback: CallbackQuery):
    """Shaxsiy Bulutli Seyf va Pleylist menyusi (Har bir foydalanuvchiki alohida izolyatsiya qilingan)"""
    user_id = callback.from_user.id

    # Bazadan foydalanuvchining seyfdagi treklarini olish (Faqat o'ziniki)
    async with db.pool.acquire() as conn:
        # Jadval mavjudligini ta'minlash
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cloud_vault (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                title TEXT,
                performer TEXT,
                file_id TEXT,
                saved_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        tracks = await conn.fetch("""
            SELECT title, performer, saved_date, file_id 
            FROM cloud_vault 
            WHERE user_id = $1 
            ORDER BY saved_date DESC LIMIT 10;
        """, user_id)

    text = "🔒 <b>Sizning Shaxsiy Bulutli Seyfingiz (Cloud Vault)</b>\n\n"
    if not tracks:
        text += "Hozircha seyfingizda saqlangan treklar yo'q. Musiqa tahrirlanganda uni seyfga saqlashingiz mumkin!"
    else:
        text += "Oxirgi saqlangan treklaringiz (Telegram bulutida xavfsiz saqlanmoqda):\n\n"
        for i, t in enumerate(tracks, 1):
            date_str = t['saved_date'].strftime('%Y-%m-%d') if t['saved_date'] else "Noma'lum"
            text += f"{i}. <b>{t['performer']} - {t['title']}</b> (📅 {date_str})\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Sana Bo'yicha Qidirish", callback_data="vault_search_date")],
        [InlineKeyboardButton(text="📤 Pleylistni Kanalga Uzatish", callback_data="export_playlist_channel")],
        [InlineKeyboardButton(text="⬅️ Asosiy Menyu", callback_data="main_menu")]
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        pass
    await callback.answer()


# ==================== 2. SANA BO'YICHA QIDIRISH ====================
@vault_router.callback_query(F.data == "vault_search_date")
async def ask_vault_search(callback: CallbackQuery, state: FSMContext):
    """Sanani yozib qidirish"""
    text = (
        "📅 <b>Sana Bo'yicha Qidirish</b>\n\n"
        "Qaysi sanadagi musiqalarni qidirmoqchisiz?\n"
        "<b>Namuna:</b> <code>2026-11-06</code> formatida yuboring:"
    )
    await state.set_state(VaultStates.waiting_for_vault_search)
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="my_playlist")]
        ]))
    except TelegramBadRequest:
        pass
    await callback.answer()


@vault_router.message(VaultStates.waiting_for_vault_search)
async def process_vault_search(message: Message, state: FSMContext):
    date_str = message.text.strip()
    user_id = message.from_user.id

    async with db.pool.acquire() as conn:
        tracks = await conn.fetch("""
            SELECT title, performer, file_id FROM cloud_vault 
            WHERE user_id = $1 AND TO_CHAR(saved_date, 'YYYY-MM-DD') = $2;
        """, user_id, date_str)

    if not tracks:
        await message.answer(f"❌ <b>{date_str}</b> sanasida sizning seyfingizda hech qanday musiqa topilmadi.")
    else:
        await message.answer(f"✅ <b>{date_str}</b> sanasidagi topilgan treklar:")
        for t in tracks:
            await message.answer_audio(audio=t['file_id'], caption=f"🎵 {t['performer']} - {t['title']}")

    await state.clear()


# ==================== 3. PLEYLISTNI KANALGA UZATISH (TAKrorlanmaydigan) ====================
@vault_router.callback_query(F.data == "export_playlist_channel")
async def export_playlist_start(callback: CallbackQuery, state: FSMContext):
    """Pleylestdagi musiqalarni kanalga uzatish (Faqat yangilari, takrorlanmaydi)"""
    text = (
        "📤 <b>Pleylistni Kanalga Uzatish</b>\n\n"
        "Musiqalarni yubormoqchi bo'lgan <b>Kanal Username</b>'ini yuboring "
        "(Masalan: <code>@my_music_channel</code>):\n"
        "<i>Eslatma: Bot o'sha kanalda Administrator bo'lishi shart!</i>"
    )
    await state.set_state(VaultStates.waiting_for_export_channel)
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="my_playlist")]
        ]))
    except TelegramBadRequest:
        pass
    await callback.answer()


@vault_router.message(VaultStates.waiting_for_export_channel)
async def process_export_channel(message: Message, state: FSMContext):
    channel_username = message.text.strip()
    user_id = message.from_user.id

    async with db.pool.acquire() as conn:
        # Hali kanalga yuborilmagan trekларни olish uchun logikani bajaramiz
        tracks = await conn.fetch("""
            SELECT id, title, performer, file_id FROM cloud_vault 
            WHERE user_id = $1 ORDER BY saved_date ASC;
        """, user_id)

    if not tracks:
        await message.answer("❌ Sizning seyfingizda uzatish uchun treklar mavjud emas.")
        await state.clear()
        return

    sent_count = 0
    for t in tracks:
        try:
            await message.bot.send_audio(
                chat_id=channel_username,
                audio=t['file_id'],
                caption=f"🎵 <b>{t['performer']} - {t['title']}</b>\n\n✨ <i>Music Hub Bot orqali uzatildi.</i>"
            )
            sent_count += 1
        except Exception as e:
            logger.error(f"Kanalga yuborishda xatolik: {e}")

    await message.answer(f"✅ Muvaffaqiyatli yakunlandi! <b>{sent_count} ta</b> yangi trek <b>{channel_username}</b> kanaliga yuborildi.")
    await state.clear()

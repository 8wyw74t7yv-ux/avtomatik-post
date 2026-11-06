import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from database import db

logger = logging.getLogger(__name__)
music_router = Router()

class MusicEditStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_artist = State()
    waiting_for_cover = State()


@music_router.message(F.audio | F.document)
async def handle_incoming_audio(message: Message, state: FSMContext):
    """Foydalanuvchi musiqa yuborganda chiqadigan asosiy ajratilgan boshqaruv paneli"""
    file_id = message.audio.file_id if message.audio else message.document.file_id
    title = message.audio.title if message.audio and message.audio.title else "Noma'lum trek"
    artist = message.audio.performer if message.audio and message.audio.performer else "Noma'lum artist"

    # Ma'lumotlarni state'ga saqlaymiz
    await state.update_data(current_file_id=file_id, title=title, artist=artist)

    text = (
        f"🎵 <b>Musiqa muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"<b>Nomi:</b> {title}\n"
        f"<b>Artist:</b> {artist}\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )

    # Aniq ajratilgan menyu tugmalari
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Ma'lumotlarni O'zgartirish", callback_data="music_start_edit")],
        [InlineKeyboardButton(text="🎛 51+ Effekt Berish", callback_data="music_effects_menu")],
        [InlineKeyboardButton(text="✂️ Musiqani Kesish", callback_data="cut_audio_start")],
        [InlineKeyboardButton(text="🔒 Seyfga Saqlash", callback_data="save_to_vault_direct")],
        [InlineKeyboardButton(text="⬅️ Asosiy Menyu", callback_data="main_menu")]
    ])

    await message.answer(text, reply_markup=keyboard)


# ==================== 1. TAHRIRLASH BO'LIMI ====================
@music_router.callback_query(F.data == "music_start_edit")
async def music_edit_menu(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    title = data.get("title", "Noma'lum")
    artist = data.get("artist", "Noma'lum")

    text = (
        "✏️ <b>Musiqa Ma'lumotlarini Tahrirlash</b>\n\n"
        f"Joriy Nomi: <b>{title}</b>\n"
        f"Joriy Artist: <b>{artist}</b>\n\n"
        "O'zgartirmoqchi bo'lgan qismingizni tanlang:"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏷 Musiqa Nomi (Title)", callback_data="edit_title")],
        [InlineKeyboardButton(text="🎤 Artist Ismi", callback_data="edit_artist")],
        [InlineKeyboardButton(text="🖼 Albom Rasmi", callback_data="edit_cover")],
        [InlineKeyboardButton(text="⬅️ Ortga (Audio Menyu)", callback_data="back_to_audio_menu")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        pass
    await callback.answer()


@music_router.callback_query(F.data == "edit_title")
async def ask_new_title(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✍️ Yangi trek nomini (Title) yuboring:")
    await state.set_state(MusicEditStates.waiting_for_title)
    await callback.answer()


@music_router.message(MusicEditStates.waiting_for_title)
async def save_new_title(message: Message, state: FSMContext):
    new_title = message.text.strip()
    await state.update_data(title=new_title)
    await message.answer(f"✅ Trek nomi <b>{new_title}</b> ga o'zgartirildi!")
    await show_audio_dashboard_msg(message, state)


@music_router.callback_query(F.data == "edit_artist")
async def ask_new_artist(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🎤 Yangi artist nomini yuboring:")
    await state.set_state(MusicEditStates.waiting_for_artist)
    await callback.answer()


@music_router.message(MusicEditStates.waiting_for_artist)
async def save_new_artist(message: Message, state: FSMContext):
    new_artist = message.text.strip()
    await state.update_data(artist=new_artist)
    await message.answer(f"✅ Artist nomi <b>{new_artist}</b> ga o'zgartirildi!")
    await show_audio_dashboard_msg(message, state)


@music_router.callback_query(F.data == "edit_cover")
async def ask_new_cover(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🖼 Albom uchun yangi rasm (foto) yuboring:")
    await state.set_state(MusicEditStates.waiting_for_cover)
    await callback.answer()


@music_router.message(MusicEditStates.waiting_for_cover, F.photo)
async def save_new_cover(message: Message, state: FSMContext):
    await message.answer("✅ Albom rasmi muvaffaqiyatli saqlandi!")
    await show_audio_dashboard_msg(message, state)


async def show_audio_dashboard_msg(message: Message, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    title = data.get("title", "Trek")
    artist = data.get("artist", "Artist")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Ma'lumotlarni O'zgartirish", callback_data="music_start_edit")],
        [InlineKeyboardButton(text="🎛 51+ Effekt Berish", callback_data="music_effects_menu")],
        [InlineKeyboardButton(text="✂️ Musiqani Kesish", callback_data="cut_audio_start")],
        [InlineKeyboardButton(text="🔒 Seyfga Saqlash", callback_data="save_to_vault_direct")],
        [InlineKeyboardButton(text="⬅️ Asosiy Menyu", callback_data="main_menu")]
    ])
    await message.answer(f"🎵 <b>Joriy musiqangiz:</b> {artist} - {title}\n\nKeyingi amalni tanlang:", reply_markup=keyboard)


@music_router.callback_query(F.data == "back_to_audio_menu")
async def back_to_audio_menu_cb(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    title = data.get("title", "Trek")
    artist = data.get("artist", "Artist")

    text = f"🎵 <b>Musiqa Boshqaruv Paneli</b>\n\n<b>Nomi:</b> {artist} - {title}\n\nKerakli bo'limni tanlang:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Ma'lumotlarni O'zgartirish", callback_data="music_start_edit")],
        [InlineKeyboardButton(text="🎛 51+ Effekt Berish", callback_data="music_effects_menu")],
        [InlineKeyboardButton(text="✂️ Musiqani Kesish", callback_data="cut_audio_start")],
        [InlineKeyboardButton(text="🔒 Seyfga Saqlash", callback_data="save_to_vault_direct")],
        [InlineKeyboardButton(text="⬅️ Asosiy Menyu", callback_data="main_menu")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        pass
    await callback.answer()


# ==================== 2. SEYFGA TO'G'RIDAN-TO'G'RI SAQLASH ====================
@music_router.callback_query(F.data == "save_to_vault_direct")
async def save_to_vault_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    file_id = data.get("current_file_id")
    title = data.get("title", "Noma'lum")
    artist = data.get("artist", "Noma'lum")
    user_id = callback.from_user.id

    if not file_id:
        await callback.answer("❌ Musiqa topilmadi. Qaytadan musiqa yuboring.", show_alert=True)
        return

    async with db.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO cloud_vault (user_id, file_id, title, performer)
            VALUES ($1, $2, $3, $4);
        """, user_id, file_id, title, artist)

    await callback.answer("✅ Musiqa shaxsiy bulutli seyfingizga saqlandi!", show_alert=True)


# ==================== 3. EFFEKTLARGA O'TISH ====================
@music_router.callback_query(F.data == "music_effects_menu")
async def open_effects_main_menu(callback: CallbackQuery):
    from handlers.effects import navigate_effects
    callback.data = "fx_nav_0_50"
    await navigate_effects(callback)

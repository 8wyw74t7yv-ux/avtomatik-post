import os
import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
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
    waiting_for_cut_start = State()


@music_router.message(F.audio | F.document)
async def handle_incoming_audio(message: Message, state: FSMContext):
    """Foydalanuvchi musiqa yuborganda chiqadigan asosiy vertikal boshqaruv paneli"""
    file_id = message.audio.file_id if message.audio else message.document.file_id
    title = message.audio.title if message.audio and message.audio.title else "Noma'lum trek"
    artist = message.audio.performer if message.audio and message.audio.performer else "Noma'lum artist"

    await state.update_data(current_file_id=file_id, title=title, artist=artist)

    text = (
        f"🎵 <b>Musiqa muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"<b>Nomi:</b> {title}\n"
        f"<b>Artist:</b> {artist}\n\n"
        "Kerakli bo'limni tanlang:"
    )

    # Vertikal tartibli chiroyli tugmalar
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
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_audio_menu")]
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
    
    # FFmpeg orqali metadata yangilash va faylni yuborish
    data = await state.get_data()
    await apply_metadata_and_send(message, data, state)


@music_router.callback_query(F.data == "edit_artist")
async def ask_new_artist(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🎤 Yangi artist nomini yuboring:")
    await state.set_state(MusicEditStates.waiting_for_artist)
    await callback.answer()


@music_router.message(MusicEditStates.waiting_for_artist)
async def save_new_artist(message: Message, state: FSMContext):
    new_artist = message.text.strip()
    await state.update_data(artist=new_artist)
    
    data = await state.get_data()
    await apply_metadata_and_send(message, data, state)


async def apply_metadata_and_send(message: Message, data: dict, state: FSMContext):
    file_id = data.get("current_file_id")
    title = data.get("title", "Trek")
    artist = data.get("artist", "Artist")

    processing_msg = await message.answer("⏳ <b>Musiqa ma'lumotlari FFmpeg orqali yangilanmoqda...</b>")

    file = await message.bot.get_file(file_id)
    input_file = f"input_{message.from_user.id}.mp3"
    output_file = f"output_{message.from_user.id}.mp3"

    await message.bot.download_file(file.file_path, destination=input_file)

    cmd = [
        "ffmpeg", "-y", "-i", input_file,
        "-metadata", f"title={title}",
        "-metadata", f"artist={artist}",
        "-codec", "copy", output_file
    ]

    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await process.communicate()

    if os.path.exists(output_file):
        await message.answer_audio(
            audio=FSInputFile(output_file),
            caption=f"✅ <b>Ma'lumotlar yangilandi!</b>\n🎵 {artist} - {title}",
            performer=artist,
            title=title
        )
        os.remove(output_file)
    else:
        await message.answer("❌ Xatolik yuz berdi.")

    if os.path.exists(input_file):
        os.remove(input_file)

    await processing_msg.delete()
    await state.set_state(None)
    await show_audio_dashboard_msg(message, state)


# ==================== 2. KESISH BO'LIMI ====================
@music_router.callback_query(F.data == "cut_audio_start")
async def cut_audio_instructions(callback: CallbackQuery, state: FSMContext):
    text = (
        "✂️ <b>Musiqani Aniq Kesish Tizimi</b>\n\n"
        "Musiqani qaysi sekunddan boshlab kesish kerak?\n"
        "<b>Namuna:</b> <code>15</code> (15-sekunddan boshlab) shaklida raqam yuboring:"
    )
    await state.set_state(MusicEditStates.waiting_for_cut_start)
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_audio_menu")]
        ]))
    except TelegramBadRequest:
        pass
    await callback.answer()


@music_router.message(MusicEditStates.waiting_for_cut_start)
async def process_cut_start_time(message: Message, state: FSMContext):
    try:
        start_sec = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting (Masalan: 15):")
        return

    await state.update_data(cut_start=start_sec)
    text = f"✅ Boshlanish vaqti: <b>{start_sec}s</b>\n\nKesilgan musiqaning davomiyligini tanlang:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="10s", callback_data="cut_dur_10"),
            InlineKeyboardButton(text="20s", callback_data="cut_dur_20"),
            InlineKeyboardButton(text="30s", callback_data="cut_dur_30"),
            InlineKeyboardButton(text="60s", callback_data="cut_dur_60")
        ],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_audio_menu")]
    ])
    await message.answer(text, reply_markup=keyboard)


@music_router.callback_query(F.data.startswith("cut_dur_"))
async def execute_audio_cut(callback: CallbackQuery, state: FSMContext):
    duration = int(callback.data.split("_")[2])
    data = await state.get_data()
    file_id = data.get("current_file_id")
    start_sec = data.get("cut_start", 0)
    title = data.get("title", "Trek")
    artist = data.get("artist", "Artist")

    await callback.message.edit_text("⏳ <b>Musiqa kesilmoqda va FFmpeg orqali tayyorlanmoqda...</b>")

    file = await callback.bot.get_file(file_id)
    input_file = f"input_cut_{callback.from_user.id}.mp3"
    output_file = f"output_cut_{callback.from_user.id}.mp3"

    await callback.bot.download_file(file.file_path, destination=input_file)

    cmd = [
        "ffmpeg", "-y", "-ss", str(start_sec), "-i", input_file,
        "-t", str(duration), "-c:a", "libmp3lame", output_file
    ]

    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await process.communicate()

    if os.path.exists(output_file):
        await callback.message.answer_audio(
            audio=FSInputFile(output_file),
            caption=f"✂️ <b>Musiqa muvaffaqiyatli kesildi!</b>\n🎵 {artist} - {title}",
            performer=artist,
            title=title
        )
        os.remove(output_file)
    else:
        await callback.message.answer("❌ Kesishda xatolik yuz berdi.")

    if os.path.exists(input_file):
        os.remove(input_file)

    await state.set_state(None)
    await callback.answer()


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


async def show_audio_dashboard_msg(message: Message, state: FSMContext):
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


# ==================== 3. SEYFGA SAQLASH ====================
@music_router.callback_query(F.data == "save_to_vault_direct")
async def save_to_vault_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    file_id = data.get("current_file_id")
    title = data.get("title", "Noma'lum")
    artist = data.get("artist", "Noma'lum")
    user_id = callback.from_user.id

    if not file_id:
        await callback.answer("❌ Musiqa topilmadi.", show_alert=True)
        return

    async with db.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO cloud_vault (user_id, file_id, title, performer)
            VALUES ($1, $2, $3, $4);
        """, user_id, file_id, title, artist)

    await callback.answer("✅ Musiqa shaxsiy bulutli seyfingizga saqlandi!", show_alert=True)


# ==================== 4. EFFEKTLARGA O'TISH ====================
@music_router.callback_query(F.data == "music_effects_menu")
async def open_effects_main_menu(callback: CallbackQuery):
    from handlers.effects import navigate_effects
    callback.data = "fx_nav_0_50"
    await navigate_effects(callback)

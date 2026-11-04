import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db

logger = logging.getLogger(__name__)
music_router = Router()

# FSM holatlari (Metadata o'zgartirish uchun)
class MusicEditStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_artist = State()
    waiting_for_artwork = State()

@music_router.message(F.audio)
async def handle_incoming_audio(message: Message, state: FSMContext):
    audio = message.audio
    file_unique_id = audio.file_unique_id
    file_id = audio.file_id
    title = audio.title or "Noma'lum trek"
    performer = audio.performer or "Noma'lum artist"

    # 1. Global Qora ro'yxatni (Blacklist) tekshirish
    async with db.pool.acquire() as conn:
        blacklisted = await conn.fetchval(
            "SELECT 1 FROM global_blacklist WHERE file_unique_id = $1;", file_unique_id
        )
    if blacklisted:
        await message.answer("❌ Kechirasiz, bu trek mualliflik huquqi yoki qoidalar tufayli **qora ro'yxatga kiritilgan** va botda ishlatilmaydi.")
        return

    # 2. Ma'lumotlarni state'ga vaqtincha saqlash
    await state.update_data(
        file_id=file_id,
        file_unique_id=file_unique_id,
        title=title,
        performer=performer
    )

    # 3. Foydalanuvchiga musiqani qabul qilganini bildirish va tanlov berish
    text = (
        f"🎵 <b>Musiqa muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"📌 <b>Nomi:</b> {title}\n"
        f"🎤 <b>Artist:</b> {performer}\n\n"
        f"<i>Musiqa ma'lumotlarini o'zgartiramizmi yoki shu holatda qoldiramizmi?</i>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ O'zgartiramiz", callback_data="edit_music_meta"),
            InlineKeyboardButton(text="🚀 Shart emas (Asosiy Menyu)", callback_data="skip_music_meta")
        ]
    ])

    await message.answer(text, reply_markup=keyboard)


@music_router.callback_query(F.data == "edit_music_meta")
async def process_edit_meta(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼 Albom rasmini (Cover) qo'shish", callback_data="set_cover")],
        [InlineKeyboardButton(text="📝 Musiqa nomi (Title)", callback_data="set_title")],
        [InlineKeyboardButton(text="🎤 Artist Tag (Performer)", callback_data="set_artist")],
        [InlineKeyboardButton(text="✅ Tayyor / Orqaga", callback_data="music_done")]
    ])
    await callback.message.edit_text("⚙️ Qaysi parametrni o'zgartirmoqchisiz?", reply_markup=keyboard)
    await callback.answer()


@music_router.callback_query(F.data == "set_title")
async def ask_for_title(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✍️ Yangi musiqa nomini (Title) yuboring:")
    await state.set_state(MusicEditStates.waiting_for_title)
    await callback.answer()


@music_router.message(MusicEditStates.waiting_for_title)
async def save_new_title(message: Message, state: FSMContext):
    new_title = message.text
    await state.update_data(title=new_title)
    await message.answer(f"✅ Musiqa nomi muvaffaqiyatli o'zgartirildi: <b>{new_title}</b>")
    
    # Qayta menyuni chiqarish
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼 Albom rasmini qo'shish", callback_data="set_cover")],
        [InlineKeyboardButton(text="🎤 Artist Tag qo'shish", callback_data="set_artist")],
        [InlineKeyboardButton(text="✅ Tayyor / Saqlash", callback_data="music_done")]
    ])
    await message.answer("Boshqa narsani o'zgartirasizmi?", reply_markup=keyboard)


@music_router.callback_query(F.data == "set_artist")
async def ask_for_artist(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✍️ Yangi artist nomini (Performer) yuboring:")
    await state.set_state(MusicEditStates.waiting_for_artist)
    await callback.answer()


@music_router.message(MusicEditStates.waiting_for_artist)
async def save_new_artist(message: Message, state: FSMContext):
    new_artist = message.text
    await state.update_data(performer=new_artist)
    await message.answer(f"✅ Artist nomi muvaffaqiyatli o'zgartirildi: <b>{new_artist}</b>")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼 Albom rasmini qo'shish", callback_data="set_cover")],
        [InlineKeyboardButton(text="📝 Musiqa nomi (Title)", callback_data="set_title")],
        [InlineKeyboardButton(text="✅ Tayyor / Saqlash", callback_data="music_done")]
    ])
    await message.answer("Boshqa narsani o'zgartirasizmi?", reply_markup=keyboard)


@music_router.callback_query(F.data == "set_cover")
async def ask_for_cover(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📷 Albom uchun rasm (Photo) yuboring:")
    await state.set_state(MusicEditStates.waiting_for_artwork)
    await callback.answer()


@music_router.message(MusicEditStates.waiting_for_artwork, F.photo)
async def save_new_cover(message: Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await state.update_data(artwork_file_id=photo_file_id)
    await message.answer("✅ Albom rasmi muvaffaqiyatli biriktirildi!")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tayyor / Saqlash", callback_data="music_done")]
    ])
    await message.answer("Boshqa sozlamalar uchun quyidagini bosing:", reply_markup=keyboard)


@music_router.callback_query(F.data.in_({"skip_music_meta", "music_done"}))
async def finalize_music(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    file_id = data.get("file_id")
    title = data.get("title", "Musiqa")
    performer = data.get("performer", "Artist")

    # Pleylistga avtomatik saqlash (Telegram file_id orqali, server yuklamasdan!)
    user_id = callback.from_user.id
    file_unique_id = data.get("file_unique_id")

    async with db.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO playlists (user_id, file_unique_id, file_id, title, performer)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (file_unique_id) DO NOTHING;
        """, user_id, file_unique_id, file_id, title, performer)

    await state.clear()
    
    # Efektlar va tahrirlash menyusiga o'tish tugmalari bilan yakuniy xabar
    success_text = (
        f"🎧 <b>Trek tayyor!</b>\n\n"
        f"📌 <b>{performer} - {title}</b>\n\n"
        f"Quyidagi tugmalar yordamida unga effektlar qo'shishingiz, kesishingiz yoki vizual videoga aylantirishingiz mumkin! 👇"
    )

    effects_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎛️ Effektlar menyusi", callback_data="menu_effects"),
         InlineKeyboardButton(text="✂️ Musiqani kesish", callback_data="menu_trim")],
        [InlineKeyboardButton(text="🎬 Story / Video Vizualizator", callback_data="menu_visualizer")],
        [InlineKeyboardButton(text="⬅️ Asosiy Menyu", callback_data="main_menu")]
    ])

    await callback.message.edit_text(success_text, reply_markup=effects_keyboard)
    await callback.answer()

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)
music_router = Router()

class MusicEditStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_artist = State()
    waiting_for_cover = State()
    waiting_for_cut_time = State()


@music_router.message(F.audio | F.document)
async def handle_incoming_audio(message: Message, state: FSMContext):
    """Foydalanuvchi musiqa tashlaganda ishlaydigan asosiy qabul qiluvchi"""
    file_id = message.audio.file_id if message.audio else message.document.file_id
    title = message.audio.title if message.audio and message.audio.title else "Noma'lum trek"
    artist = message.audio.performer if message.audio and message.audio.performer else "Noma'lum artist"

    # State'ga file_id va ma'lumotlarni saqlab qo'yamiz
    await state.update_data(current_file_id=file_id, title=title, artist=artist)

    text = (
        f"🎵 <b>Musiqa qabul qilindi!</b>\n\n"
        f"<b>Nomi:</b> {title}\n"
        f"<b>Artist:</b> {artist}\n\n"
        "Musiqa ma'lumotlarini (nomi, artist yoki albom rasmini) o'zgartiramizmi?"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ O'zgartiramiz", callback_data="music_start_edit"),
            InlineKeyboardButton(text="⏩ Shart emas (Effektlar menyusi)", callback_data="music_effects_menu")
        ]
    ])

    await message.answer(text, reply_markup=keyboard)


@music_router.callback_query(F.data == "music_start_edit")
async def music_edit_menu(callback: CallbackQuery):
    text = (
        "✏️ <b>Musiqa Ma'lumotlarini Tahrirlash</b>\n\n"
        "Kerakli amalni tanlang:"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼 Albom Rasmini Qo'shish", callback_data="edit_cover")],
        [InlineKeyboardButton(text="🏷 Musiqa Nomi (Title)", callback_data="edit_title")],
        [InlineKeyboardButton(text="🎤 Artist Tag Qo'shish", callback_data="edit_artist")],
        [InlineKeyboardButton(text="🎛 Effektlar Menyuiga O'tish", callback_data="music_effects_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@music_router.callback_query(F.data == "edit_title")
async def ask_new_title(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✍️ Yangi trek nomini (Title) yuboring:")
    await state.set_state(MusicEditStates.waiting_for_title)
    await callback.answer()


@music_router.message(MusicEditStates.waiting_for_title)
async def save_new_title(message: Message, state: FSMContext):
    new_title = message.text
    await state.update_data(title=new_title)
    await message.answer(f"✅ Trek nomi <b>{new_title}</b> ga o'zgartirildi!")
    await show_effects_menu_after_edit(message)
    await state.set_state(None)


@music_router.callback_query(F.data == "edit_artist")
async def ask_new_artist(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🎤 Yangi artist nomini (Artist) yuboring:")
    await state.set_state(MusicEditStates.waiting_for_artist)
    await callback.answer()


@music_router.message(MusicEditStates.waiting_for_artist)
async def save_new_artist(message: Message, state: FSMContext):
    new_artist = message.text
    await state.update_data(artist=new_artist)
    await message.answer(f"✅ Artist nomi <b>{new_artist}</b> ga o'zgartirildi!")
    await show_effects_menu_after_edit(message)
    await state.set_state(None)


@music_router.callback_query(F.data == "edit_cover")
async def ask_new_cover(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🖼 Albom uchun yangi rasm (foto) yuboring:")
    await state.set_state(MusicEditStates.waiting_for_cover)
    await callback.answer()


@music_router.message(MusicEditStates.waiting_for_cover, F.photo)
async def save_new_cover(message: Message, state: FSMContext):
    await message.answer("✅ Albom rasmi muvaffaqiyatli qo'shildi!")
    await show_effects_menu_after_edit(message)
    await state.set_state(None)


async def show_effects_menu_after_edit(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎛 50+ Effektlar Menusi", callback_data="music_effects_menu")],
        [InlineKeyboardButton(text="✂️ Musiqani Kesish", callback_data="cut_audio_start")],
        [InlineKeyboardButton(text="🎥 Video Vizualizator (Story)", callback_data="visualizer_start")]
    ])
    await message.answer("Quyidagi menyudan foydalanishingiz mumkin:", reply_markup=keyboard)


@music_router.callback_query(F.data == "music_effects_menu")
async def open_effects_main_menu(callback: CallbackQuery):
    text = (
        "🎛 <b>Professional Audio Effektlar Markazi</b>\n\n"
        "Quyidagi turkumdagi effektlardan birini tanlang:\n"
        "<i>(Har bir effekt server xotirasini band qilmasdan, Telegram file_id va FFmpeg orqali ishlaydi)</i>"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎧 8D & Reverb", callback_data="fx_page_1"),
            InlineKeyboardButton(text="🤖 Robot & Pitch", callback_data="fx_page_2")
        ],
        [
            InlineKeyboardButton(text="🎸 Bass & Booster", callback_data="fx_page_3"),
            InlineKeyboardButton(text="📻 Vinyl & Lo-Fi", callback_data="fx_page_4")
        ],
        [
            InlineKeyboardButton(text="✂️ Musiqani Kesish", callback_data="cut_audio_start"),
            InlineKeyboardButton(text="🎥 Video Vizualizator", callback_data="visualizer_start")
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

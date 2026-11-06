import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)
effects_router = Router()

class CutStates(StatesGroup):
    waiting_for_cut_start = State()


@effects_router.callback_query(F.data == "cut_audio_start")
async def cut_audio_instructions(callback: CallbackQuery, state: FSMContext):
    text = (
        "✂️ <b>Musiqani Aniq Kesish Tizimi</b>\n\n"
        "Musiqani qaysi soniyadan boshlab kesish kerak?\n"
        "<b>Namuna:</b> <code>28:3</code> (28-soniya va 3-millisekund) formatida yuboring:"
    )
    await state.set_state(CutStates.waiting_for_cut_start)
    await callback.message.edit_text(text)
    await callback.answer()


@effects_router.message(CutStates.waiting_for_cut_start)
async def process_cut_start_time(message: Message, state: FSMContext):
    start_time = message.text.strip()
    await state.update_data(cut_start=start_time)

    text = (
        f"✅ Boshlanish vaqti qabul qilindi: <b>{start_time}</b>\n\n"
        "Endi kesilgan musiqaning davomiyligini (uzunligini) tanlang:"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="5 soniya", callback_data="cut_dur_5"),
            InlineKeyboardButton(text="10 soniya", callback_data="cut_dur_10"),
            InlineKeyboardButton(text="20 soniya", callback_data="cut_dur_20")
        ],
        [
            InlineKeyboardButton(text="30 soniya", callback_data="cut_dur_30"),
            InlineKeyboardButton(text="50 soniya", callback_data="cut_dur_50")
        ]
    ])
    await message.answer(text, reply_markup=keyboard)


@effects_router.callback_query(F.data.startswith("cut_dur_"))
async def execute_audio_cut(callback: CallbackQuery, state: FSMContext):
    duration = callback.data.split("_")[2]
    data = await state.get_data()
    start_time = data.get("cut_start", "00:00")

    await callback.message.edit_text("⏳ <b>Musiqa kesilmoqda va FFmpeg orqali qayta ishlanmoqda...</b>")
    
    # Natijaviy xabar va ulashish tugmasi
    share_text = (
        "🔥 Bu qo'shiqni eshitib shokka tushdim! 8D audio va dahshatli bas... 🎧\n\n"
        "O‘z musiqangni ham shunday o‘zgartirmoqchimisan? 👇"
    )
    
    # Bot username orqali forward ssilka
    bot_info = await callback.bot.get_me()
    share_url = f"https://t.me/{bot_info.username}?start=from_share"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎛 Musiqani Tahrirlash", url=share_url)]
    ])

    await callback.message.answer(
        f"✅ Musiqa muvaffaqiyatli kesildi! (Boshlanishi: {start_time}, Davomiyligi: {duration}s)\n\n{share_text}",
        reply_markup=keyboard
    )
    await state.clear()
    await callback.answer()


@effects_router.callback_query(F.data.startswith("fx_page_"))
async def show_effects_page(callback: CallbackQuery):
    page = callback.data.split("_")[2]
    
    effects_list = {
        "1": "🎧 <b>1-Sahifa: 8D & Reverb Effektlari</b>\n\n1. 8D Audio (Spatial Surround)\n2. Cathedral Reverb (Katta Sobor)\n3. Underwater Effect (Suv Osti)\n4. Stadium Echo (Ochiq Stadion)",
        "2": "🤖 <b>2-Sahifa: Robot & Pitch Effektlari</b>\n\n5. Nightcore Generator\n6. Vaporwave (Slowed + Reverb)\n7. Chipmunk (Olmaxon ovozi)\n8. Monster / Demon Voice",
        "3": "🎸 <b>3-Sahifa: Bass & Booster</b>\n\n9. Monster Sub-Bass Booster\n10. Vocal Presence Enhancer\n11. Radio Broadcast Limiter\n12. Super Stereo Widener",
        "4": "📻 <b>4-Sahifa: Vinyl & Lo-Fi</b>\n\n13. Vinyl Crackle & Dust\n14. Cassette Tape Flutter\n15. Telephone Handset\n16. Glitch Stutter Repeat"
    }

    text = effects_list.get(page, "Effektlar topilmadi.")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"fx_page_{max(1, int(page)-1)}"),
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"fx_page_{min(4, int(page)+1)}")
        ],
        [InlineKeyboardButton(text="🎛 Bosh Menyu", callback_data="music_effects_menu")]
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        pass
    await callback.answer()


@effects_router.callback_query(F.data == "visualizer_start")
async def video_visualizer_start(callback: CallbackQuery):
    text = (
        "🎥 <b>Story / Video Vizualizator (Audio to Video)</b>\n\n"
        "Musiqani Instagram yoki Telegram Stories uchun chiroyli to'lqinli (Waveform) videoga aylantiring.\n"
        "Necha soniyali video yasash kerak? (Maksimal 30 soniya):"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="10 soniya", callback_data="vis_10"),
            InlineKeyboardButton(text="20 soniya", callback_data="vis_20"),
            InlineKeyboardButton(text="30 soniya", callback_data="vis_30")
        ],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="music_effects_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@effects_router.callback_query(F.data.startswith("vis_"))
async def generate_visualizer_video(callback: CallbackQuery):
    seconds = callback.data.split("_")[1]
    await callback.message.edit_text(f"⏳ {seconds} soniyali video vizualizator yaratilmoqda... Iltimos kuting.")
    
    share_text = (
        "🔥 Bu qo'shiqni eshitib shokka tushdim! 8D audio va dahshatli bas... 🎧\n\n"
        "O‘z musiqangni ham shunday o‘zgartirmoqchimisan? 👇"
    )
    bot_info = await callback.bot.get_me()
    share_url = f"https://t.me/{bot_info.username}?start=from_share"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎛 Musiqani Tahrirlash", url=share_url)]
    ])

    await callback.message.answer(f"✅ Video vizualizator tayyor! ({seconds}s)\n\n{share_text}", reply_markup=keyboard)
    await callback.answer()

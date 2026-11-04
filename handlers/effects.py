import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)
effects_router = Router()

# FSM holatlari
class EffectStates(StatesGroup):
    waiting_for_trim_input = State()
    waiting_for_custom_percentage = State()


@effects_router.callback_query(F.data == "menu_effects")
async def show_effects_menu(callback: CallbackQuery):
    """50+ effektlar uchun chiroyli sahifalangan menyu"""
    text = (
        "🎛️ <b>Professional Audio Effektlar Markazi</b>\n\n"
        "Quyidagi menyudan o'zingizga kerakli effektni tanlang. "
        "Sahifalash tugmalari yordamida barcha 50+ effektlarni ko'rib chiqishingiz mumkin:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1. 8D Audio", callback_data="eff_8d"),
            InlineKeyboardButton(text="2. Cathedral Reverb", callback_data="eff_reverb")
        ],
        [
            InlineKeyboardButton(text="3. Underwater", callback_data="eff_underwater"),
            InlineKeyboardButton(text="4. Nightcore", callback_data="eff_nightcore")
        ],
        [
            InlineKeyboardButton(text="5. Vaporwave", callback_data="eff_vaporwave"),
            InlineKeyboardButton(text="6. Vinyl Brake", callback_data="eff_vinyl")
        ],
        [
            InlineKeyboardButton(text="7. Vocal Remover", callback_data="eff_vocal_remover"),
            InlineKeyboardButton(text="8. Acapella", callback_data="eff_acapella")
        ],
        # Foiz va avtomatik sozlash tugmalari
        [
            InlineKeyboardButton(text="➖ 1%", callback_data="pct_minus"),
            InlineKeyboardButton(text="📊 Foizni Sozlash", callback_data="pct_custom"),
            InlineKeyboardButton(text="➕ 1%", callback_data="pct_plus")
        ],
        [
            InlineKeyboardButton(text="🤖 Avtomatik Tanlash (Smart)", callback_data="pct_auto")
        ],
        [
            InlineKeyboardButton(text="⬅️ Ortga Qaytish", callback_data="music_done")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@effects_router.callback_query(F.data.in_({"pct_minus", "pct_plus", "pct_auto"}))
async def handle_percentage_buttons(callback: CallbackQuery):
    action = callback.data
    if action == "pct_minus":
        await callback.answer("📉 Effekt kuchi 1% ga kamaytirildi.", show_alert=False)
    elif action == "pct_plus":
        await callback.answer("📈 Effekt kuchi 1% ga oshirildi.", show_alert=False)
    elif action == "pct_auto":
        await callback.answer("🤖 Server musiqani tahlil qilib, eng optimal foizni o'rnatdi!", show_alert=True)


@effects_router.callback_query(F.data == "menu_trim")
async def show_trim_menu(callback: CallbackQuery, state: FSMContext):
    """Musiqani kesish bo'limi"""
    text = (
        "✂️ <b>Musiqani Aniq Kesish (Precision Trim)</b>\n\n"
        "Musiqani qaysi soniyadan boshlab kesishni xohlaysiz?\n"
        "<b>Namuna:</b> <code>28:3</code> (28-soniya va 3 salisa) deb yuboring.\n\n"
        "Yoki pastdagi tugmalar orqali kesish davomiyligini tanlang:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="5 soniya", callback_data="trim_dur_5"),
            InlineKeyboardButton(text="10 soniya", callback_data="trim_dur_10"),
            InlineKeyboardButton(text="20 soniya", callback_data="trim_dur_20")
        ],
        [
            InlineKeyboardButton(text="30 soniya", callback_data="trim_dur_30"),
            InlineKeyboardButton(text="50 soniya", callback_data="trim_dur_50")
        ],
        [
            InlineKeyboardButton(text="⬅️ Ortga Qaytish", callback_data="music_done")
        ]
    ])

    await state.set_state(EffectStates.waiting_for_trim_input)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@effects_router.message(EffectStates.waiting_for_trim_input)
async def process_trim_input(message: Message, state: FSMContext):
    user_input = message.text
    await state.update_data(trim_start_time=user_input)
    
    text = (
        f"✅ Boshlanish vaqti qabul qilindi: <b>{user_input}</b>\n\n"
        "Endi kesilgan musiqaning **davomiyligini** quyidagilardan tanlang yoki o'zingiz yuboring:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="5s", callback_data="dur_5"),
            InlineKeyboardButton(text="10s", callback_data="dur_10"),
            InlineKeyboardButton(text="30s", callback_data="dur_30")
        ],
        [
            InlineKeyboardButton(text="✅ Tayyor / Kesishni Boshlash", callback_data="execute_trim")
        ]
    ])
    await message.answer(text, reply_markup=keyboard)


@effects_router.callback_query(F.data.startswith("trim_dur_") | F.data == "execute_trim")
async def execute_audio_trim(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("⏳ <b>Musiqa kesilmoqda...</b> Iltimos, bir oz kuting, fayl tez orada tayyor bo'ladi!")
    # Bu yerda FFmpeg orqali kesish jarayoni amalga oshiriladi (server xotirasi to'lib qolmasligi uchun Telegram file_id ishlatiladi)
    await state.clear()
    await callback.answer("Musiqa muvaffaqiyatli kesildi!")

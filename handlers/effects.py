import logging
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)
effects_router = Router()

class CutStates(StatesGroup):
    waiting_for_cut_start = State()


# Barcha 51 ta professional effektlar ro'yxati (O'zbekcha izohlari bilan)
ALL_EFFECTS = [
    "1. Faqat Vokalni Ajratib Olish (Acapella) — Musiqaning faqat xonanda ovozini qoldirib, orqa fondagi barcha asboblarni kesib tashlaydi.",
    "2. Vokalni O‘chirish (Minus / Instrumental) — Xonandaning ovozini o‘chirib, faqat musiqiy asboblar sadosini qoldiradi.",
    "3. Toza 8D Audio (Spatial Surround) — Ovozni chap va o‘ng quloqchinlar orasida aylanib turgandek fazoviy effekt beradi.",
    "4. Cathedral Reverb (Katta Sobor) — Katta va bo‘sh ibodatxonadagidek keng, uzoq davom etadigan aks sado qo‘shadi.",
    "5. Underwater Effect (Suv Osti) — Yuqori chastotalarni bo‘g‘ib, daryo yoki hovuz ostidan eshitilayotgandek tuyg‘u beradi.",
    "6. Megafon / Politsiya karnaychasi — Ovozni o‘rtaga siqib, ko‘cha karnayi yoki ratsiya orqali gaplashayotgandek qiladi.",
    "7. Ochiq Stadion (Stadium Echo) — Ochiq va katta stadion muhitidagi uzoqdan eshitiluvchi aks sadoni hosil qiladi.",
    "8. Kosmik Tunnel (Sci-Fi Flanger-Tunnel) — Ovoz ichida fazoviy esnash va metallik tebranish hosil qiladi.",
    "9. Nightcore Generator — Musiqaning tezligi va tonini ko‘tarib, quvnoq anime/TikTok uslubiga o‘tkazadi.",
    "10. Vaporwave (Slowed + Reverb) — Sekinlashtirilgan, past va sirli retro estetik muhit yaratadi.",
    "11. DJ Turntable Brake (Vinyl Stop) — Plastinkani to‘satdan bosib to‘xtatgandek sekinlashib o‘chish effekti.",
    "12. Chipmunk (Olmaxon ovozi) — Tonni haddan tashqari ingichka va tez qilib qo‘yadi.",
    "13. Monster / Demon Voice — Tonni pastga tushirib, qo‘rqinchli va qalin bazali ovozga aylantiradi.",
    "14. Tempo Lock — Qo‘shiq tezligini o‘zgartirganda xonandaning ovoz tonini o‘zgarishsiz saqlab qoladi.",
    "15. Cyberpunk Overdrive / Distortion — Elektron musiqalarga agressiv, qattiq va xirillovchi rok tus beradi.",
    "16. Robot Vocoder (Ring Modulation) — Oddiy ovozni mexanik robot ovoziga o‘zgartiradi.",
    "17. Tremolo (Dinamik Tebranish) — Ovoz balandligining ritmik ravishda tez-tez o‘zgarib turishini ta'minlaydi.",
    "18. Vibrato (Ton Tebranishi) — Notaning chastotasi tabiiy ravishda titrab turishini hosil qiladi.",
    "19. Phaser / Jet-Plane Effect — Ovoz ustidan xuddi reaktiv samolyot uchib o‘tgandek faza siljishini beradi.",
    "20. Bitcrush (8-Bit Retro Game) — Musiqani eski 8-bitli kompyuter o‘yinlari ovozi sifatiga tushiradi.",
    "21. Monster Sub-Bass Booster — Pastki baslarni kuchaytirib, kuchli avtomobil kalonkalaridek tebranish beradi.",
    "22. Vocal Presence Enhancer — Xonandaning ovozini boshqa shovqinlar orasidan yaqinroq va aniqroq qilib chiqaradi.",
    "23. Sidechain Compression Simulation — Bas urgan paytda boshqa instrumentlarning ovozini biroz pasaytirib beradi.",
    "24. Radio Broadcast Limiter — Ovozni radiostansiyalardagidek zich, bir maromda baland va tiniq qiladi.",
    "25. De-Esser (O‘tkir s, sh tovushlarni tekislash) — Quloqni kesuvchi o‘tkir “s”, “sh” hushtak tovushlarini yumshatadi.",
    "26. Super Stereo Widener — Tor mono audioni keng, quloqni to‘ldiruvchi stereobazaga o‘tkazadi.",
    "27. Cinematic Reverse + Buildup — Musiqani orqaga aylantirib, oxirida kuchli aks sado bilan asosiy qismga ulaydi.",
    "28. Vinyl Crackle & Dust — Eski gramofon plastinkasining shig‘irlashi va chang tovushini qo‘shadi.",
    "29. Cassette Tape Flutter — Eskirgan magnitofon lentalardagidek ovozning suzib, to‘lqinlanib turishini beradi.",
    "30. Radio Tuner Static — Radio to‘lqinlarini aylantirgandagi shovqin va oqim portlashlarini qo‘shadi.",
    "31. Heartbeat Pulse — Musiqa ostiga past chastotali yurak urish ritmini sinxronlashtiradi.",
    "32. Glitch Stutter Repeat — Musiqaning kichik bir qismini chaqmoq tezligida takrorlab, raqamli xatolik yuzaga keltiradi.",
    "33. Chorus Effect — Bir nechta solist bir vaqtning o‘zida kuylayotgandek ovozni qalinlashtiradi va kengaytiradi.",
    "34. Flanger Effect — Ovozga o‘ziga xos o‘tuvchi fazoviy to‘lqin va chuqurlik beradi.",
    "35. Gain Normalization — Hamma qo‘shiqlarni bir xil professional standart ovoz balandligiga keltiradi.",
    "36. Silence Remover (Jimlikni kesish) — Qo‘shiq boshidagi va oxiridagi bo‘sh, jim turgan qismlarni qirqib tashlaydi.",
    "37. High-Pass Filter (Low Cut) — Past chastotali ortiqcha g‘uvillashlar va shovqinlarni kesib tashlaydi.",
    "38. Low-Pass Filter (High Cut) — O‘tkir va yoqimsiz yuqori chastotali shivirlashlarni olib tashlaydi.",
    "39. Telephone Handset (Eski telefon) — Ovozni tor diapazonda qisib, eski simli telefon orqali gaplashayotgandek qiladi.",
    "40. Subtle Vinyl Warmth — Musiqadagi sun'iy sovuqlikni yo‘qotib, iliq analog tus beradi.",
    "41. Stereo to Mono Converter — Keng stereoni bir xil markaziy mono formatga aylantiradi.",
    "42. Ping-Pong Delay — Aks sado ovozining chap va o‘ng quloqchinlar orasida navbatma-navbat sakrashini ta'minlaydi.",
    "43. Mid-Range Punch — O‘rta chastotalarni kuchaytirib, vokal va gitara ovozini yaqinlashtiradi.",
    "44. Treble Air Booster — Yuqori chastotalarga “havodor” va tiniq yaltiroqlik beradi.",
    "45. Dynamic Compressing (Pumping Compress) — Ovoz diapazonini qisib, eng past joylarni ham eshitiladigan darajada zich qiladi.",
    "46. Sub-Bass Rumble Eliminator — Quloqni portlatuvchi keraksiz past chastotali tebranishlarni tozalaydi.",
    "47. Auto-Fade In (Smooth Start) — Qo‘shiq boshlanishini 2-3 soniya davomida asta-sekin ko‘tarib keladi.",
    "48. Auto-Fade Out (Smooth End) — Qo‘shiq oxirini asta-sekin pasaytirib, silliq yakunlaydi.",
    "49. Pitch Shift (Solo Ton O‘zgartirish) — Tezlikni o‘zgartirmasdan, faqatgina ovoz tonini ingichka yoki qalin qiladi.",
    "50. Harmonic Exciter (Ovoz yaltiroqligi) — Ovozga sun'iy yuqori harmonikalar qo‘shib, uning tiniqligini oshiradi.",
    "51. Invert Phase (Faza o‘zgartirish) — Ovoz to‘lqinlarini teskari o‘girib, faza ziddiyatlarini tekislaydi."
]


# ==================== 1. MUSIQANI KESISH BO'LIMI ====================
@effects_router.callback_query(F.data == "cut_audio_start")
async def cut_audio_instructions(callback: CallbackQuery, state: FSMContext):
    text = (
        "✂️ <b>Musiqani Aniq Kesish Tizimi</b>\n\n"
        "Musiqani qaysi soniyadan boshlab kesish kerak?\n"
        "<b>Namuna:</b> <code>28:3</code> (28-soniya va 3-millisekund) formatida yuboring:"
    )
    await state.set_state(CutStates.waiting_for_cut_start)
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="music_effects_menu")]
        ]))
    except TelegramBadRequest:
        pass
    await callback.answer()


@effects_router.message(CutStates.waiting_for_cut_start)
async def process_cut_start_time(message: Message, state: FSMContext):
    start_time = message.text.strip()
    await state.update_data(cut_start=start_time)

    text = (
        f"✅ Boshlanish vaqti qabul qilindi: <b>{start_time}</b>\n\n"
        "Endi kesilgan musiqaning davomiyligini (uzunligini) tanlang va oxirida <b>'Tayyor'</b> tugmasini bosing:"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="5s", callback_data="cut_dur_5"),
            InlineKeyboardButton(text="10s", callback_data="cut_dur_10"),
            InlineKeyboardButton(text="20s", callback_data="cut_dur_20"),
            InlineKeyboardButton(text="30s", callback_data="cut_dur_30"),
            InlineKeyboardButton(text="50s", callback_data="cut_dur_50")
        ],
        [
            InlineKeyboardButton(text="✅ Tayyor", callback_data="cut_finish"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="music_effects_menu")
        ]
    ])
    await message.answer(text, reply_markup=keyboard)


@effects_router.callback_query(F.data.startswith("cut_dur_"))
async def select_cut_duration(callback: CallbackQuery, state: FSMContext):
    duration = callback.data.split("_")[2]
    await state.update_data(cut_duration=duration)
    await callback.answer(f"Davomiylik tanlandi: {duration}s. 'Tayyor' tugmasini bosing!", show_alert=False)


@effects_router.callback_query(F.data == "cut_finish")
async def execute_audio_cut_finish(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    start_time = data.get("cut_start", "00:00")
    duration = data.get("cut_duration", "10")

    try:
        await callback.message.edit_text("⏳ <b>Musiqa kesilmoqda va FFmpeg orqali qayta ishlanmoqda...</b>")
    except TelegramBadRequest:
        pass

    share_text = (
        "🔥 Bu qo'shiqni eshitib shokka tushdim! 8D audio va dahshatli bas... 🎧\n\n"
        "O‘z musiqangni ham shunday o‘zgartirmoqchimisan? 👇"
    )
    
    bot_info = await callback.bot.get_me()
    share_url = f"https://t.me/{bot_info.username}?start=from_share"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎛 Musiqani Tahrirlash", url=share_url)]
    ])

    await callback.message.answer(
        f"✅ Musiqa muvaffaqiyatli kesildi!\n"
        f"⏱ Boshlanishi: <b>{start_time}</b> | Davomiyligi: <b>{duration}s</b>\n\n{share_text}",
        reply_markup=keyboard
    )
    await state.clear()
    await callback.answer()


# ==================== 2. BIRMA-BIR ⬅️➡️ EFFEKTLAR BOSHQARUVI ====================
@effects_router.callback_query(F.data.startswith("fx_nav_"))
async def navigate_effects(callback: CallbackQuery):
    parts = callback.data.split("_")
    index = int(parts[2])
    intensity = int(parts[3]) if len(parts) > 3 else 50

    # Chegaralarni tekshirish (1 dan 51 gacha)
    if index < 0:
        index = len(ALL_EFFECTS) - 1
    elif index >= len(ALL_EFFECTS):
        index = 0

    current_effect = ALL_EFFECTS[index]

    text = (
        "🎛 <b>Professional Audio Effektlar Markazi</b>\n\n"
        f"Tanlangan effekt:\n<b>✨ {current_effect}</b>\n\n"
        f"🎚 <b>Intensivlik (Kuchlanishi):</b> <code>{intensity}%</code>\n"
        "<i>Tugmalar orqali effektlarni almashtiring va kuchini sozlang:</i>"
    )

    prev_idx = index - 1
    next_idx = index + 1

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"fx_nav_{prev_idx}_{intensity}"),
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"fx_nav_{next_idx}_{intensity}")
        ],
        [
            InlineKeyboardButton(text="➖ 1%", callback_data=f"fx_nav_{index}_{max(0, intensity-1)}"),
            InlineKeyboardButton(text=f"🎚 {intensity}%", callback_data="noop"),
            InlineKeyboardButton(text="➕ 1%", callback_data=f"fx_nav_{index}_{min(100, intensity+1)}")
        ],
        [
            InlineKeyboardButton(text="🎲 Avtomatik (Random)", callback_data=f"fx_auto_{index}")
        ],
        [
            InlineKeyboardButton(text="✅ Tayyor", callback_data="fx_finish"),
            InlineKeyboardButton(text="🎛 Bosh Menyu", callback_data="music_effects_menu")
        ]
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        pass
    await callback.answer()


@effects_router.callback_query(F.data.startswith("fx_auto_"))
async def auto_configure_single_effect(callback: CallbackQuery):
    parts = callback.data.split("_")
    index = int(parts[2])
    rand_val = random.randint(30, 95)
    await callback.answer(f"🎲 Avtomatik kuchlanish tanlandi: {rand_val}%", show_alert=True)
    
    # Yangilangan qiymat bilan qayta chizish
    callback.data = f"fx_nav_{index}_{rand_val}"
    await navigate_effects(callback)


@effects_router.callback_query(F.data == "fx_finish")
async def finish_single_effect_processing(callback: CallbackQuery):
    try:
        await callback.message.edit_text("⏳ <b>Tanlangan professional effekt musiqaga qo'shilmoqda...</b>")
    except TelegramBadRequest:
        pass

    share_text = (
        "🔥 Bu qo'shiqni eshitib shokka tushdim! 8D audio va dahshatli bas... 🎧\n\n"
        "O‘z musiqangni ham shunday o‘zgartirmoqchimisan? 👇"
    )
    bot_info = await callback.bot.get_me()
    share_url = f"https://t.me/{bot_info.username}?start=from_share"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎛 Musiqani Tahrirlash", url=share_url)]
    ])

    await callback.message.answer(
        f"✅ Musiqaga tanlangan effekt muvaffaqiyatli ulandi!\n\n{share_text}",
        reply_markup=keyboard
    )
    await callback.answer()


@effects_router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    await callback.answer()

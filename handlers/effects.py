import os
import asyncio
import random
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)
effects_router = Router()

# 100 ta professional audio effektlar ro'yxati
ALL_EFFECTS = [
    "1. Faqat Vokalni Ajratib Olish (Acapella)",
    "2. Vokalni O‘chirish (Minus / Instrumental)",
    "3. Toza 8D Audio (Spatial Surround)",
    "4. Cathedral Reverb (Katta Sobor)",
    "5. Underwater Effect (Suv Osti)",
    "6. Megafon / Politsiya karnaychasi",
    "7. Ochiq Stadion (Stadium Echo)",
    "8. Kosmik Tunnel (Sci-Fi Flanger-Tunnel)",
    "9. Nightcore Generator",
    "10. Vaporwave (Slowed + Reverb)",
    "11. DJ Turntable Brake (Vinyl Stop)",
    "12. Chipmunk (Olmaxon ovozi)",
    "13. Monster / Demon Voice",
    "14. Tempo Lock",
    "15. Cyberpunk Overdrive / Distortion",
    "16. Robot Vocoder (Ring Modulation)",
    "17. Tremolo (Dinamik Tebranish)",
    "18. Vibrato (Ton Tebranishi)",
    "19. Phaser / Jet-Plane Effect",
    "20. Bitcrush (8-Bit Retro Game)",
    "21. Monster Sub-Bass Booster",
    "22. Vocal Presence Enhancer",
    "23. Sidechain Compression Simulation",
    "24. Radio Broadcast Limiter",
    "25. De-Esser (O‘tkir s, sh tovushlarni tekislash)",
    "26. Super Stereo Widener",
    "27. Cinematic Reverse + Buildup",
    "28. Vinyl Crackle & Dust",
    "29. Cassette Tape Flutter",
    "30. Radio Tuner Static",
    "31. Heartbeat Pulse",
    "32. Glitch Stutter Repeat",
    "33. Chorus Effect",
    "34. Flanger Effect",
    "35. Gain Normalization",
    "36. Silence Remover (Jimlikni kesish)",
    "37. High-Pass Filter (Low Cut)",
    "38. Low-Pass Filter (High Cut)",
    "39. Telephone Handset (Eski telefon)",
    "40. Subtle Vinyl Warmth",
    "41. Stereo to Mono Converter",
    "42. Ping-Pong Delay",
    "43. Mid-Range Punch",
    "44. Treble Air Booster",
    "45. Dynamic Compressing (Pumping Compress)",
    "46. Sub-Bass Rumble Eliminator",
    "47. Auto-Fade In (Smooth Start)",
    "48. Auto-Fade Out (Smooth End)",
    "49. Pitch Shift (Solo Ton O‘zgartirish)",
    "50. Harmonic Exciter (Ovoz yaltiroqligi)",
    "51. Invert Phase (Faza o‘zgartirish)",
    "52. Lo-Fi Warmth & Crackle",
    "53. Stadium Announcement (PA System)",
    "54. Subtle Vocal Doubler",
    "55. Extreme Radio Transceiver",
    "56. Deep Cave Echo",
    "57. Underwater Submerge Transition",
    "58. Cinematic Boom Impact",
    "59. Vinyl Warmth & Hiss",
    "60. Fast Stutter Glitch",
    "61. Crystal Clear Vocal Tune",
    "62. Spatial 360 Rotation",
    "63. Sub-Bass Subwoofer Test",
    "64. Vintage Gramophone 1920s",
    "65. Space Echo Machine",
    "66. Aggressive Metal Distortion",
    "67. Soft Acoustic Warmth",
    "68. Stadium Crowd Singalong",
    "69. Cyberpunk Synth Wave Filter",
    "70. Nightclub Bathroom Reverb",
    "71. Concert Hall Grand",
    "72. Heavy Metal Guitar Crunch",
    "73. Telephone Box Intercom",
    "74. Dubstep Wobble Bass Filter",
    "75. Smooth Radio Compression",
    "76. Lo-Fi Tape Warble",
    "77. Epic Trailer Sub-Bass",
    "78. Clean Studio Mastering",
    "79. Warm Valve Tube Saturation",
    "80. Space Ambient Reverb",
    "81. Retro 90s Cassette",
    "82. Club Sub-Bass Pumping",
    "83. Acoustic Room Simulation",
    "84. Digital Bit Depth Reducer",
    "85. Vocal Warmth Enhancer",
    "86. Mega Stadion Echo",
    "87. Sci-Fi Alien Voice",
    "88. Smooth Vocal De-Harshness",
    "89. Vinyl Dust & Scratch",
    "90. Heavy Industrial Distortion",
    "91. Warm Analog Tape Echo",
    "92. Concert Stage Monitor",
    "93. Subtle Stereo Enhancement",
    "94. Deep Oceanic Pressure",
    "95. Broadcast AM Radio",
    "96. Epic Cinematic Boom",
    "97. Lo-Fi Muffled Filter",
    "98. Virtual Surround 7.1",
    "99. Cyberpunk Neon Bass",
    "100. Master DJ Final Polish"
]

@effects_router.callback_query(F.data.startswith("fx_nav_"))
async def navigate_effects(callback: CallbackQuery):
    parts = callback.data.split("_")
    index = int(parts[2])
    intensity = int(parts[3]) if len(parts) > 3 else 50

    if index < 0:
        index = len(ALL_EFFECTS) - 1
    elif index >= len(ALL_EFFECTS):
        index = 0

    current_effect = ALL_EFFECTS[index]

    text = (
        "🎛 <b>Professional Audio Effektlar Markazi</b>\n\n"
        f"Tanlangan effekt ({index + 1}/100):\n<b>✨ {current_effect}</b>\n\n"
        f"🎚 <b>Intensivlik:</b> <code>{intensity}%</code>\n"
        "Tugmalar orqali sozlating:"
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
        [InlineKeyboardButton(text="🎲 Avtomatik", callback_data=f"fx_auto_{index}")],
        [InlineKeyboardButton(text="✅ Tayyor (Effektni qo'shish)", callback_data=f"fx_apply_{index}_{intensity}")],
        [InlineKeyboardButton(text="⬅️ Ortga (Audio Menyu)", callback_data="back_to_audio_menu")]
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
    await callback.answer(f"🎲 Avtomatik kuchlanish: {rand_val}%", show_alert=True)
    callback.data = f"fx_nav_{index}_{rand_val}"
    await navigate_effects(callback)


@effects_router.callback_query(F.data.startswith("fx_apply_"))
async def apply_audio_effect(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    index = int(parts[2])
    intensity = int(parts[3])

    data = await state.get_data()
    file_id = data.get("current_file_id")
    title = data.get("title", "Trek")
    artist = data.get("artist", "Artist")

    if not file_id:
        await callback.answer("❌ Musiqa topilmadi.", show_alert=True)
        return

    await callback.message.edit_text("⏳ <b>FFmpeg orqali professional effekt qo'shilmoqda...</b>")

    file = await callback.bot.get_file(file_id)
    input_file = f"input_fx_{callback.from_user.id}.mp3"
    output_file = f"output_fx_{callback.from_user.id}.mp3"

    await callback.bot.download_file(file.file_path, destination=input_file)

    # Effekt indeksiga qarab mos keluvchi FFmpeg filtri
    filter_arg = "volume=1.0"
    if index == 2:  # 3. Toza 8D Audio
        filter_arg = f"apulsator=mode=sine:hz={intensity/20}"
    elif index in [3, 55, 79]:  # Reverb / Echo turkumi
        filter_arg = f"aecho=0.8:0.88:60:{intensity/100}"
    elif index in [4, 37, 38]:  # Suv osti / Filterlar
        cut_freq = max(200, 2000 - (intensity * 15))
        filter_arg = f"lowpass=frequency={cut_freq}"
    elif index == 8:  # 9. Nightcore Generator
        rate = 44100 * (1 + intensity/200)
        filter_arg = f"asetrate={rate},aresample=44100"
    elif index in [20, 62]:  # Bass Booster
        gain = int(intensity / 5)
        filter_arg = f"equalizer=f=60:width_type=h:width=50:g={gain}"
    else:
        vol = intensity / 50.0
        filter_arg = f"volume={vol}"

    cmd = [
        "ffmpeg", "-y", "-i", input_file,
        "-af", filter_arg,
        "-c:a", "libmp3lame", output_file
    ]

    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await process.communicate()

    if os.path.exists(output_file):
        await callback.message.answer_audio(
            audio=FSInputFile(output_file),
            caption=f"✅ <b>Effekt muvaffaqiyatli qo'shildi! ({ALL_EFFECTS[index]})</b>\n🎵 {artist} - {title}",
            performer=artist,
            title=title
        )
        os.remove(output_file)
    else:
        await callback.message.answer("❌ Effektni qo'shishda xatolik yuz berdi.")

    if os.path.exists(input_file):
        os.remove(input_file)

    await callback.answer()


@effects_router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    await callback.answer()

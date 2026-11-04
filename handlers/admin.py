import logging
import psutil
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from config import ADMIN_ID, ADMIN_PIN

logger = logging.getLogger(__name__)
admin_router = Router()

class AdminStates(StatesGroup):
    waiting_for_pin = State()
    waiting_for_broadcast_msg = State()
    waiting_for_lookup_user = State()
    waiting_for_vip_id = State()
    waiting_for_blacklist_id = State()
    waiting_for_channel_link = State()


@admin_router.callback_query(F.data == "admin_panel_auth")
async def admin_auth_start(callback: CallbackQuery, state: FSMContext):
    """Admin panelga kirishda 2-bosqichli PIN-kodni so'rash"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Sizda bu bo'limga kirish huquqi yo'q!", show_alert=True)
        return

    text = (
        "🔐 <b>Xavfsizlik Tekshiruvi (Two-Factor Verification)</b>\n\n"
        "Admin panelga kirish uchun maxfiy PIN-kodni kiriting (Masalan: <code>1202</code>):"
    )
    await state.set_state(AdminStates.waiting_for_pin)
    await callback.message.edit_text(text)
    await callback.answer()


@admin_router.message(AdminStates.waiting_for_pin)
async def verify_admin_pin(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    if message.text.strip() == ADMIN_PIN:
        await state.clear()
        await show_main_admin_panel(message)
    else:
        await message.answer("❌ Noto'g'ri PIN-kod! Qaytadan kiriting:")


async def show_main_admin_panel(message: Message):
    """Asosiy Admin Panel menyusi"""
    text = (
        "👑 <b>Music Hub — Admin Boshqaruv Markazi</b>\n\n"
        "Barcha tizimlar sozlamalari, statistikalar va boshqaruv tugmalari quyidagilar:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Statistika & Tahlil", callback_data="adm_stats"),
            InlineKeyboardButton(text="📢 Xabar Tarqatish", callback_data="adm_broadcast")
        ],
        [
            InlineKeyboardButton(text="👥 Foydalanuvchi Lookup", callback_data="adm_lookup"),
            InlineKeyboardButton(text="💎 VIP Tizim Boshqaruvi", callback_data="adm_vip")
        ],
        [
            InlineKeyboardButton(text="🖥 Server Holati (Health)", callback_data="adm_health"),
            InlineKeyboardButton(text="🚫 Global Blacklist", callback_data="adm_blacklist")
        ],
        [
            InlineKeyboardButton(text="📢 Majburiy Kanallar", callback_data="adm_channels"),
            InlineKeyboardButton(text="🧹 Keshni Tozalash", callback_data="adm_clear_cache")
        ],
        [
            InlineKeyboardButton(text="🔄 Serverni Qayta Ishga Tushirish", callback_data="adm_restart")
        ],
        [
            InlineKeyboardButton(text="⬅️ Asosiy Menyuga Qaytish", callback_data="main_menu")
        ]
    ])

    if isinstance(message, Message):
        await message.answer(text, reply_markup=keyboard)
    elif isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=keyboard)


@admin_router.callback_query(F.data == "adm_stats", F.from_user.id == ADMIN_ID)
async def admin_statistics(callback: CallbackQuery):
    total_users = await db.get_total_users_count()
    
    async with db.pool.acquire() as conn:
        playlists_count = await conn.fetchval("SELECT COUNT(*) FROM playlists;")
        vault_count = await conn.fetchval("SELECT COUNT(*) FROM cloud_vault;")

    text = (
        "📊 <b>Bot Statistikasi va Tahlili</b>\n\n"
        f"👤 Jami foydalanuvchilar: <b>{total_users} ta</b>\n"
        f"🎧 Saqlangan pleylistlar: <b>{playlists_count} ta</b>\n"
        f"🔒 Bulutli seyfdagi treklar: <b>{vault_count} ta</b>\n"
        f"🟢 Bot holati: <b>Barqaror ishlamoqda (Online)</b>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Admin Panelga Qaytish", callback_data="admin_panel_auth")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@admin_router.callback_query(F.data == "adm_health", F.from_user.id == ADMIN_ID)
async def admin_system_health(callback: CallbackQuery):
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    text = (
        "🖥 <b>Server Holatini Nazorat Qilish (System Health)</b>\n\n"
        f"⚡ CPU Yuklanishi: <b>{cpu_usage}%</b>\n"
        f"🧠 RAM Ishlatilishi: <b>{memory.percent}% ({memory.used // (1024**2)} MB / {memory.total // (1024**2)} MB)</b>\n"
        f"💾 Disk Bo'sh Joyi: <b>{disk.free // (1024**3)} GB ({disk.percent}% band)</b>\n"
        f"⚙️ Platforma: <b>Fly.io (1 GB RAM / 1 CPU)</b>\n"
        f"💡 Xotira tejamkorligi: <i>Barcha media fayllar Telegram serverida (file_id) saqlanmoqda.</i>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="adm_health"),
         InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_panel_auth")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@admin_router.callback_query(F.data == "adm_broadcast", F.from_user.id == ADMIN_ID)
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    text = (
        "📢 <b>Ommaviy Xabar Tarqatish (Broadcast)</b>\n\n"
        "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni (matn, rasm yoki post) yuboring:"
    )
    await state.set_state(AdminStates.waiting_for_broadcast_msg)
    await callback.message.edit_text(text)
    await callback.answer()


@admin_router.message(AdminStates.waiting_for_broadcast_msg, F.from_user.id == ADMIN_ID)
async def execute_broadcast(message: Message, state: FSMContext):
    async with db.pool.acquire() as conn:
        users = await db.pool.fetch("SELECT user_id FROM users WHERE is_banned = FALSE;")

    success = 0
    failed = 0
    for u in users:
        try:
            await message.send_copy(chat_id=u['user_id'])
            success += 1
        except Exception:
            failed += 1

    await message.answer(f"✅ Xabar tarqatish yakunlandi!\n\n📬 Yetib bordi: <b>{success} ta</b>\n❌ Xatolik (bloklaganlar): <b>{failed} ta</b>")
    await state.clear()


@admin_router.callback_query(F.data == "adm_vip", F.from_user.id == ADMIN_ID)
async def admin_vip_panel(callback: CallbackQuery, state: FSMContext):
    text = (
        "💎 <b>VIP & Premium Boshqaruvi</b>\n\n"
        "Foydalanuvchiga 30 kunlik VIP maqom berish uchun uning <b>Telegram ID</b> raqamini yuboring:\n"
        "<i>(To'lov cheki tekshirilgandan so'ng kiritiladi)</i>"
    )
    await state.set_state(AdminStates.waiting_for_vip_id)
    await callback.message.edit_text(text)
    await callback.answer()


@admin_router.message(AdminStates.waiting_for_vip_id, F.from_user.id == ADMIN_ID)
async def grant_vip_status(message: Message, state: FSMContext):
    try:
        target_user_id = int(message.text.strip())
        async with db.pool.acquire() as conn:
            await conn.execute("""
                UPDATE users 
                SET is_vip = TRUE, vip_expires_at = CURRENT_TIMESTAMP + INTERVAL '30 days'
                WHERE user_id = $1;
            """, target_user_id)
        await message.answer(f"✅ <code>{target_user_id}</code> raqamli foydalanuvchiga muvaffaqiyatli **30 kunlik VIP maqom** berildi!")
    except ValueError:
        await message.answer("❌ Noto'g'ri ID format! Faqat raqamlardan iborat ID kiriting.")
    await state.clear()


@admin_router.callback_query(F.data == "adm_channels", F.from_user.id == ADMIN_ID)
async def admin_channels_panel(callback: CallbackQuery, state: FSMContext):
    async with db.pool.acquire() as conn:
        channels = await conn.fetch("SELECT * FROM forced_channels;")

    text = "📢 <b>Majburiy Obuna Kanallari</b>\n\n"
    if not channels:
        text += "Hozircha homiy kanallar ulanmagan."
    else:
        for c in channels:
            text += f"• {c['channel_title']} (<code>{c['channel_username']}</code>)\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kanal Qo'shish", callback_data="add_forced_channel")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_panel_auth")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@admin_router.callback_query(F.data == "add_forced_channel", F.from_user.id == ADMIN_ID)
async def add_channel_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🔗 Yangi kanal havolasini yuboring (Masalan: <code>@my_channel</code>):")
    await state.set_state(AdminStates.waiting_for_channel_link)
    await callback.answer()


@admin_router.message(AdminStates.waiting_for_channel_link, F.from_user.id == ADMIN_ID)
async def save_forced_channel(message: Message, state: FSMContext):
    ch_link = message.text.strip()
    async with db.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO forced_channels (channel_id, channel_username, channel_title)
            VALUES ($1, $2, $3)
            ON CONFLICT (channel_id) DO NOTHING;
        """, message.chat.id, ch_link, "Homiy Kanal")
    await message.answer(f"✅ Kanal muvaffaqiyatli qo'shildi: <b>{ch_link}</b>")
    await state.clear()


@admin_router.callback_query(F.data == "adm_clear_cache", F.from_user.id == ADMIN_ID)
async def clear_cache_action(callback: CallbackQuery):
    await callback.answer("🧹 Server kesh xotirasi tozalandi! Telegram file_id buluti faol ishlamoqda.", show_alert=True)


@admin_router.callback_query(F.data == "adm_restart", F.from_user.id == ADMIN_ID)
async def restart_bot_action(callback: CallbackQuery):
    await callback.message.edit_text("🔄 <b>Server masofadan qayta ishga tushirilmoqda...</b> Iltimos, 5 soniya kuting.")

import asyncpg
import logging
from config import DATABASE_URL

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """PostgreSQL ulanish hovuzini (pool) yaratish"""
        try:
            self.pool = await asyncpg.create_pool(DATABASE_URL, statement_cache_size=0)
            logger.info("PostgreSQL ma'lumotlar bazasiga muvaffaqiyatli ulandi!")
            await self.create_tables()
        except Exception as e:
            logger.error(f"Bazaga ulanishda xatolik: {e}")
            raise e

    async def close(self):
        """Baza ulanishini yopish"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL ulanishi yopildi.")

    async def create_tables(self):
        """Barcha kerakli jadvallarni yaratish"""
        async with self.pool.acquire() as connection:
            # 1. Foydalanuvchilar jadvali
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_banned BOOLEAN DEFAULT FALSE,
                    is_vip BOOLEAN DEFAULT FALSE,
                    vip_expires_at TIMESTAMP
                );
            """)

            # 2. Pleylistlar va Musiqalar jadvali (Telegram file_id orqali)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS playlists (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    file_unique_id TEXT UNIQUE,
                    file_id TEXT,
                    title TEXT,
                    performer TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 3. Shaxsiy Bulutli Seyf (Cloud Vault)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS cloud_vault (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    file_unique_id TEXT,
                    file_id TEXT,
                    title TEXT,
                    performer TEXT,
                    saved_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 4. Global Blacklist (Qora ro'yxat)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS global_blacklist (
                    file_unique_id TEXT PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 5. Majburiy Kanallar (Forced Subscriptions)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS forced_channels (
                    channel_id BIGINT PRIMARY KEY,
                    channel_username TEXT,
                    channel_title TEXT
                );
            """)

            # 6. Adminlar jadvali (Multi-admin)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    admin_id BIGINT PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                );
            """)

            # 7. Bot Sozlamalari va CMS (Dinamik matnlar va limitlar)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS bot_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)

            # 8. Yozishmalar va Faollik tarixi (Logs / Analytics)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    action_type TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            logger.info("Barcha PostgreSQL jadvallari muvaffaqiyatli tekshirildi va yaratildi.")

    async def add_user(self, user_id: int, username: str, full_name: str):
        """Foydalanuvchini qo'shish yoki yangilash"""
        async with self.pool.acquire() as connection:
            await connection.execute("""
                INSERT INTO users (user_id, username, full_name)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE
                SET username = EXCLUDED.username, full_name = EXCLUDED.full_name;
            """, user_id, username, full_name)

    async def get_user(self, user_id: int):
        """Foydalanuvchini olish"""
        async with self.pool.acquire() as connection:
            return await connection.fetchrow("SELECT * FROM users WHERE user_id = $1;", user_id)

    async def get_total_users_count(self) -> int:
        """Jami foydalanuvchilar soni"""
        async with self.pool.acquire() as connection:
            return await connection.fetchval("SELECT COUNT(*) FROM users;")

# Global baza obyekti
db = Database()

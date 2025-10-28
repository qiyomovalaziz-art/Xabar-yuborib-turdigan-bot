import logging
import asyncio
from datetime import datetime
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ChatMemberUpdated

# =============================
# ⚙️ Sozlamalar
# =============================
API_TOKEN = "8246546890:AAHBwTmRyEgjqpEY4otaQIoTFGh3VUq-YYQ"  # Bot tokenini shu yerga yozing
ADMIN_ID = 7973934849               # Sizning Telegram ID'ingiz
DB_PATH = "group_events.db"
# =============================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


# =============================
# 📦 Ma'lumotlar bazasi funksiyalari
# =============================
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT,
                chat_id INTEGER,
                chat_title TEXT,
                user_id INTEGER,
                user_name TEXT,
                event_type TEXT,
                detail TEXT
            )
        """)
        await db.commit()


async def log_event(chat, user, event_type, detail=""):
    now = datetime.utcnow().isoformat()
    chat_title = getattr(chat, "title", str(chat.id))
    user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or f"@{user.username}" or "Noma'lum"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO events (time, chat_id, chat_title, user_id, user_name, event_type, detail)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (now, chat.id, chat_title, user.id, user_name, event_type, detail))
        await db.commit()


async def notify_admin(text: str):
    try:
        await bot.send_message(ADMIN_ID, text, parse_mode="HTML")
    except Exception as e:
        logging.warning(f"Adminga xabar yuborishda xato: {e}")


# =============================
# 👥 Guruhdagi qo‘shilish / chiqish hodisalari
# =============================
@dp.message_handler(content_types=types.ContentTypes.NEW_CHAT_MEMBERS)
async def on_new_member(message: types.Message):
    for user in message.new_chat_members:
        text = (f"➕ <b>Yangi foydalanuvchi qo‘shildi</b>\n"
                f"👥 Guruh: <code>{message.chat.title}</code>\n"
                f"👤 Foydalanuvchi: {user.full_name} "
                f"(@{user.username or '–'})\n🕒 {datetime.utcnow().isoformat()}")
        await log_event(message.chat, user, "joined")
        await notify_admin(text)


@dp.message_handler(content_types=types.ContentTypes.LEFT_CHAT_MEMBER)
async def on_left_member(message: types.Message):
    user = message.left_chat_member
    text = (f"➖ <b>Foydalanuvchi chiqdi</b>\n"
            f"👥 Guruh: <code>{message.chat.title}</code>\n"
            f"👤 Foydalanuvchi: {user.full_name} "
            f"(@{user.username or '–'})\n🕒 {datetime.utcnow().isoformat()}")
    await log_event(message.chat, user, "left")
    await notify_admin(text)


# =============================
# 🔄 ChatMember yangilanishlari (status o‘zgarishi)
# =============================
@dp.chat_member_handler()
async def on_chat_member_update(update: ChatMemberUpdated):
    old_status = update.old_chat_member.status
    new_status = update.new_chat_member.status
    if old_status != new_status:
        user = update.new_chat_member.user
        text = (f"🔁 <b>Foydalanuvchi statusi o‘zgardi</b>\n"
                f"👥 Guruh: <code>{update.chat.title}</code>\n"
                f"👤 {user.full_name} (@{user.username or '–'})\n"
                f"🌀 {old_status} → {new_status}\n"
                f"🕒 {datetime.utcnow().isoformat()}")
        await log_event(update.chat, user, "status_change", f"{old_status}→{new_status}")
        await notify_admin(text)


# =============================
# 🔘 Buyruqlar
# =============================
@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    await message.reply("👋 Salom!\n"
                        "Men guruhga kim kirgan yoki chiqqanini kuzatib boraman.\n"
                        "Adminga avtomatik xabar yuboraman.")


@dp.message_handler(commands=["events"])
async def cmd_events(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Siz admin emassiz.")
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT time, chat_title, user_name, event_type FROM events ORDER BY id DESC LIMIT 10")
        rows = await cur.fetchall()
    if not rows:
        await message.reply("📭 Hali hech qanday voqea yo‘q.")
        return
    text = "<b>📜 So‘nggi 10 voqea:</b>\n\n"
    for t, chat, user, ev in rows:
        text += f"🕒 {t}\n👥 {chat}\n👤 {user}\n📌 {ev}\n\n"
    await message.reply(text, parse_mode="HTML")


# =============================
# 🚀 Ishga tushirish
# =============================
async def on_startup(dp):
    await init_db()
    await notify_admin("✅ Bot ishga tushdi va guruhlarni kuzatishni boshladi.")


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)

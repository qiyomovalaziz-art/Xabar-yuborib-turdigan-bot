# watch_user_changes.py
import logging
import asyncio
import aiosqlite
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.utils.exceptions import ChatNotFound, Unauthorized, BadRequest, RetryAfter

API_TOKEN = "8246546890:AAHBwTmRyEgjqpEY4otaQIoTFGh3VUq-YYQ"  # <-- bu yerga token yozing
ADMIN_ID = 7973934849               # <-- bu yerga o‘zingizning Telegram ID’ingizni yozing

DB_PATH = "users.db"
CHECK_INTERVAL_SECONDS = 60 * 10  # fon tekshiruv oralig‘i (10 daqiqa)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


# --- DB helperlar ---
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                last_seen TEXT
            )
        """)
        await db.commit()


async def save_or_update_user(user: types.User):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users (id, first_name, last_name, username, last_seen)
            VALUES (?, ?, ?, ?, ?)
        """, (user.id, user.first_name or "", user.last_name or "", user.username or "", now))
        await db.commit()


async def get_stored_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id, first_name, last_name, username, last_seen FROM users WHERE id = ?", (user_id,))
        return await cur.fetchone()


async def update_stored_user_fields(user_id: int, first_name, last_name, username):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users SET first_name = ?, last_name = ?, username = ?, last_seen = ? WHERE id = ?
        """, (first_name or "", last_name or "", username or "", now, user_id))
        await db.commit()


async def get_all_user_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM users")
        rows = await cur.fetchall()
        return [r[0] for r in rows]


# --- Xabar yuborish ---
async def notify_admin(text: str):
    try:
        await bot.send_message(ADMIN_ID, text)
    except Exception:
        logging.exception("Adminga xabar yuborishda xato")


# --- Foydalanuvchi ma’lumotlarini solishtirish ---
def detect_changes(old_data, new_user: types.User):
    _, old_first, old_last, old_username, _ = old_data
    changes = []

    if (old_first or "") != (new_user.first_name or ""):
        changes.append(f"🧾 Ism o‘zgardi: {old_first} ➜ {new_user.first_name}")
    if (old_last or "") != (new_user.last_name or ""):
        changes.append(f"🧾 Familiya o‘zgardi: {old_last} ➜ {new_user.last_name}")
    if (old_username or "") != (new_user.username or ""):
        changes.append(f"🧾 Username o‘zgardi: @{old_username} ➜ @{new_user.username}")

    return changes


# --- Tekshirish jarayoni ---
async def check_users_loop():
    while True:
        try:
            ids = await get_all_user_ids()
            logging.info(f"Tekshirilmoqda: {len(ids)} foydalanuvchi...")
            for uid in ids:
                try:
                    user_chat = await bot.get_chat(uid)
                    stored = await get_stored_user(uid)
                    if stored:
                        changes = detect_changes(stored, user_chat)
                        if changes:
                            msg = f"⚙️ Foydalanuvchi ma’lumotlari o‘zgardi:\n\n" \
                                  f"ID: `{uid}`\n" \
                                  f"{chr(10).join(changes)}"
                            await notify_admin(msg)
                            await update_stored_user_fields(uid, user_chat.first_name, user_chat.last_name, user_chat.username)
                except ChatNotFound:
                    logging.warning(f"ChatNotFound: foydalanuvchi {uid}")
                except Unauthorized:
                    logging.warning(f"Unauthorized: foydalanuvchi {uid}")
                except RetryAfter as e:
                    logging.warning(f"Rate limit {e.timeout}s kutish...")
                    await asyncio.sleep(e.timeout)
                except BadRequest as e:
                    logging.warning(f"BadRequest: {e}")
                await asyncio.sleep(0.5)
        except Exception:
            logging.exception("Tekshiruvda xato")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


# --- Komandalar ---
@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    await save_or_update_user(message.from_user)
    await message.reply("👋 Salom! Men sizning ma’lumotlaringizni kuzataman.")


@dp.message_handler(commands=["track"])
async def cmd_track(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Foydalanuvchi ID kiriting: /track <id>")
        return
    try:
        target_id = int(parts[1])
        user_chat = await bot.get_chat(target_id)
        await save_or_update_user(user_chat)
        await message.reply(f"🔍 Kuzatuvga qo‘shildi:\n\n"
                            f"Ism: {user_chat.first_name}\n"
                            f"Familiya: {user_chat.last_name}\n"
                            f"Username: @{user_chat.username}\n"
                            f"ID: {user_chat.id}")
    except Exception as e:
        await message.reply(f"Xato: {e}")


@dp.message_handler(commands=["list"])
async def cmd_list(message: types.Message):
    users = await get_all_user_ids()
    if not users:
        await message.reply("Hech kim kuzatuvda emas.")
    else:
        text = "📋 Kuzatilayotgan foydalanuvchilar ID ro‘yxati:\n\n"
        text += "\n".join(str(u) for u in users)
        await message.reply(text)


@dp.message_handler()
async def any_message(message: types.Message):
    await save_or_update_user(message.from_user)


# --- Asosiy ishga tushirish ---
async def on_startup(dp):
    await init_db()
    asyncio.create_task(check_users_loop())
    await notify_admin("✅ Bot ishga tushdi va foydalanuvchilarni kuzatishni boshladi.")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

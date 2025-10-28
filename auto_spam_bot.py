import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ----------------------------
# ⚙️ Sozlamalar
# ----------------------------
API_TOKEN = "8246546890:AAHBwTmRyEgjqpEY4otaQIoTFGh3VUq-YYQ"   # <-- bu yerga BotFather'dan olingan tokenni yozing
ADMIN_ID = 7973934849                # <-- bu yerga o'z Telegram ID'ingizni yozing
ALLOWED_GROUPS = [-10017384342819]  # <-- siz kuzatmoqchi bo'lgan guruh ID
# ----------------------------

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ----------------------------
# ➕ Kimdir guruhga qo‘shildi
# ----------------------------
@dp.message_handler(content_types=types.ContentTypes.NEW_CHAT_MEMBERS)
async def on_new_member(message: types.Message):
    if message.chat.id not in ALLOWED_GROUPS:
        return
    chat = message.chat
    for user in message.new_chat_members:
        text = (
            f"➕ <b>Yangi foydalanuvchi qo‘shildi</b>\n"
            f"👥 Guruh: <code>{chat.title}</code>\n"
            f"👤 {user.full_name} (@{user.username or '–'})\n"
            f"🕒 {datetime.utcnow().isoformat()}"
        )
        await bot.send_message(ADMIN_ID, text, parse_mode="HTML")

# ----------------------------
# ➖ Kimdir guruhdan chiqdi
# ----------------------------
@dp.message_handler(content_types=types.ContentTypes.LEFT_CHAT_MEMBER)
async def on_left_member(message: types.Message):
    if message.chat.id not in ALLOWED_GROUPS:
        return
    chat = message.chat
    user = message.left_chat_member
    text = (
        f"➖ <b>Foydalanuvchi chiqdi</b>\n"
        f"👥 Guruh: <code>{chat.title}</code>\n"
        f"👤 {user.full_name} (@{user.username or '–'})\n"
        f"🕒 {datetime.utcnow().isoformat()}"
    )
    await bot.send_message(ADMIN_ID, text, parse_mode="HTML")

# ----------------------------
# 🔄 Status o‘zgarishini kuzatish
# ----------------------------
@dp.chat_member_handler()
async def on_member_update(update: types.ChatMemberUpdated):
    if update.chat.id not in ALLOWED_GROUPS:
        return

    old_status = update.old_chat_member.status
    new_status = update.new_chat_member.status
    if old_status != new_status:
        user = update.new_chat_member.user
        chat = update.chat
        text = (
            f"🔁 <b>Status o‘zgardi</b>\n"
            f"👥 Guruh: <code>{chat.title}</code>\n"
            f"👤 {user.full_name} (@{user.username or '–'})\n"
            f"🔸 {old_status} → {new_status}\n"
            f"🕒 {datetime.utcnow().isoformat()}"
        )
        await bot.send_message(ADMIN_ID, text, parse_mode="HTML")

# ----------------------------
# 🟢 /start buyrug‘i
# ----------------------------
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.reply(
        "👋 Salom! Men faqat siz belgilagan guruhdagi kirish, chiqish va status o‘zgarishlarini kuzataman."
    )

# ----------------------------
# 🚀 Ishga tushirish
# ----------------------------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

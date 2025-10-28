import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ⚙️ Sozlamalar
API_TOKEN = "8246546890:AAHBwTmRyEgjqpEY4otaQIoTFGh3VUq-YYQ"     # Bot tokenini shu yerga yoz
ADMIN_ID = 7973934849                  # O'zingning Telegram ID'ingni yoz
ALLOWED_GROUPS = [--1002451428746]     # Guruh ID (-100 bilan boshlanadi)

# 📋 Log sozlamasi
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


# ✅ Guruhga yangi a'zo kirganda
@dp.message_handler(content_types=['new_chat_members'])
async def new_member(message: types.Message):
    for member in message.new_chat_members:
        text = (
            f"🟢 <b>Yangi a'zo qo‘shildi:</b>\n"
            f"👤 Ism: <code>{member.full_name}</code>\n"
            f"🆔 ID: <code>{member.id}</code>\n"
            f"📅 Guruh: {message.chat.title}"
        )
        await bot.send_message(ADMIN_ID, text, parse_mode="HTML")


# ❌ Guruhdan foydalanuvchi chiqsa yoki chiqarilsa
@dp.message_handler(content_types=['left_chat_member'])
async def member_left(message: types.Message):
    user = message.left_chat_member
    text = (
        f"🔴 <b>A'zo chiqdi yoki chiqarildi:</b>\n"
        f"👤 Ism: <code>{user.full_name}</code>\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📅 Guruh: {message.chat.title}"
    )
    await bot.send_message(ADMIN_ID, text, parse_mode="HTML")


# 🧩 Start komandasi
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "👋 Salom! Men siz belgilagan guruhdagi kirish va chiqish holatlarini "
        "sutka davomida kuzatib boraman va sizga xabar yuboraman."
    )


# 🚀 Ishga tushirish
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

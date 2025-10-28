from aiogram import Bot, Dispatcher, types, executor
import os

API_TOKEN = ("8246546890:AAHBwTmRyEgjqpEY4otaQIoTFGh3VUq-YYQ")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Faqat admin ID (o'zingning Telegram ID'ingni shu yerga yoz)
ADMIN_ID = 7973934849  # bu joyga o'zingning ID'ingni qo'y
message_text = "Hozircha xabar yo‘q."  # dastlabki matn

# /start buyrug'i
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer("Assalomu alaykum! Admin xabarini yuboraman.")
    await bot.send_message(message.chat.id, message_text)

# Admin xabar yuborsa, uni saqlaymiz
@dp.message_handler(lambda msg: msg.from_user.id == ADMIN_ID)
async def admin_msg(msg: types.Message):
    global message_text
    message_text = msg.text
    await msg.answer("✅ Xabar yangilandi. Endi yangi foydalanuvchilarga shu xabar yuboriladi.")

# Oddiy foydalanuvchi yozsa — e’tibor bermaymiz
@dp.message_handler()
async def ignore_msg(msg: types.Message):
    pass

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

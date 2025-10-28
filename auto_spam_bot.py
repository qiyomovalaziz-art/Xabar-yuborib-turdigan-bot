import asyncio
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = 'BOT_TOKEN_BU_YERGA_YOZ'  # BotFather dan olingan token
INTERVAL = 2  # soniyada (har 2 soniyada xabar yuboradi)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

user_message = None
target_chat_id = None
is_running = False

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    global target_chat_id
    target_chat_id = msg.chat.id
    await msg.answer("Salom! Menga bir marta matn yubor, men uni har 2 soniyada yuborib turaman.")

@dp.message_handler()
async def get_message(msg: types.Message):
    global user_message, is_running, target_chat_id

    if target_chat_id is None:
        target_chat_id = msg.chat.id

    user_message = msg.text
    is_running = True
    await msg.answer(f"✅ Xabar qabul qilindi: '{user_message}'\nHar 2 soniyada yuborishni boshlayman.")

    while is_running:
        try:
            await bot.send_message(target_chat_id, user_message)
            await asyncio.sleep(INTERVAL)
        except Exception as e:
            print(f"Xatolik: {e}")
            break

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

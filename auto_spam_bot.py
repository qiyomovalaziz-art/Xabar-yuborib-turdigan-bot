import asyncio
import json
import os
from aiogram import Bot, Dispatcher, executor, types

# --- Sozlamalar ---
API_TOKEN = os.getenv("8246546890:AAHBwTmRyEgjqpEY4otaQIoTFGh3VUq-YYQ")  # BotFather'dan olingan token, Railway ENV da saqlanadi
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)  # Admin Telegram ID
INTERVAL = 2  # soniyada yuborish intervali

DATA_FILE = "subscribers.json"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- Faylni o'qish / yozish funksiyalari ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"subs": [], "message": "Hozircha xabar yo'q."}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"subs": [], "message": "Hozircha xabar yo'q."}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()
subscribers = set(data.get("subs", []))
admin_message = data.get("message", "Hozircha xabar yo'q.")

# --- /myid buyrug'i (admin ID ni bilish uchun) ---
@dp.message_handler(commands=["myid"])
async def myid_cmd(msg: types.Message):
    await msg.answer(f"Sizning ID'ingiz: {msg.from_user.id}")

# --- /start buyrug'i ---
@dp.message_handler(commands=["start"])
async def start_cmd(msg: types.Message):
    chat_id = msg.chat.id
    if chat_id not in subscribers:
        subscribers.add(chat_id)
        data["subs"] = list(subscribers)
        save_data(data)
        await msg.answer("✅ Siz obunaga qo'shildingiz. Admin xabarini olasiz.")
    else:
        await msg.answer("Siz allaqachon obunadasiz.")
    await bot.send_message(chat_id, admin_message)

# --- /unsubscribe yoki /stop ---
@dp.message_handler(commands=["unsubscribe", "stop"])
async def unsubscribe_cmd(msg: types.Message):
    chat_id = msg.chat.id
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        data["subs"] = list(subscribers)
        save_data(data)
        await msg.answer("❌ Siz obunadan chiqarildingiz.")
    else:
        await msg.answer("Siz obunada emassiz.")

# --- /setmsg (faqat admin uchun) ---
@dp.message_handler(commands=["setmsg"])
async def setmsg_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("Sizda ruxsat yo'q.")
        return

    if msg.reply_to_message and msg.reply_to_message.text:
        new_text = msg.reply_to_message.text
    else:
        args = msg.get_args()
        if not args:
            await msg.answer("Iltimos: /setmsg <matn> yoki xabarga reply qilib /setmsg yuboring.")
            return
        new_text = args

    global admin_message
    admin_message = new_text
    data["message"] = admin_message
    save_data(data)
    await msg.answer("✅ Xabar yangilandi.\nYangi xabar:\n" + admin_message)

# --- /getmsg (hozirgi xabarni ko'rish, admin uchun) ---
@dp.message_handler(commands=["getmsg"])
async def getmsg_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("Sizda ruxsat yo'q.")
        return
    await msg.answer("Hozirgi xabar:\n" + admin_message)

# --- Xabar yuborish vazifasi ---
async def periodic_sender():
    await asyncio.sleep(3)
    while True:
        if not subscribers:
            await asyncio.sleep(1)
            continue
        for chat_id in list(subscribers):
            try:
                await bot.send_message(chat_id, admin_message)
            except Exception as e:
                print(f"Xato {chat_id}: {e}")
            await asyncio.sleep(0.1)
        await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_sender())
    executor.start_polling(dp, skip_updates=True)

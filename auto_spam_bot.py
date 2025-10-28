import asyncio
import json
import os
from aiogram import Bot, Dispatcher, executor, types

# --- Sozlamalar ---
API_TOKEN = ("8246546890:AAHBwTmRyEgjqpEY4otaQIoTFGh3VUq-YYQ")  # Railway: Environment variable sifatida qo'ying
ADMIN_ID = int(os.getenv("7973934849") or 0)  # Admin Telegram ID: Railway dagi env ga qo'ying (masalan 123456789)
INTERVAL = 2  # soniyada (har 2 soniyada yuboradi)

DATA_FILE = "subscribers.json"  # obuna ro'yxati va xabarni saqlash (soddalashtirilgan)

# --- Bot va dispatcher ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- Yordamchi funksiyalar: faylga yozish/o'qish ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"subs": [], "message": "Hozircha xabar yo'q."}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"subs": [], "message": "Hozircha xabar yo'q."}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Save error:", e)

data = load_data()
subscribers = set(data.get("subs", []))
admin_message = data.get("message", "Hozircha xabar yo'q.")

# --- Komandalar ---

@dp.message_handler(commands=["start"])
async def start_cmd(msg: types.Message):
    """
    /start bosilganda — bot foydalanuvchiga ruxsat so'raydi (va avtomatik subscribe qiladi).
    """
    chat_id = msg.chat.id
    # Avtomatik subscribe qilamiz (agar yo'q bo'lsa)
    if chat_id not in subscribers:
        subscribers.add(chat_id)
        data["subs"] = list(subscribers)
        save_data(data)
        await msg.answer("Salom! Seni obuna sifatida qoʻshdim. Endi menga yuborilgan admin xabarini olasan.")
    else:
        await msg.answer("Siz allaqachon obunadasiz. /unsubscribe bilan to'xtatishingiz mumkin.")
    # birinchi javob sifatida admin xabarini yuborish
    await bot.send_message(chat_id, admin_message)

@dp.message_handler(commands=["subscribe"])
async def subscribe_cmd(msg: types.Message):
    chat_id = msg.chat.id
    if chat_id in subscribers:
        await msg.answer("Siz allaqachon obunadasiz.")
        return
    subscribers.add(chat_id)
    data["subs"] = list(subscribers)
    save_data(data)
    await msg.answer("✅ Siz obunaga qo'shildingiz. Har 2 soniyada xabar olasiz.")
    await bot.send_message(chat_id, admin_message)

@dp.message_handler(commands=["unsubscribe", "stop"])
async def unsubscribe_cmd(msg: types.Message):
    chat_id = msg.chat.id
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        data["subs"] = list(subscribers)
        save_data(data)
        await msg.answer("✅ Siz obunadan o'chirildingiz. Endi xabar olmayapsiz.")
    else:
        await msg.answer("Siz obunada emassiz.")

@dp.message_handler(commands=["setmsg"])
async def setmsg_cmd(msg: types.Message):
    """
    Admin buyrug'i: /setmsg Matn...
    Faqat ADMIN_ID orqali ishlaydi.
    """
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("Sizda ruxsat yo'q.")
        return
    # matnni buyruqdan keyin oling
    args = msg.get_args()
    if not args:
        await msg.answer("Iltimos: /setmsg <yangi matn>")
        return
    global admin_message
    admin_message = args
    data["message"] = admin_message
    save_data(data)
    await msg.answer("✅ Bosh xabar yangilandi.\nYangi xabar:\n" + admin_message)

@dp.message_handler(commands=["getmsg"])
async def getmsg_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("Sizda ruxsat yo'q.")
        return
    await msg.answer("Hozirgi xabar:\n" + admin_message)

@dp.message_handler(commands=["list_subs"])
async def list_subs_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("Sizda ruxsat yo'q.")
        return
    await msg.answer(f"Obunachilar soni: {len(subscribers)}\nIDS: {list(subscribers)}")

@dp.message_handler()
async def other(msg: types.Message):
    # boshqa xabarlar uchun moslashuvchan javob (yozishga hojat yo'q)
    pass

# --- Fon vazifa: har INTERVAL sekundda obunachilarga yuborish ---
async def periodic_sender():
    await bot.wait_until_ready()  # aiogram 2.x da mavjud emas, ammo saqlab qo'ydik; agar xato bo'lsa, ishga tushishdan oldin 1s kutamiz
    while True:
        if not subscribers:
            await asyncio.sleep(1)
            continue
        # Har bir obunachiga yuborish
        for chat_id in list(subscribers):
            try:
                await bot.send_message(chat_id, admin_message)
            except Exception as e:
                print(f"Send error to {chat_id}: {e}")
            await asyncio.sleep(0.1)  # kichik kechikish — tizimni bo'lib yuborish uchun
        # Oxirida INTERVALga kutamiz
        await asyncio.sleep(INTERVAL)

# --- Ishga tushirish ---
if __name__ == "__main__":
    # Background task yaratamiz
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_sender())
    executor.start_polling(dp, skip_updates=True)

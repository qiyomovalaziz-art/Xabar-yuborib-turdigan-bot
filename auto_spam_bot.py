# bot_profile_linker.py
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = "BOT_TOKEN_HERE"  # <- BotFather'dan olgan tokenni shu yerga qo'ying

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    waiting_for_id = State()
    waiting_for_label = State()

@dp.message_handler(commands=['start', 'help'])
async def cmd_start(message: types.Message):
    await Form.waiting_for_id.set()
    await message.reply("Salom! Foydalanuvchi ID sini kiriting (raqamli ID yoki @username).")

@dp.message_handler(state=Form.waiting_for_id, content_types=types.ContentTypes.TEXT)
async def process_id(message: types.Message, state: FSMContext):
    text = message.text.strip()
    # saqlaymiz
    await state.update_data(target=text)
    await Form.waiting_for_label.set()
    await message.reply("Endi tugma uchun matn kiriting (masalan: 'Profilga o‘tish').")

@dp.message_handler(state=Form.waiting_for_label, content_types=types.ContentTypes.TEXT)
async def process_label(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target = data.get("target")
    label = message.text.strip() or "Profilga oʻtish"

    # Har doim urinib ko'ramiz: agar @username yoki username mavjud bo'lsa, t.me link ishlatamiz.
    # Aks holda tg://user?id=ID linkni beramiz.
    url = None

    # Agar foydalanuvchi '@username' tarzida kiritgan bo'lsa
    if target.startswith("@"):
        username = target[1:]
        url = f"https://t.me/{username}"
    else:
        # target raqamli ID bo'lgandek ko'rinadi; lekin u holda ham get_chat orqali usernameni aniqlashga urinib ko'ramiz
        try:
            # 'get_chat' bilan username bo'lsa chat.username o'zgaradi
            chat = await bot.get_chat(chat_id=target)
            username = getattr(chat, "username", None)
            if username:
                url = f"https://t.me/{username}"
            else:
                # username yo'q — fallback: tg://user?id=ID
                url = f"tg://user?id={chat.id}"
        except Exception as e:
            # Agar get_chat xato bersa (masalan noto'g'ri ID), fallback sifatida tg:// link yasashga urinib ko'ramiz
            try:
                # agar target butun raqam bo'lsa
                numeric = int(target)
                url = f"tg://user?id={numeric}"
            except Exception:
                await message.reply("Kiritilgan ID/username noto'g'ri yoki aniqlab bo'lmadi. Iltimos qayta urinib ko'ring.")
                await state.finish()
                return

    # Inline tugma yaratamiz
    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text=label, url=url)
    keyboard.add(button)

    await message.reply("Mana tugma — bosganingizda profilga o'tishga urinadi:", reply_markup=keyboard)
    # tozalaymiz state
    await state.finish()

@dp.message_handler()
async def fallback(message: types.Message):
    await message.reply("Bot ishlamoqda. /start ni bosing va foydalanuvchi ID yoki @username kiriting.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

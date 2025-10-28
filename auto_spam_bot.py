# bot_profile_button.py
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

API_TOKEN = "8246546890:AAHBwTmRyEgjqpEY4otaQIoTFGh3VUq-YYQ"  # BotFather'dan olingan tokenni shu yerga qo'ying

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
    await message.reply("Salom! Foydalanuvchi ID sini yuboring (raqam yoki @username).")

@dp.message_handler(state=Form.waiting_for_id, content_types=types.ContentTypes.TEXT)
async def process_id(message: types.Message, state: FSMContext):
    target = message.text.strip()
    await state.update_data(target=target)
    await Form.waiting_for_label.set()
    await message.reply("Endi tugma uchun matn (soʻz) yuboring. Tugma bosilganda profil ochiladi (iman qilsak).")

@dp.message_handler(state=Form.waiting_for_label, content_types=types.ContentTypes.TEXT)
async def process_label(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target = data.get("target")
    label = message.text.strip() or "Profilga o'tish"

    url = None

    # 1) Agar @username ni berishgan bo'lsa
    if isinstance(target, str) and target.startswith("@"):
        username = target[1:]
        url = f"https://t.me/{username}"
    else:
        # 2) Agar raqamli ID bo'lsa urinish: get_chat orqali usernameni aniqlashga harakat qilamiz
        try:
            # Agar target raqam yoki string formatidagi raqam bo'lsa ishlaydi
            chat = await bot.get_chat(chat_id=target)
            username = getattr(chat, "username", None)
            if username:
                url = f"https://t.me/{username}"
            else:
                # username yo'q: fallback tg:// link
                user_id = int(chat.id)
                url = f"tg://user?id={user_id}"
        except Exception as e:
            # noto'g'ri ID yoki boshqa xato: tekshirib ko'ramiz agar plain raqam yuborilgan bo'lsa
            try:
                numeric = int(str(target).strip())
                url = f"tg://user?id={numeric}"
            except Exception:
                await message.reply("Kiritilgan ID/username noto'g'ri yoki aniqlab bo'lmadi. Iltimos to'g'ri ID yoki @username kiriting.")
                await state.finish()
                return

    # Inline tugma yaratamiz
    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text=label, url=url)
    keyboard.add(button)

    # Sinovdan o'tkazish uchun konsolga chiqaramiz (server log)
    logging.info(f"Created profile button for target={target} url={url}")

    try:
        await message.reply("Tugma tayyor — bosganingizda profilni ochishga urinadi:", reply_markup=keyboard)
    except Exception as err:
        # Ba'zan Telegram serveri 'BadRequest: Button_user_invalid' kabi xatolik beradi
        logging.exception("Failed to send button")
        await message.reply(f"Tugma yuborishda xatolik yuz berdi: {err}\nEhtimol tg:// link platformingizda ishlamaydi. Foydalanuvchining @username bor-yo'qligini tekshiring.")
    finally:
        await state.finish()

@dp.message_handler()
async def fallback(message: types.Message):
    await message.reply("Ishlamoqda. /start ni bosing va foydalanuvchi ID yoki @username kiriting.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

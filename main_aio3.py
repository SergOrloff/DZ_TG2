import os
import logging
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from dotenv import load_dotenv
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from googletrans import Translator
from gtts import gTTS

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем значения из .env файла
API_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Установите уровень логирования
logging.basicConfig(level=logging.INFO)

# Токен вашего бота
# API_TOKEN = 'YOUR_BOT_TOKEN'

# Инициализация бота и диспетчера
session = AiohttpSession()
bot = Bot(token=API_TOKEN, session=session)
# Создаем роутер
router = Router()

# Регистрация обработчика для callback_query
@router.callback_query(F.data.startswith('lang_'))
async def process_callback_query(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer(f"You selected {callback_query.data}")

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_router(router)

# Создаем папки, если они не существуют
os.makedirs('img', exist_ok=True)
os.makedirs('voice', exist_ok=True)

# Инициализация переводчика
translator = Translator()

# Словарь для хранения выбранного языка каждого пользователя
user_language = {}

# Счетчики для имен файлов
photo_counter = {}
voice_counter = {}

# Список доступных языков
available_languages = {
    'en': 'Английский',
    'ru': 'Русский',
    'uk': 'Украинский',
    'es': 'Испанский',
    'it': 'Итальянский',
    'de': 'Немецкий',
    'fr': 'Французский',
    'zh-TW': 'Китайский',
    'pt-PT': 'Португальский',
    'tr': 'Турецкий',
    'fi': 'Финский',
    'uz': 'Узбекский',
    'ja': 'Японский',
    # Добавьте другие языки по желанию
}


# Создаем клавиатуру с кнопками

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='📷 Загрузить фото', callback_data="photo"),
            KeyboardButton(text='🔤 Перевести текст', callback_data="text")
        ],
        [
            KeyboardButton(text='🌐 Выбрать язык', callback_data="text"),
            KeyboardButton(text='🆘 Помощь')
        ]
    ],
    resize_keyboard=True
)

# Обработчик команды /start
@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    user_language[message.from_user.id] = 'en'  # Устанавливаем английский по умолчанию
    await message.answer(
        "Привет! Я могу сохранить ваше фото и перевести текст на выбранный вами язык с голосовым дублированием.",
        reply_markup=keyboard  # Убедитесь, что keyboard определен
    )

    try:
# Создаём голосовое сообщение
        tts = gTTS(text="Здравствуйте! Я ваш бот-помощник.", lang='ru')
        tts.save("voice_message.ogg")

        # Отправляем голосовое сообщение
        voice = FSInputFile("voice_message.ogg")
        await bot.send_voice(chat_id=message.chat.id, voice=voice)
        # with open("voice_message.ogg", 'rb') as voice:
        #     await message.answer_voice(voice)
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        # Удаляем файл голосового сообщения
        if os.path.exists("voice_message.ogg"):
            os.remove("voice_message.ogg")


# Обработчик команды /help
@dp.message(Command('help'))
async def send_help(message: types.Message):
    help_text = (
        "🆘 *Справка по боту:*\n\n"
        "• Нажмите кнопку 📷 *Загрузить фото*, чтобы отправить фото и сохранить его.\n"
        "• Нажмите кнопку 🔤 *Перевести текст*, чтобы отправить текст для перевода на выбранный язык с голосовым "
        "дублированием.\n"
        "• Нажмите кнопку 🌐 *Выбрать язык*, чтобы изменить язык перевода.\n"
        "• Нажмите кнопку 🆘 *Помощь*, чтобы увидеть это сообщение.\n"
        "• Вы также можете использовать команды:\n"
        "  - /start - начать работу с ботом.\n"
        "  - /help - показать это сообщение помощи.\n"
    )
    await message.reply(help_text, parse_mode='Markdown', reply_markup=keyboard)


# Хендлер для обработки нажатия на кнопку '📷 Загрузить фото'
@dp.message(lambda message: message.text == '📷 Загрузить фото')
async def handle_upload_photo(message: types.Message):
    await message.answer("Пожалуйста, отправьте фото, которое вы хотите загрузить.")


# Хендлер для обработки нажатия на кнопку '🔤 Перевести текст'
@dp.message(lambda message: message.text == '🔤 Перевести текст')
async def handle_translate_text(message: types.Message):
    await message.answer("Пожалуйста, отправьте текст, который вы хотите перевести.")


# # Хендлер для обработки нажатия на кнопку '🌐 Выбрать язык'
@dp.message(lambda message: message.text == '🌐 Выбрать язык')
async def handle_select_language(message: types.Message):
    buttons = [
        InlineKeyboardButton(text=lang_name, callback_data=lang_code)
        for lang_code, lang_name in available_languages.items()
    ]
    # Если количество кнопок нечетное, добавляем последнюю кнопку отдельно
    if len(buttons) % 2 != 0:
        # Создаем клавиатуру с кнопками в два столбика
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [buttons[i], buttons[i + 1]] for i in range(0, len(buttons) - 1, 2)
        ])
        inline_kb.inline_keyboard.append([buttons[-1]])
    elif len(buttons) % 2 == 0:
        # Создаем клавиатуру с кнопками в два столбика
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [buttons[i], buttons[i + 1]] for i in range(0, len(buttons), 2)
        ])
    await message.reply("Пожалуйста, выберите язык для перевода:", reply_markup=inline_kb)


# Обработчик нажатия на кнопки выбора языка
@dp.callback_query(lambda c: c.data in available_languages.keys())
# @dp.callback_query(lambda c: c.data.startswith('lang_'))
async def process_language_selection(callback_query: types.CallbackQuery):
    lang_code = callback_query.data  # Извлекаем код языка
    # print(lang_code)
    user_language[callback_query.from_user.id] = lang_code  # Сохраняем выбранный язык
    # print(user_language[callback_query.from_user.id])
    # Уведомляем Telegram, что запрос был обработан
    await bot.answer_callback_query(callback_query.id)
    lang_name = available_languages[callback_query.data]
    # print(lang_name)
    # Отправляем подтверждение пользователю
    await bot.send_message(callback_query.from_user.id, f"Вы выбрали язык: {lang_name}", reply_markup=keyboard)


# Хендлер для обработки нажатия на кнопку '🆘 Помощь'
@dp.message(lambda message: message.text == '🆘 Помощь')
async def send_help(message: types.Message):
    help_text = (
        "🆘 *Справка по боту:*\n\n"
        "• Нажмите кнопку 📷 *Загрузить фото*, чтобы отправить фото и сохранить его.\n"
        "• Нажмите кнопку 🔤 *Перевести текст*, чтобы отправить текст для перевода на выбранный язык с голосовым "
        "дублированием.\n"
        "• Нажмите кнопку 🌐 *Выбрать язык*, чтобы изменить язык перевода.\n"
        "• Нажмите кнопку 🆘 *Помощь*, чтобы увидеть это сообщение.\n"
        "• Вы также можете использовать команды:\n"
        "  - /start - начать работу с ботом.\n"
        "  - /help - показать это сообщение помощи.\n"
    )
    await message.reply(help_text, parse_mode='Markdown', reply_markup=keyboard)


# Обработчик фото с более коротким именем файла
@router.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    # Инициализируем счетчик для пользователя, если его еще нет
    if user_id not in photo_counter:
        photo_counter[user_id] = 1
    else:
        photo_counter[user_id] += 1

    photo = message.photo[-1]
    file_id = photo.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    downloaded_file = await bot.download_file(file_path)
    # Генерируем более короткое имя файла
    file_name = f'img/photo_{user_id}_{photo_counter[user_id]}.jpg'
    with open(file_name, 'wb') as f:
        f.write(downloaded_file.read())
    await message.reply("Фото сохранено!", reply_markup=keyboard)


# Обработчик текстовых сообщений с голосовым дублированием
@router.message(F.text)
async def handle_text(message: Message):
    text = message.text
    if text in ['📷 Загрузить фото', '🔤 Перевести текст', '🆘 Помощь', '🌐 Выбрать язык']:
        # Если это текст кнопок, не обрабатываем его как обычный текст
        return
    user_id = message.from_user.id
    target_lang = user_language.get(user_id, 'en')  # Получаем выбранный язык, по умолчанию английский
    print(target_lang)
    # Переводим текст на выбранный язык
    try:
        translated = translator.translate(text, dest=target_lang)
    except Exception as e:
        await message.reply("Ошибка при переводе текста. Пожалуйста, попробуйте еще раз.")
        logging.error(f"Ошибка при переводе: {e}")
        return
    translated_text = translated.text
    # Отправляем текстовый перевод
    await message.reply(
        f"Перевод на {available_languages.get(target_lang, 'выбранный язык')}:\n{translated_text}",
        reply_markup=keyboard
    )
    # Генерируем голосовое сообщение с переведенным текстом
    # Инициализируем счетчик для голосовых сообщений
    if user_id not in voice_counter:
        voice_counter[user_id] = 1
    else:
        voice_counter[user_id] += 1

    # Разбиваем текст на части по 300 символов
    max_length = 300
    text_parts = [translated_text[i:i + max_length] for i in range(0, len(translated_text), max_length)]

    for index, part in enumerate(text_parts):
        # Создаем голосовое сообщение для каждой части
        try:
            tts = gTTS(text=part, lang=target_lang)
        except Exception as e:
            await message.reply("Ошибка при создании голосового сообщения. Пожалуйста, попробуйте еще раз.")
            logging.error(f"Ошибка при создании голосового сообщения: {e}")
            return
        voice_file_name = f'voice/voice_{user_id}_{voice_counter[user_id]}_{index}.ogg'
        tts.save(voice_file_name)
        # Отправляем голосовое сообщение
        voice = FSInputFile(voice_file_name)
        await bot.send_audio(message.chat.id, voice)
        # Удаляем файл после отправки
        os.remove(voice_file_name)
    # Увеличиваем счетчик голосовых сообщений
    voice_counter[user_id] += len(text_parts) - 1  # Уже увеличили на 1 ранее


# Функция для запуска бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
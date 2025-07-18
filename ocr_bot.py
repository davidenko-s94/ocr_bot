import asyncio
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CommandHandler
import pytesseract
from PIL import Image
import tempfile
import nest_asyncio

# === Настройки ===

# Укажи путь к Tesseract (только для Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# === Функция OCR ===
def ocr_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='eng+rus')  # поддержка русского и английского
        return text.strip()
    except Exception as e:
        return f"Ошибка при распознавании: {e}"

# === Обработчики команд ===
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Отправь мне фото, и я распознаю на нём текст.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ Это OCR-бот. Он распознаёт текст на изображениях.\n\n"
        "Как пользоваться:\n"
        "1. Сделай фото документа или текста.\n"
        "2. Отправь его сюда.\n"
        "3. Бот пришлёт распознанный текст."
    )
    await update.message.reply_text(text)

async def ocr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📸 Чтобы использовать OCR:\n"
        "1. Сделайте чёткое фото документа или текста.\n"
        "2. Отправьте его сюда.\n"
        "3. Бот распознает текст и отправит вам его копию."
    )
    await update.message.reply_text(text)

# === Обработчик фото ===
import time

from datetime import datetime

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📷 Получено фото. Обрабатываю...")

    photo = update.message.photo[-1]
    file = await photo.get_file()

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmpfile:
        tmp_path = tmpfile.name
        await file.download_to_drive(tmp_path)

    extracted_text = ocr_image(tmp_path)
    os.unlink(tmp_path)  # Удаляем временный файл

    if extracted_text:
        # === Сохранение фото и текста с именем пользователя и датой ===
        SAVE_DIR = "ocr_results"
        os.makedirs(SAVE_DIR, exist_ok=True)

        # Получаем имя пользователя
        user = update.effective_user
        username = user.username or f"{user.first_name}_{user.last_name}" or "unknown_user"
        username = username.replace(" ", "_")  # Заменяем пробелы

        # Текущая дата и время
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Пути для сохранения
        photo_path = os.path.join(SAVE_DIR, f"{username}_{now}_photo.jpg")
        text_path = os.path.join(SAVE_DIR, f"{username}_{now}_text.txt")

        # Сохраняем фото
        photo_file = await photo.get_file()
        await photo_file.download_to_drive(photo_path)

        # Сохраняем текст
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)

        # === Конец блока сохранения ===

        await update.message.reply_text(f"📄 Распознанный текст:")
        await update.message.reply_text(f"{extracted_text}")

    else:
        await update.message.reply_text("❌ Текст не найден.")

# === Запуск бота ===
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Устанавливаем меню команд
    await app.bot.set_my_commands([
        ('start', 'Запустить бота'),
        ('help', 'Показать помощь'),
        ('ocr', 'Как использовать OCR')
    ])

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ocr", ocr_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("✅ Бот запущен...")
    await app.run_polling()

# === Запуск ===
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())

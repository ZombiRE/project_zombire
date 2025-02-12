#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from dotenv import load_dotenv
from models.database import init_db
from models.photo import Photo

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID'))

# Добавляем словарь для хранения временных данных о фото
temp_photos = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Отправь мне фото для галереи на сайте https://project.zombire.ru!')


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()

        # Сохраняем фото
        file_path = f'static/photos/{photo.file_id}.jpg'
        await file.download_to_drive(file_path)

        # Сохраняем временные данные о фото
        temp_photos[update.effective_user.id] = {
            'file_path': file_path,
            'telegram_user_id': update.effective_user.id
        }

        # Запрашиваем описание фото
        await update.message.reply_text('Пожалуйста, добавьте описание к фотографии (так же можете указать авторство):')
        return 'WAITING_DESCRIPTION'
    except Exception as e:
        logger.error(f"Error in handle_photo: {e}")
        await update.message.reply_text('Произошла ошибка при обработке фото. Пожалуйста, попробуйте еще раз.')
        return ConversationHandler.END


async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        if user_id not in temp_photos:
            await update.message.reply_text('Сначала отправьте фотографию.')
            return ConversationHandler.END

        # Получаем временные данные о фото
        photo_data = temp_photos[user_id]
        description = update.message.text

        # Создаем запись в БД
        db_photo = Photo.create(
            file_path=photo_data['file_path'],
            telegram_user_id=photo_data['telegram_user_id'],
            description=description,
            status='pending'
        )

        # Очищаем временные данные
        del temp_photos[user_id]

        # Отправляем уведомление админу
        keyboard = [
            [
                InlineKeyboardButton('Одобрить', callback_data=f'approve_{db_photo.id}'),
                InlineKeyboardButton('Отклонить', callback_data=f'reject_{db_photo.id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_photo(
            chat_id=ADMIN_USER_ID,
            photo=open(db_photo.file_path, 'rb'),
            caption=f'Новое фото от пользователя {user_id}\nОписание: {description}',
            reply_markup=reply_markup
        )

        await update.message.reply_text('Спасибо! Ваше фото отправлено на модерацию.')
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in handle_description: {e}")
        await update.message.reply_text('Произошла ошибка при сохранении фото. Пожалуйста, попробуйте еще раз.')
        return ConversationHandler.END


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        action, photo_id = query.data.split('_')
        photo = Photo.get_by_id(int(photo_id))

        if action == 'approve':
            photo.approve()
            await query.message.edit_caption('✅ Фото одобрено')
            await context.bot.send_message(
                chat_id=photo.telegram_user_id,
                text='Ваше фото было одобрено и добавлено в галерею на сайте https://project.zombire.ru!'
            )
        elif action == 'reject':
            photo.reject()
            await query.message.edit_caption('❌ Фото отклонено')
            await context.bot.send_message(
                chat_id=photo.telegram_user_id,
                text='К сожалению, ваше фото не было одобрено.'
            )

        await query.answer()
    except Exception as e:
        logger.error(f"Error in handle_callback: {e}")
        await query.answer('Произошла ошибка при обработке запроса.')


# Удаление фото из галереи
async def delete_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Проверяем, что команду вызывает администратор
        if update.effective_user.id != ADMIN_USER_ID:
            await update.message.reply_text('У вас нет прав для этой команды')
            return

        # Проверяем, что передан ID фото
        if not context.args or len(context.args) != 1:
            await update.message.reply_text('Используйте: /delete_photo <id>')
            return

        photo_id = int(context.args[0])
        photo = Photo.get_by_id(photo_id)

        if photo:
            # Удаляем файл
            if os.path.exists(photo.file_path):
                os.remove(photo.file_path)

            # Удаляем из базы данных
            photo.delete()

            await update.message.reply_text(f'Фото с ID {photo_id} удалено')
        else:
            await update.message.reply_text(f'Фото с ID {photo_id} не найдено')

    except ValueError:
        await update.message.reply_text('Неверный формат ID. Используйте целое число.')
    except Exception as e:
        logger.error(f"Error in delete_photo: {e}")
        await update.message.reply_text('Произошла ошибка при удалении фото.')


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, что команду вызывает администратор
    await update.message.reply_text('Неизвестная команда. Введите /help для вызова справки.')


# Подсказка для админа
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, является ли пользователь администратором
    if update.effective_user.id == ADMIN_USER_ID:
        help_text = """
    Доступные команды для администратора:
    
    /start - Начать работу с ботом
    /delete_photo <id> - Удалить фото по его ID
    /help - Показать список доступных команд
    
    Как найти ID фото:
    - Откройте фото в галерее
    - ID будет показан в описании при клике на фото
    """
        await update.message.reply_text(help_text)
    else:
        help_text = """
    🤖 Инструкция по использованию бота Project Zombire 📸
    
    1. Начало работы:
       - Нажмите /start для активации бота
    
    2. Загрузка фото:
       - Отправьте одно фото в чат
       - Важно: качественное и интересное изображение
    
    3. Добавление описания:
       - После отправки фото, напишите его краткое описание
       - Описание поможет модератору понять контекст фото
    
    4. Модерация:
       - Администратор проверит ваше фото
       - При одобрении, фото попадет на сайт https://project.zombire.ru
       - При отклонении, вам придет уведомление
    
    ❓ Остались вопросы?
    Свяжитесь с администратором: admin@zombire.ru
    
    Удачи в создании галереи! 🌟
    """
        await update.message.reply_text(help_text)


def ensure_photos_directory():
    photos_dir = Path('static/photos')
    photos_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Проверка директории для фото: {photos_dir.absolute()}")

def main():
    ensure_photos_directory()
    init_db()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.PHOTO, handle_photo)],
        states={
            'WAITING_DESCRIPTION': [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description)]
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(handle_callback))

    # /start как обычный обработчик
    application.add_handler(CommandHandler("start", start))

    # обработчик для всех неизвестных сообщений
    application.add_handler(MessageHandler(~filters.COMMAND & ~filters.PHOTO, unknown_command))

    # удаление фото из БД
    application.add_handler(CommandHandler("delete_photo", delete_photo))

    # помощь
    application.add_handler(CommandHandler("help", help_command))

    application.run_polling()


if __name__ == '__main__':
    main()

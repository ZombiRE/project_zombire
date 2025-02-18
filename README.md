# Photo gallery & Telegram Bot

## Описание
Telegram бот для загрузки и модерации фотографий через telegram с последующим размещением на сайте.

## Возможности
- Загрузка фотографий через Telegram
- Модерация фото администратором
- Интеграция с веб-галереей

## Установка
1. Клонируйте репозиторий
2. Установите зависимости: `pip install -r requirements.txt`
3. Создайте в корне каталога `.env` файл и внести переменные:
- TELEGRAM_BOT_TOKEN=TOKEN # токен от телеграм бота
- ADMIN_USER_ID=ADMIN_ID # id пользователя телеграм, который будет администратором
4. Запустите Flask `python app.py`, затем бота: `python bot/telegram_bot.py`

## Технологии
- Python
- Telegram Bot API
- SQLAlchemy
- Flask

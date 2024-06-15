import telebot
import requests
import json
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Укажите ваш токен Телеграм-бота
TOKEN = "7474544152:AAFYg5_s8Fyx1Y8HSonGiVwWcpao8yb20ks"

bot = telebot.TeleBot(TOKEN)
scheduler = BackgroundScheduler()
scheduler.start()

# Подсоединение к SQL таблице, в которой хранятся данные.
conn = sqlite3.connect('events.db', check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицы, если их нет
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE
                  )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    event_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                  )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY,
                    event_name TEXT,
                    start_time TEXT,
                    end_time TEXT
                  )''')

conn.commit()

# Функция для команды /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Привет 😎 Я чат-бот НАФИ, я помогаю организовать приятные и интересные встречи.\n\n"
        "Узнать, что я могу сделать, ты можешь по команде /info."
    )

# Функция для команды /info
def info(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Я чат-бот созданный для компании НАФИ, чтобы улучшить взаимодействие спикеров с аудиторией. "
        "Мне можно давать такие задания, как \"Открыть сайт НАФИ\", \"Открыть актуальные исследования\", "
        "\"Узнать подробнее о мероприятии\" и т.д."
    )

# Функция для обработки текстовых сообщений
def text_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()

    if 'открыть сайт нафи' in text:
        update.message.reply_text("Сайт НАФИ: https://www.nafi.ru")
    elif 'открыть актуальные исследования' in text:
        update.message.reply_text("Актуальные исследования: https://www.nafi.ru/researches/")
    elif 'узнать подробнее о мероприятии' in text:
        update.message.reply_text("\nВведите id мероприятия:")
        # Добавляем обработку id мероприятия
        context.user_data['awaiting_event_id'] = True
    elif context.user_data.get('awaiting_event_id'):
        event_id = text
        context.user_data['awaiting_event_id'] = False
        handle_event_id(update, context, event_id)
    else:
        update.message.reply_text("Извините, я не понял вашу команду. Попробуйте команду /info для получения списка доступных команд.")

def handle_event_id(update: Update, context: CallbackContext, event_id: str):
    cursor.execute("SELECT * FROM events WHERE event_id=?", (event_id,))
    event = cursor.fetchone()
    if event:
        event_info = f"Имя мероприятия: {event[1]}\nНачало: {event[2]}\nОкончание: {event[3]}"
        update.message.reply_text(event_info)
        cursor.execute("INSERT INTO subscriptions (user_id, event_id) VALUES (?, ?)", (update.message.from_user.id, event_id))
        conn.commit()
        update.message.reply_text("Вы подписаны на мероприятия!")
    else:
        update.message.reply_text("Мероприятие с таким id не найдено.")

# Обработка команды /start и /help
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    conn.commit()
    bot.reply_to(message, "Привет!!! Я бот НАФИ, моя основная цель - уведомлять пользователей по событиям.")

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Определяем команды
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("info", info))
    
    # Обработка текстовых сообщений
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, text_message))

    # Запускаем бота
    updater.start_polling()

    # Ожидание завершения
    updater.idle()

if __name__ == "__main__":
    main()
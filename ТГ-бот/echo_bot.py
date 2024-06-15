import telebot
import requests
import json
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

bot = telebot.TeleBot("7474544152:AAFYg5_s8Fyx1Y8HSonGiVwWcpao8yb20ks")
scheduler = BackgroundScheduler()
scheduler.start()

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

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    conn.commit()
    bot.reply_to(message, "Привет!!! Я бот НАФИ, моя основная цель это уведомлять пользователей по выбранным мероприятиям.")

@bot.message_handler(commands=['subscribe'])
def subscribe(message):
    event_id = int(message.text.split()[1])
    cursor.execute("INSERT INTO subscriptions (user_id, event_id) VALUES (?, ?)", (message.from_user.id, event_id))
    conn.commit()
    bot.reply_to(message, f"Вы подписались на уведомления по мероприятию {event_id}")

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(message):
    event_id = int(message.text.split()[1])
    cursor.execute("DELETE FROM subscriptions WHERE user_id = ? AND event_id = ?", (message.from_user.id, event_id))
    conn.commit()
    bot.reply_to(message, f"Вы отписались от уведомлений по мероприятию {event_id}")

def check_events():
    current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    cursor.execute("SELECT * FROM events WHERE start_time = ?", (current_time,))
    events = cursor.fetchall()
    for event in events:
        event_id = event[0]
        event_name = event[1]
        cursor.execute("SELECT user_id FROM subscriptions WHERE event_id = ?", (event_id,))
        users = cursor.fetchall()
        for user in users:
            bot.send_message(user[0], f"Напоминание: Мероприятие '{event_name}' начинается сейчас!")

scheduler.add_job(check_events, 'interval', minutes=1)

def fetch_events_from_api():
    # Пример запроса
    response = requests.get('YOUR_PLATFORM_API_ENDPOINT')
    events = json.loads(response.text)
    for event in events:
        cursor.execute("INSERT OR IGNORE INTO events (event_id, event_name, start_time, end_time) VALUES (?, ?, ?, ?)", 
                       (event['id'], event['name'], event['start_time'], event['end_time']))
    conn.commit()

# Можно добавить функцию для периодического обновления информации о событиях
scheduler.add_job(fetch_events_from_api, 'interval', hours=1)

bot.infinity_polling()
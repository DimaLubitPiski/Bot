from telethon.sync import TelegramClient
from telethon.tl.types import Message
from datetime import datetime, timedelta, timezone
from parser.config import CHANNELS, MAX_POST_AGE_DAYS
from dotenv import load_dotenv
import os
import time

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME")

EVENT_KEYWORDS = [
    "концерт", "лекция", "выставка", "мастер-класс", "спектакль",
    "фестиваль", "мероприятие", "показ", "презентация",
    "начало", "вход", "регистрация", "афиша", "состоится", "встреча", "выступление",
    "открытие", "приходите", "приходи", "мероприятия" "приходите","состояться", "праздник", "билет"
]

ADD_KEYWORDS = [
    "реклама"
]

def contains_event(text: str | None) -> bool:
    if not text:
        return False
    
    text_lower = text.lower()
     # Сначала проверяем, нет ли «запрещённых» слов (например, реклама)
    if any(add_keyword in text_lower for add_keyword in ADD_KEYWORDS):
        return False

    # Если запрещённых слов нет, проверяем «ключи» от мероприятий
    return any(keyword in text_lower for keyword in EVENT_KEYWORDS)

# Создаем клиент с именем сессии SESSION_NAME
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

print(f"[INFO] Инициализация клиента Telegram...")
def fetch_recent_posts():
    posts = []
    request_count = 0  # Счётчик запросов
    print(f"[INFO] Начинаем загрузку постов из каналов...")
    # Запускаем клиента - авторизация сохраняется в SESSION_NAME.session
    with client:
        utc_now = datetime.now(timezone.utc)
        for channel in CHANNELS:
            print(f"[INFO] Загружаем сообщения из канала: {channel}")
            try:
                # Получаем entity канала, чтобы избежать ошибок с поиском
                entity = client.get_entity(channel)
                time.sleep(1)  # небольшая пауза между каналами

            except Exception as e:
                print(f"Ошибка при получении канала '{channel}': {e}")
                continue 

            try:
                for message in client.iter_messages(entity, limit=50): # максимум 5 сообщений
                    request_count += 1
                    if not contains_event(message.message):
                        if message.message:
                            print(f"[DEBUG] Пропущено — не содержит признаков мероприятия: {message.message[:30]}...")
                            continue
                        
                        else:
                            print(f"[DEBUG] Пропущено сообщение без текста (None).")
                            
                    if message.date < utc_now - timedelta(days=MAX_POST_AGE_DAYS):
                        print(f"[DEBUG] Сообщение слишком старое, пропускаем.")
                        break

                    print(f"[DEBUG] Получено сообщение от {message.date}: {message.message[:20]}...")
                    posts.append({
                        "channel": channel,
                        "text": message.message,
                        "date": message.date,
                        "message_id": message.id,
                        "channel_username": entity.username or channel.replace("https://t.me/", "").replace("@", "")
                    })

            except Exception as e:
                print(f"[ERROR] Ошибка при чтении: {e}")

    print(f"[INFO] Всего собрано {len(posts)} постов.")
    return posts

if __name__ == "__main__":
    posts = fetch_recent_posts()
    print(f"Загружено {len(posts)} постов")
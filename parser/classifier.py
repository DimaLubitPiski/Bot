import subprocess
import json
import re
from dotenv import load_dotenv
import os

MODEL = os.getenv("OLLAMA_MODEL")

def classify_event(text: str) -> dict:
    prompt = f"""
    Ты — помощник, который извлекает **все события** из текста и возвращает их в виде массива JSON-объектов или **только один JSON-объект**, никаких списков и текста вокруг!.
    Вот текст события:
    {text}
    Верни **только список JSON-объектов**, или **только один JSON-объект**, без пояснений и без лишнего текста, вот такой структуры:
    [ (если **только один JSON** то эти скобки не нужны)
    {{
    "title": "<название> Если нет явного названия, то первые 5 слов поста. ЕСЛИ ДЕЛАЕШЬ СПИСОК, ТО БЕРИ ИЛИ ПРИДУМЫВАЙ НАЗВАНИЕ ИЛИ АДРЕСС И ВРЕМЯ (Розыгрыши, конкурсы и просто описание что будет происходить и кто придет внутри поста не считаются мероприятием, ИГНОРИРУЕМ)",
    "description": "<описание> (бери самое длинное, что подходит в описание. Можно бртаь несколько предложений)", 
    "date": "<Дата в формате ДД-ММ | ЧЧ:ММ если есть или пусто>",
    "address": "<адрес события или пусто> (БЕРИ ТОЛЬКО АДРЕСС, НАПРИМЕР ул. Ленина 5)",
    "price": <цена (ТОЛЬКО ЧИСЛО) или 0>,
    "is_outdoor": true/false,
    "duration_minutes": длительность мероприятия если есть время начала и конца или 120 или 60 (число выбирай случайно)
    }}, (если если **только один JSON** , и что после нее не нужны)
    ...
    ]
    """
    result = subprocess.run(
        ["ollama", "run", MODEL, prompt],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )

    raw = result.stdout.strip() if result.stdout else ""
    if not raw:
        print("[ERROR] stdout пустой или None. stderr:")
        print(result.stderr)
        return []

    # Пробуем найти массив JSON-объектов
    match = re.search(r'\[\s*\{.*\}\s*\]', raw, re.DOTALL)
    if not match:
        print("[ERROR] Не удалось найти JSON-массив в ответе модели.")
        print("Сырой ответ:", raw)
        return []

    json_str = match.group(0)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("[ERROR] Ошибка парсинга JSON:", e)
        print("Сырой JSON:", json_str)
        return []

    
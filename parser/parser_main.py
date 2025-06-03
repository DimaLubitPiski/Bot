from parser.fetcher import fetch_recent_posts
from parser.classifier import classify_event
from parser.geolocation import get_district_from_address
from database.db import SessionLocal
from database.models import Event
from sqlalchemy.exc import IntegrityError
import hashlib

def generate_event_hash(classification):
    data = (
        classification.get("title", "") +
        classification.get("description", "") 
    )
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def parse_and_store():
    posts = fetch_recent_posts()
    total_posts = 0
    total_events = 0
    added = 0
    skipped = 0
    failed = 0

    with SessionLocal() as session:
        for post in posts:
            total_posts += 1
            try:
                events = classify_event(post["text"])  # список событий
                for classification in events:
                    total_events += 1
                    
                    source_url = f"https://t.me/{post['channel_username']}/{post['message_id']}"
                    address = classification.get("address", "")
                    district = get_district_from_address(address) if address else None
                    event = Event(
                        title=classification["title"],
                        description=classification.get("description", ""),
                        date=classification.get("date") or post["date"].date(),
                        location=address,
                        price=classification.get("price"),
                        is_outdoor=classification.get("is_outdoor", False),
                        duration_minutes=classification.get("duration_minutes"),
                        district=district,
                        source_channel=source_url,
                        content_hash=generate_event_hash(classification)
                    )

                    try:
                        session.add(event)
                        session.commit()
                        added += 1
                        print(f"[INFO] Добавлено событие: {event.title}")

                    except IntegrityError:
                        session.rollback()
                        skipped += 1
                        print("[WARN] Повтор события — пропущено.")

                    except Exception as e:
                        session.rollback()
                        failed += 1
                        print(f"[ERROR] Не удалось сохранить событие: {e}")

            except Exception as e:
                failed += 1
                print(f"[ERROR] Не удалось обработать пост: {e}")

    print(f"\n[SUMMARY]")
    print(f"Постов обработано: {total_posts}")
    print(f"Событий найдено: {total_events}")
    print(f"Добавлено: {added}")
    print(f"Пропущено: {skipped}")
    print(f"Ошибок: {failed}")

if __name__ == "__main__":
    parse_and_store()

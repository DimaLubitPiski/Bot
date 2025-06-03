from .db import engine, Base
from .models import Event

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы")

if __name__ == "__main__":
    create_tables()
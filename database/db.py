import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

DB_PATH = os.getenv("DB_PATH", "eventdb.sqlite3")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Создаем движок подключения к базе
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Создаем сессию для работы с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

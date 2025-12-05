# db.py
import os
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

url = URL.create(
    drivername="postgresql+psycopg2",
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_DATABASE"),
)

engine = create_engine(url)
SessionLocal = sessionmaker(bind=engine)

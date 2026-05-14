import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# Esto carga las variables del archivo .env
load_dotenv()

# Lee la URL de forma segura sin mostrar la contraseña en el código
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    pool_pre_ping=True, # <-- ESTA ES LA MAGIA
    pool_recycle=300    # Opcional: Recicla las conexiones cada 5 minutos
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # === URL DE NEON QUE TE DIO TU COMPAÑERA (funciona 100%) ===
    SQLALCHEMY_DATABASE_URI = "postgresql://neondb_owner:npg_5mxh7JjzNHyq@ep-summer-bonus-a4gqupm1-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"
    
    # Si en algún momento te da error de SSL, usa esta versión alternativa:
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql+psycopg2://neondb_owner:npg_5mxh7JjzNHyq@ep-summer-bonus-a4gqupm1-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-2025')
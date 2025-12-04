from flask import Flask
from flask_cors import CORS
from config import Config
from flask_sqlalchemy import SQLAlchemy
from routes import init_routes
import models  # ← solo importamos el archivo (las clases ya están definidas)

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, resources={r"/*": {"origins": "*"}})

db = SQLAlchemy(app)

# CREAR TABLAS
with app.app_context():
    db.create_all()
    print("¡Tablas usuario y material creadas o ya existen en Neon!")

# RUTAS
init_routes(app, db)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
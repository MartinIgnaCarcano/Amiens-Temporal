from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Inicializar SQLAlchemy sin asociar aún con la app
db = SQLAlchemy()

# Cargar las variables de entorno
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Configurar base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar extensiones
    CORS(app)
    db.init_app(app)

    with app.app_context():
        # Importar modelos y rutas DENTRO del contexto para evitar ciclo
        from app import models
        from .routes import productos_bp  # 👈 este blueprint debe definirse en routes.py
        app.register_blueprint(productos_bp)

        # Crear las tablas si no existen
        db.create_all()

    return app

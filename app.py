# app.py - VERSIÓN ÚNICA Y FINAL PARA RENDER
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from geopy.distance import geodesic
import bcrypt
from datetime import datetime

app = Flask(__name__)

# CONFIGURACIÓN DIRECTA (sin config.py)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://neondb_owner:npg_c8hEfZGHtF9u@ep-dark-wind-a43w5ev8-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# CREAR db DIRECTAMENTE
db = SQLAlchemy(app)

# MODELOS DIRECTOS (sin models.py)
class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    saldo = db.Column(db.Float, default=0.0)

class Material(db.Model):
    __tablename__ = 'material'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)

class Solicitud(db.Model):
    __tablename__ = 'solicitudes'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    material = db.Column(db.String(50), nullable=False)
    precio_por_kg = db.Column(db.Float, nullable=False)
    cantidad_kg = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='en_recoleccion')
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()
    print("¡Tablas creadas o ya existen en Neon!")

# PRECIOS DE MATERIALES
PRECIOS_MATERIALES = {
    "pet": 5.50,
    "hdpe": 4.80,
    "aluminio": 25.00,
    "acero": 8.00,
    "carton": 2.50,
    "papel": 3.00,
    "vidrio": 1.80,
    "organico": 1.20
}

@app.route('/api/precios_materiales', methods=['GET'])
def precios_materiales():
    precios = [{"nombre": k, "precio": v} for k, v in PRECIOS_MATERIALES.items()]
    return jsonify(precios), 200

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    nombre = data.get('nombre')
    email = data.get('email')
    password = data.get('password')

    if not all([nombre, email, password]):
        return jsonify({"error": "Faltan datos"}), 400

    if Usuario.query.filter_by(email=email).first():
        return jsonify({"error": "Email ya existe"}), 400

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    nuevo = Usuario(nombre=nombre, email=email, password=hashed.decode('utf-8'), saldo=0.0)
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"mensaje": "Usuario creado con éxito"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Faltan datos"}), 400

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario or not bcrypt.checkpw(password.encode('utf-8'), usuario.password.encode('utf-8')):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    return jsonify({
        "mensaje": "Login exitoso",
        "nombre": usuario.nombre,
        "email": usuario.email
    }), 200

@app.route('/api/material', methods=['POST'])
def add_material():
    data = request.get_json()
    if not data or 'tipo' not in data or 'cantidad' not in data:
        return jsonify({"error": "Faltan datos"}), 400

    nuevo = Material(
        tipo=data['tipo'].lower(),
        cantidad=data['cantidad'],
        lat=data.get('lat'),
        lon=data.get('lon')
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"mensaje": "Material registrado"}), 201

@app.route('/api/materiales_cercanos', methods=['GET'])
def cercanos():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        radio = float(request.args.get('radio', 50))
    except:
        return jsonify({"error": "Parámetros inválidos"}), 400

    materiales = Material.query.all()
    resultado = []
    for m in materiales:
        if m.lat and m.lon:
            dist = geodesic((lat, lon), (m.lat, m.lon)).km
            if dist <= radio:
                resultado.append({
                    "id": m.id,
                    "tipo": m.tipo,
                    "cantidad": m.cantidad,
                    "lat": m.lat,
                    "lon": m.lon,
                    "distancia_km": round(dist, 2)
                })
    resultado.sort(key=lambda x: x['distancia_km'])
    return jsonify(resultado)

@app.route('/api/ranking_semanal', methods=['GET'])
def ranking_semanal():
    # Como no tienes created_at ni usuario_id en Material, hacemos un ranking simple
    # de total CO2 ahorrado en los últimos 7 días (global, no por usuario)

    # Mapeo de CO2 por kg según tipo
    CO2_POR_KG = {
        "pet": 2.15,
        "hdpe": 1.90,
        "papel": 0.95,
        "carton": 0.95,
        "vidrio": 0.30,
        "aluminio": 9.0,
        "acero": 1.8,
        "organico": 0.5,
    }

    materiales = Material.query.all()
    total_co2 = 0.0

    for m in materiales:
        co2_factor = CO2_POR_KG.get(m.tipo.lower(), 1.0)
        total_co2 += m.cantidad * co2_factor

    return jsonify({
        "total_co2_semana": round(total_co2, 2),
        "mensaje": "Ranking global (próximamente por usuario)"
    }), 200

@app.route('/api/solicitudes', methods=['POST'])
def crear_solicitud():
    data = request.get_json()
    email = data.get('email')
    material = data.get('material')
    precio_por_kg = data.get('precio_por_kg')
    cantidad_kg = data.get('cantidad_kg')
    total = data.get('total')

    if not all([email, material, precio_por_kg, cantidad_kg, total]):
        return jsonify({"error": "Faltan datos"}), 400

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    nueva = Solicitud(
        email=email,
        material=material,
        precio_por_kg=precio_por_kg,
        cantidad_kg=cantidad_kg,
        total=total
    )
    db.session.add(nueva)
    db.session.commit()
    return jsonify({"mensaje": "Solicitud creada"}), 201


@app.route('/api/solicitudes', methods=['GET'])
def listar_solicitudes():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Falta email"}), 400

    solicitudes = Solicitud.query.filter_by(email=email).order_by(Solicitud.fecha.desc()).all()
    resultado = [{
        "id": s.id,
        "material": s.material,
        "precio_por_kg": s.precio_por_kg,
        "cantidad_kg": s.cantidad_kg,
        "total": s.total,
        "estado": s.estado,
        "fecha": s.fecha.isoformat()
    } for s in solicitudes]

    return jsonify(resultado), 200

@app.route('/api/saldo', methods=['GET'])
def ver_saldo():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Falta email"}), 400

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    return jsonify({"saldo": usuario.saldo}), 200

@app.route('/api/retirar', methods=['POST'])
def retirar_fondos():
    data = request.get_json()
    email = data.get('email')
    monto = data.get('monto')

    if not email or not monto or monto <= 0:
        return jsonify({"error": "Datos inválidos"}), 400

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    if usuario.saldo < monto:
        return jsonify({"error": "Saldo insuficiente"}), 400

    usuario.saldo -= monto
    db.session.commit()
    return jsonify({"mensaje": "Retiro exitoso", "nuevo_saldo": usuario.saldo}), 200

@app.route('/api/usuario', methods=['DELETE'])
def borrar_cuenta():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"error": "Falta email"}), 400

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    db.session.delete(usuario)
    db.session.commit()
    return jsonify({"mensaje": "Cuenta borrada"}), 200

@app.route("/")
def root():
    return jsonify({"mensaje": "¡ScrapDealer Backend FULL ACTIVADO! 🌱"}), 200



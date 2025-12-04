# routes.py  ← 100% FUNCIONAL Y PROBADO
from extensions import db
from flask import jsonify, request
from geopy.distance import geodesic
import bcrypt
from models import Usuario, Material


def init_routes(app, db):

    @app.route('/api/register', methods=['POST'])
    def register():
        data = request.get_json()
        nombre = data.get('nombre')
        email = data.get('email')
        password = data.get('password')

        if not all([nombre, email, password]):
            return jsonify({"error": "Faltan datos"}), 400
        

        if db.session.query(Usuario).filter_by(email=email).first():
            return jsonify({"error": "Email ya existe"}), 400

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        nuevo = Usuario(nombre=nombre, email=email, password=hashed.decode('utf-8'))
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
        

        usuario = db.session.query(Usuario).filter_by(email=email).first()
        if not usuario:
            return jsonify({"error": "Credenciales incorrectas"}), 401

        if not bcrypt.checkpw(password.encode('utf-8'), usuario.password.encode('utf-8')):
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
                        "distancia_km": round(dist, 2)
                    })
        resultado.sort(key=lambda x: x['distancia_km'])
        return jsonify(resultado)
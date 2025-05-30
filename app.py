from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
app.secret_key = 'clave-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///postbasey.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Disponibilidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    disponibilidad_json = db.Column(db.Text, nullable=False)

# Crear base de datos si no existe
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def formulario():
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    horas = [f'{h:02d}:00' for h in range(8, 21)]  # 08:00 - 20:00

    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        if not nombre or not telefono:
            return "El nombre y el teléfono son obligatorios.", 400

        disponibilidad = {}
        for dia in dias:
            horas_seleccionadas = request.form.getlist(dia)
            if horas_seleccionadas:
                disponibilidad[dia] = horas_seleccionadas

        nueva = Disponibilidad(
            nombre=nombre,
            telefono=telefono,
            disponibilidad_json=json.dumps(disponibilidad)
        )
        db.session.add(nueva)
        db.session.commit()
        return redirect(url_for('gracias'))

    return render_template('formulario.html', dias=dias, horas=horas)

@app.route('/gracias')
def gracias():
    return "¡Gracias por enviar tu disponibilidad!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin123':
            session['logged_in'] = True
            return redirect(url_for('autoescuela'))
        else:
            return "Credenciales incorrectas", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/autoescuela')
def autoescuela():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    registros = Disponibilidad.query.all()
    dias_ordenados = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    horas_por_dia = {dia: [] for dia in dias_ordenados}

    for reg in registros:
        data = json.loads(reg.disponibilidad_json)
        for dia, horas in data.items():
            for hora in horas:
                horas_por_dia[dia].append((hora, reg.nombre, reg.telefono))

    for dia in horas_por_dia:
        horas_por_dia[dia].sort()

    return render_template('autoescuela.html', horas_por_dia=horas_por_dia)

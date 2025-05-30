from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
import json
# Cambio mínimo para forzar commit


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///disponibilidad.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecreto123'
db = SQLAlchemy(app)

usuarios = {
    "admin": "clave123"
}

class Disponibilidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    disponibilidad_json = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def formulario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']

        disponibilidad = {}
        for dia in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]:
            horas = request.form.getlist(dia)
            if horas:
                disponibilidad[dia] = horas

        if not (nombre and telefono and disponibilidad):
            return "Todos los campos son obligatorios", 400

        disponibilidad_json = json.dumps(disponibilidad)
        nueva = Disponibilidad(nombre=nombre, telefono=telefono, disponibilidad_json=disponibilidad_json)
        db.session.add(nueva)
        db.session.commit()
        return redirect('/gracias')

    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    horas = ["09:00", "10:00", "11:00", "12:00", "13:00", "16:00", "17:00", "18:00", "19:00"]
    return render_template('formulario.html', dias=dias, horas=horas)

@app.route('/gracias')
def gracias():
    return "¡Gracias por enviar tu disponibilidad!"

@app.route('/autoescuela')
def vista_autoescuela():
    if 'usuario' not in session:
        return redirect('/login')

    datos = Disponibilidad.query.all()
    registros = []
    for d in datos:
        disponibilidad = json.loads(d.disponibilidad_json)
        registros.append({
            'nombre': d.nombre,
            'telefono': d.telefono,
            'disponibilidad': disponibilidad
        })

    return render_template('vista_autoescuela.html', registros=registros)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']
        if usuario in usuarios and usuarios[usuario] == clave:
            session['usuario'] = usuario
            return redirect('/autoescuela')
        return "Credenciales incorrectas", 401
    return render_template('login.html')

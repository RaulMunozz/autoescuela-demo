from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
app.secret_key = 'clave_super_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///postbasey.db'
db = SQLAlchemy(app)

# Modelo de datos
class Disponibilidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    disponibilidad_json = db.Column(db.Text)

# Crear la base si no existe
with app.app_context():
    db.create_all()

# Página de inicio / formulario
@app.route('/', methods=['GET', 'POST'])
def formulario():
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    horas = [f"{h:02}:00" for h in range(8, 21)]  # 08:00 a 20:00

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono')

        if not nombre or not telefono:
            return "Nombre y teléfono son obligatorios", 400

        disponibilidad = {}
        for dia in dias:
            horas_seleccionadas = request.form.getlist(dia)
            if horas_seleccionadas:
                disponibilidad[dia] = horas_seleccionadas

        nueva_disponibilidad = Disponibilidad(
            nombre=nombre,
            telefono=telefono,
            disponibilidad_json=json.dumps(disponibilidad, ensure_ascii=False)
        )
        db.session.add(nueva_disponibilidad)
        db.session.commit()
        return redirect('/gracias')

    return render_template('formulario.html', dias=dias, horas=horas)

# Página de agradecimiento
@app.route('/gracias')
def gracias():
    return "¡Gracias! Tu disponibilidad ha sido registrada."

# Login simple
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        contraseña = request.form.get('contraseña')
        if usuario == 'admin' and contraseña == 'admin123':
            session['logueado'] = True
            return redirect('/autoescuela')
        return 'Credenciales incorrectas', 401
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# Vista protegida
@app.route('/autoescuela')
def autoescuela():
    if not session.get('logueado'):
        return redirect('/login')

    datos = Disponibilidad.query.all()
    horas_por_dia = {}

    for entrada in datos:
        disponibilidad = json.loads(entrada.disponibilidad_json)
        for dia, horas in disponibilidad.items():
            if dia not in horas_por_dia:
                horas_por_dia[dia] = []
            for hora in horas:
                horas_por_dia[dia].append((hora, entrada.nombre, entrada.telefono))

    # Ordenar por día (Lunes a Viernes) y por hora dentro de cada día
    dias_orden = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    horas_por_dia_ordenado = {
        dia: sorted(horas_por_dia.get(dia, []), key=lambda x: x[0])
        for dia in dias_orden
    }

    return render_template('vista_autoescuela.html', horas_por_dia=horas_por_dia_ordenado)

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nueva_base.db'
db = SQLAlchemy(app)

class Disponibilidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    disponibilidad_json = db.Column(db.Text, nullable=False)

@app.before_first_request
def crear_tablas():
    db.create_all()

dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
horas = [f'{h:02}:00' for h in range(8, 21)]  # De 08:00 a 20:00

@app.route('/', methods=['GET', 'POST'])
def formulario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        disponibilidad = {}

        for dia in dias:
            horas_dia = request.form.getlist(dia)
            if horas_dia:
                disponibilidad[dia] = horas_dia

        nueva = Disponibilidad(
            nombre=nombre,
            telefono=telefono,
            disponibilidad_json=json.dumps(disponibilidad, ensure_ascii=False)
        )
        db.session.add(nueva)
        db.session.commit()
        return redirect('/gracias')

    return render_template('formulario.html', dias=dias, horas=horas)

@app.route('/gracias')
def gracias():
    return "Gracias por enviar tu disponibilidad."

@app.route('/autoescuela')
def vista_autoescuela():
    if not session.get('logueado'):
        return redirect(url_for('login'))

    datos = Disponibilidad.query.all()
    datos_por_dia = {dia: [] for dia in dias}

    for entrada in datos:
        disponibilidad = json.loads(entrada.disponibilidad_json)
        for dia in disponibilidad:
            for hora in disponibilidad[dia]:
                datos_por_dia[dia].append((hora, entrada.nombre, entrada.telefono))

    for dia in datos_por_dia:
        datos_por_dia[dia].sort()

    return render_template('autoescuela.html', datos_por_dia=datos_por_dia)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['usuario'] == 'admin' and request.form['password'] == '1234':
            session['logueado'] = True
            return redirect(url_for('vista_autoescuela'))
        return "Credenciales incorrectas", 401
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)

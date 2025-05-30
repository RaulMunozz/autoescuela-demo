from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///disponibilidad.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecreto123'
db = SQLAlchemy(app)

# Diccionario de usuarios autorizados
usuarios = {
    "admin": "clave123"
}

# Modelo de base de datos
class Disponibilidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    dia = db.Column(db.String(20), nullable=False)
    horas = db.Column(db.String(200), nullable=False)  # varias horas como texto

# Crear la tabla
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def formulario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        dia = request.form['dia']
        horas = request.form.getlist('horas')
        if not (nombre and telefono and dia and horas):
            return "Todos los campos son obligatorios", 400
        horas_str = ', '.join(horas)
        nueva = Disponibilidad(nombre=nombre, telefono=telefono, dia=dia, horas=horas_str)
        db.session.add(nueva)
        db.session.commit()
        return redirect('/gracias')
    return render_template('formulario.html')

@app.route('/gracias')
def gracias():
    return "¡Disponibilidad registrada correctamente! Gracias."

@app.route('/autoescuela')
def vista_autoescuela():
    if 'usuario' not in session:
        return redirect('/login')
    datos = Disponibilidad.query.order_by(Disponibilidad.dia, Disponibilidad.horas).all()
    return render_template('vista_autoescuela.html', disponibilidad=datos)

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

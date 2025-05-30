from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///disponibilidad.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Crear la tabla al arrancar
with app.app_context():
    db.create_all()

# Modelo
class Disponibilidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    dia = db.Column(db.String(20), nullable=False)
    hora = db.Column(db.String(20), nullable=False)

# Crear la tabla
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def formulario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        dia = request.form['dia']
        hora = request.form['hora']
        nueva = Disponibilidad(nombre=nombre, dia=dia, hora=hora)
        db.session.add(nueva)
        db.session.commit()
        return redirect('/gracias')
    return render_template('formulario.html')

@app.route('/gracias')
def gracias():
    return "¡Disponibilidad registrada correctamente! Gracias."

@app.route('/autoescuela')
def vista_autoescuela():
    datos = Disponibilidad.query.order_by(Disponibilidad.dia, Disponibilidad.hora).all()
    return render_template('vista_autoescuela.html', disponibilidad=datos)

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///disponibilidad.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo
class Disponibilidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    dia = db.Column(db.String(20), nullable=False)
    hora = db.Column(db.String(20), nullable=False)

# Crear la tabla
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def formulario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        dia = request.form['dia']
        hora = request.form['hora']
        nueva = Disponibilidad(nombre=nombre, dia=dia, hora=hora)
        db.session.add(nueva)
        db.session.commit()
        return redirect('/gracias')
    return render_template('formulario.html')

@app.route('/gracias')
def gracias():
    return "¡Disponibilidad registrada correctamente! Gracias."

@app.route('/autoescuela')
def vista_autoescuela():
    datos = Disponibilidad.query.order_by(Disponibilidad.dia, Disponibilidad.hora).all()
    return render_template('vista_autoescuela.html', disponibilidad=datos)

if __name__ == '__main__':
    app.run(debug=True)


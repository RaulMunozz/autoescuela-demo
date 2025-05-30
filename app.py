from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

# Crear la app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///disponibilidad.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo para guardar las disponibilidades
class Disponibilidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    dia = db.Column(db.String(20), nullable=False)
    hora = db.Column(db.String(20), nullable=False)

# Crear la tabla si no existe
@app.before_first_request
def crear_tabla():
    db.create_all()

# Ruta principal del formulario
@app.route('/', methods=['GET', 'POST'])
def formulario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        dia = request.form['dia']
        hora = request.form['hora']
        nueva_disponibilidad = Disponibilidad(nombre=nombre, dia=dia, hora=hora)
        db.session.add(nueva_disponibilidad)
        db.session.commit()
        return redirect('/gracias')
    return render_template('formulario.html')

# Página de agradecimiento tras enviar el formulario
@app.route('/gracias')
def gracias():
    return "¡Disponibilidad registrada correctamente! Gracias."

# Vista para la autoescuela
@app.route('/autoescuela')
def vista_autoescuela():
    datos = Disponibilidad.query.order_by(Disponibilidad.dia, Disponibilidad.hora).all()
    return render_template('vista_autoescuela.html', disponibilidad=datos)

# Solo se ejecuta en modo local, no en Render
if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
app.secret_key = 'supersecreto'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///disponibilidad.db'
db = SQLAlchemy(app)

class Disponibilidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    disponibilidad_json = db.Column(db.Text, nullable=False)

@app.route('/', methods=['GET', 'POST'])
def formulario():
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    horas = [f'{h:02}:00' for h in range(8, 21)]  # de 08:00 a 20:00

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono')

        if not nombre or not telefono:
            return "Por favor, completa los campos obligatorios (nombre y teléfono).", 400

        disponibilidad = {}
        for dia in dias:
            horas_dia = request.form.getlist(dia)
            if horas_dia:
                disponibilidad[dia] = horas_dia

        nueva_disponibilidad = Disponibilidad(
            nombre=nombre,
            telefono=telefono,
            disponibilidad_json=json.dumps(disponibilidad)
        )
        db.session.add(nueva_disponibilidad)
        db.session.commit()
        return redirect(url_for('gracias'))

    return render_template('formulario.html', dias=dias, horas=horas)

@app.route('/gracias')
def gracias():
    return "¡Gracias por enviar tu disponibilidad!"

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
app.secret_key = 'clave-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///disponibilidad.db'
db = SQLAlchemy(app)

class Disponibilidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    disponibilidad_json = db.Column(db.Text, nullable=False)

@app.route("/", methods=["GET", "POST"])
def formulario():
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    horas = ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "16:00", "17:00", "18:00", "19:00"]

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()

        if not nombre or not telefono:
            return "Nombre y teléfono son obligatorios", 400

        disponibilidad = {}
        for dia in dias:
            horas_dia = request.form.getlist(f"disponibilidad_{dia}")
            if horas_dia:
                disponibilidad[dia] = horas_dia

        nueva_disponibilidad = Disponibilidad(
            nombre=nombre,
            telefono=telefono,
            disponibilidad_json=json.dumps(disponibilidad)
        )
        db.session.add(nueva_disponibilidad)
        db.session.commit()
        return redirect("/gracias")

    return render_template("formulario.html", dias=dias, horas=horas)

@app.route("/gracias")
def gracias():
    return "<h3>Gracias por enviar tu disponibilidad.</h3>"

if __name__ == '__main__':
    app.run(debug=True)

import json
import os
import secrets
import threading
import time
from collections import defaultdict

from flask import Flask, abort, make_response, redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash

app = Flask(__name__)

# No secret is stored in the repository. In production set SECRET_KEY explicitly;
# the random fallback keeps local development working and invalidates sessions on restart.
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URI", "sqlite:///postbasey.db"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
)
if app.config["SESSION_COOKIE_SECURE"]:
    app.config["SESSION_COOKIE_NAME"] = "__Host-session"

db = SQLAlchemy(app)

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
HORAS_VALIDAS = {f"{h:02}:00" for h in range(8, 21)}

_login_attempts = defaultdict(list)
_attempts_lock = threading.Lock()


class Disponibilidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    disponibilidad_json = db.Column(db.Text)


with app.app_context():
    db.create_all()


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def csrf_protect():
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        sent = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        if not expected or not secrets.compare_digest(sent, expected):
            abort(400, "CSRF token inválido")


@app.after_request
def harden_responses(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; base-uri 'none'; object-src 'none'; "
        "style-src 'self' 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'",
    )
    if os.environ.get("HSTS", "0") == "1":
        resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
    return resp


def login_rate_limited(key, limit=5, window_seconds=300):
    now = time.time()
    with _attempts_lock:
        recent = [t for t in _login_attempts[key] if now - t < window_seconds]
        _login_attempts[key] = recent
        if len(recent) >= limit:
            return True
        recent.append(now)
        return False


@app.route("/", methods=["GET", "POST"])
def formulario():
    horas = [f"{h:02}:00" for h in range(8, 21)]

    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        telefono = (request.form.get("telefono") or "").strip()

        if not nombre or not telefono or len(nombre) > 100 or len(telefono) > 20:
            return "Datos inválidos", 400

        disponibilidad = {}
        for dia in DIAS:
            seleccionadas = [h for h in request.form.getlist(dia) if h in HORAS_VALIDAS]
            if seleccionadas:
                disponibilidad[dia] = seleccionadas

        nueva = Disponibilidad(
            nombre=nombre,
            telefono=telefono,
            disponibilidad_json=json.dumps(disponibilidad, ensure_ascii=False),
        )
        db.session.add(nueva)
        db.session.commit()
        return redirect("/gracias")

    return render_template("formulario.html", dias=DIAS, horas=horas)


@app.route("/gracias")
def gracias():
    return "¡Gracias! Tu disponibilidad ha sido registrada."


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ip = request.remote_addr or "unknown"
        if login_rate_limited(ip):
            return "Demasiados intentos. Inténtalo más tarde.", 429

        if not ADMIN_PASSWORD_HASH:
            app.logger.error("ADMIN_PASSWORD_HASH is not configured")
            return "Login no configurado", 503

        usuario = request.form.get("usuario", "")
        contraseña = request.form.get("contraseña", "")

        if (
            secrets.compare_digest(usuario, ADMIN_USER)
            and check_password_hash(ADMIN_PASSWORD_HASH, contraseña)
        ):
            session.clear()
            session["logueado"] = True
            session["csrf_token"] = secrets.token_urlsafe(32)
            with _attempts_lock:
                _login_attempts.pop(ip, None)
            return redirect("/autoescuela")

        app.logger.warning("Login fallido para usuario=%r desde %s", usuario, ip)
        return "Credenciales incorrectas", 401

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/login")


@app.route("/autoescuela")
def autoescuela():
    if not session.get("logueado"):
        return redirect("/login")

    horas_por_dia = {}
    for entrada in Disponibilidad.query.all():
        try:
            disponibilidad = json.loads(entrada.disponibilidad_json or "{}")
        except (TypeError, ValueError):
            continue
        if not isinstance(disponibilidad, dict):
            continue
        for dia, horas in disponibilidad.items():
            if dia not in DIAS or not isinstance(horas, list):
                continue
            for hora in horas:
                if hora in HORAS_VALIDAS:
                    horas_por_dia.setdefault(dia, []).append(
                        (hora, entrada.nombre, entrada.telefono)
                    )

    horas_ordenadas = {
        dia: sorted(horas_por_dia.get(dia, []), key=lambda x: x[0]) for dia in DIAS
    }

    resp = make_response(
        render_template("vista_autoescuela.html", horas_por_dia=horas_ordenadas)
    )
    resp.headers["Cache-Control"] = "no-store"
    return resp

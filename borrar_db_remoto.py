import os

try:
    os.remove("disponibilidad.db")
    print("✅ Base de datos borrada correctamente en Render.")
except Exception as e:
    print("❌ No se pudo borrar la base de datos:", e)

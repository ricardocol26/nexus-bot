import os
import time
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
from supabase import create_client, Client

app = Flask(__name__)
CORS(app)

# --- CONEXIÓN A SUPABASE ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Cliente de Supabase inicializado.", flush=True)
else:
    supabase = None
    print("⚠️ Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY.", flush=True)

def guardar_en_supabase(venta, recompra):
    if not supabase:
        return
    try:
        data = {
            "timestamp": datetime.now().isoformat(),
            "venta": float(venta),
            "recompra": float(recompra)
        }
        supabase.table("historial_precios").insert(data).execute()
        print("💾 4. ¡Guardado exitoso en Supabase!", flush=True) 
    except Exception as e:
        print(f"❌ 5. Error de Supabase: {e}", flush=True) 

# --- DATOS EN MEMORIA (Respaldo) ---
datos_actuales = {
    "venta": 0.0,
    "recompra": 0.0,
    "timestamp": datetime.now().isoformat()
}
historial_precios = []

# --- RUTAS DE LA API ---
@app.route('/')
def home():
    return "Servidor NexusP2P funcionando con Supabase"

@app.route('/api/datos')
def get_datos():
    # 1. Intentamos leer desde Supabase
    if supabase:
        try:
            # Calcular la fecha exacta de hace 24 horas
            hace_24_horas = (datetime.now() - timedelta(hours=24)).isoformat()

            # Traemos SOLO los datos de las últimas 24h, ordenados cronológicamente
            response = supabase.table("historial_precios") \
                .select("timestamp", "venta", "recompra") \
                .gte("timestamp", hace_24_horas) \
                .order("timestamp", desc=False) \
                .execute()
            
            historial_db = response.data
            
            if historial_db and len(historial_db) > 0:
                # El último registro de la lista es el precio actual (el más reciente)
                actual = historial_db[-1]
                return jsonify({
                    "precios_actuales": actual,
                    "historial": historial_db
                })
        except Exception as e:
            print(f"⚠️ Error leyendo de Supabase: {e}", flush=True)

    # 2. Si Supabase falla o está vacío, usamos la memoria (Respaldo)
    if datos_actuales["venta"] == 0.0 and not historial_precios:
        return jsonify({"error": "El bot aún no ha recibido precios"}), 202
    
    return jsonify({
        "precios_actuales": datos_actuales,
        "historial": historial_precios
    })

@app.route('/api/actualizar', methods=['POST'])
def actualizar():
    global datos_actuales, historial_precios
    data = request.json
    
    if data and 'venta' in data and 'recompra' in data:
        datos_actuales = {
            "venta": float(data['venta']),
            "recompra": float(data['recompra']),
            "timestamp": datetime.now().isoformat()
        }
        historial_precios.append(datos_actuales)
        
        # Guardamos en Supabase
        guardar_en_supabase(datos_actuales["venta"], datos_actuales["recompra"])
        
        if len(historial_precios) > 2000:
            historial_precios.pop(0)
            
        return jsonify({"status": "ok"}), 200
    
    return jsonify({"error": "Datos inválidos"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

import os
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
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

def guardar_en_supabase(venta, recompra, timestamp):
    if not supabase:
        return
    try:
        data = {
            "timestamp": timestamp,
            "venta": float(venta),
            "recompra": float(recompra)
        }
        supabase.table("historial_precios").insert(data).execute()
        print("💾 Guardado exitoso en Supabase", flush=True) 
    except Exception as e:
        print(f"❌ Error de Supabase: {e}", flush=True) 

# --- DATOS EN MEMORIA (Respaldo) ---
datos_actuales = {
    "venta": 0.0,
    "recompra": 0.0,
    "timestamp": datetime.now(timezone.utc).isoformat()
}
historial_precios = []

# --- RUTAS DE LA API ---
@app.route('/')
def home():
    return "Servidor NexusP2P funcionando con Supabase"

@app.route('/api/datos')
def get_datos():
    if supabase:
        try:
            hace_7_dias = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            
            # PAGINACIÓN: Supabase corta en 1000 filas. Hacemos un bucle.
            todos_los_datos = []
            bloque = 1000
            inicio = 0
            
            while True:
                response = supabase.table("historial_precios") \
                    .select("timestamp", "venta", "recompra") \
                    .gte("timestamp", hace_7_dias) \
                    .order("timestamp", desc=False) \
                    .range(inicio, inicio + bloque - 1) \
                    .execute()
                
                datos = response.data
                if not datos:
                    break
                
                todos_los_datos.extend(datos)
                
                if len(datos) < bloque:
                    break
                    
                inicio += bloque

            if todos_los_datos:
                actual = todos_los_datos[-1]
                global datos_actuales
                datos_actuales = actual
                
                return jsonify({
                    "precios_actuales": actual,
                    "historial": todos_los_datos
                })
        except Exception as e:
            print(f"⚠️ Error leyendo de Supabase: {e}", flush=True)

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
        timestamp = data.get('timestamp', datetime.now(timezone.utc).isoformat())
        
        datos_actuales = {
            "venta": float(data['venta']),
            "recompra": float(data['recompra']),
            "timestamp": timestamp
        }
        historial_precios.append(datos_actuales)
        
        guardar_en_supabase(datos_actuales["venta"], datos_actuales["recompra"], timestamp)
        
        if len(historial_precios) > 2000:
            historial_precios.pop(0)
            
        return jsonify({"status": "ok"}), 200
    
    return jsonify({"error": "Datos inválidos"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

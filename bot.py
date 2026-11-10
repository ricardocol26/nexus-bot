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

# Inicializamos el cliente solo si las variables existen
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Cliente de Supabase inicializado.")
else:
    supabase = None
    print("⚠️ Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY.")

def guardar_en_supabase(venta, recompra):
    print("🔍 1. Intentando conectar con Supabase...") 
    if not supabase:
        print("⚠️ 2. El cliente de Supabase es None. Revisa las variables en Render.") 
        return
    try:
        data = {
            "timestamp": datetime.now().isoformat(),
            "venta": float(venta),
            "recompra": float(recompra)
        }
        print(f"📦 3. Enviando datos: Venta={venta}, Recompra={recompra}") 
        supabase.table("historial_precios").insert(data).execute()
        print("💾 4. ¡Guardado exitoso en Supabase!") 
    except Exception as e:
        print(f"❌ 5. Error de Supabase: {e}") 

# --- DATOS EN MEMORIA ---
datos_actuales = {
    "venta": 0.0,
    "recompra": 0.0,
    "timestamp": datetime.now().isoformat()
}
historial_precios = []

# --- CARGAR HISTORIAL DESDE JSON LOCAL ---
def cargar_historial():
    archivo = 'datos_historicos.json'
    if not os.path.exists(archivo):
        print("⚠️ No se encontró datos_historicos.json.")
        return
    
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            
            fecha_base = datetime.now() - timedelta(hours=24)
            total = len(datos)
            
            for i, item in enumerate(datos):
                minutos_por_dato = (24 * 60) / max(total, 1)
                fecha_registro = fecha_base + timedelta(minutes=i * minutos_por_dato)
                
                registro = {
                    "venta": float(item['precio']),
                    "recompra": float(item['precio']) * 0.985,
                    "timestamp": fecha_registro.isoformat()
                }
                historial_precios.append(registro)
            
            print(f"✅ Historial cargado: {len(historial_precios)} registros.")
    except Exception as e:
        print(f"⚠️ Error cargando historial: {e}")

cargar_historial()

# --- RUTAS DE LA API ---
@app.route('/')
def home():
    return "Servidor NexusP2P funcionando con Supabase"

@app.route('/api/datos')
def get_datos():
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
        
        # 🔥 AQUÍ GUARDAMOS EN SUPABASE
        guardar_en_supabase(datos_actuales["venta"], datos_actuales["recompra"])
        
        if len(historial_precios) > 2000:
            historial_precios.pop(0)
            
        return jsonify({"status": "ok"}), 200
    
    return jsonify({"error": "Datos inválidos"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

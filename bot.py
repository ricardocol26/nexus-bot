import os
import time
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app) 

datos_actuales = {
    "venta": 0.0,
    "recompra": 0.0,
    "timestamp": datetime.now().isoformat()
}
historial_precios = []

# --- AÑADIDO: CARGAR HISTORIAL DESDE JSON ---
def cargar_historico():
    if os.path.exists('datos_historicos.json'):
        try:
            with open('datos_historicos.json', 'r', encoding='utf-8') as f:
                datos = json.load(f)
                for item in datos:
                    registro = {
                        "venta": item['precio'],
                        "recompra": item['precio'] * 0.985,
                        "timestamp": datetime.now().isoformat()
                    }
                    historial_precios.append(registro)
                if historial_precios:
                    datos_actuales.update(historial_precios[-1])
                print(f"✅ Historial cargado: {len(historial_precios)} datos.")
        except Exception as e:
            print(f"Error cargando historial: {e}")

cargar_historico()
# --------------------------------------------

@app.route('/')
def home():
    return "Servidor NexusP2P funcionando"

@app.route('/api/datos')
def get_datos():
    if datos_actuales["venta"] == 0.0:
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
        if len(historial_precios) > 2000:
            historial_precios.pop(0)
        return jsonify({"status": "ok"}), 200
    
    return jsonify({"error": "Datos inválidos"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

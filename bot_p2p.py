import os
import time
from flask import Flask, jsonify
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

# ESTE ES EL ENDPOINT QUE USARÁ TU BOT REAL PARA ENVIAR LOS DATOS
@app.route('/api/actualizar', methods=['POST'])
def actualizar():
    global datos_actuales, historial_precios
    from flask import request
    data = request.json
    
    if data and 'venta' in data and 'recompra' in data:
        datos_actuales = {
            "venta": float(data['venta']),
            "recompra": float(data['recompra']),
            "timestamp": datetime.now().isoformat()
        }
        historial_precios.append(datos_actuales)
        if len(historial_precios) > 100:
            historial_precios.pop(0)
        return jsonify({"status": "ok"}), 200
    
    return jsonify({"error": "Datos inválidos"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

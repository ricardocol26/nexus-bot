import os
import threading
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
import time

app = Flask(__name__)
CORS(app) 

datos_actuales = {
    "venta": 0.0,
    "recompra": 0.0,
    "timestamp": datetime.now().isoformat()
}
historial_precios = []

@app.route('/api/datos')
def get_datos():
    if datos_actuales["venta"] == 0.0:
        return jsonify({"error": "El bot aún no ha recibido precios"}), 202
    
    return jsonify({
        "precios_actuales": datos_actuales,
        "historial": historial_precios
    })

if __name__ == '__main__':
    def run_flask():
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    
    threading.Thread(target=run_flask, daemon=True).start()
    print("API Web iniciada y escuchando...")
    
    # Este bucle mantiene vivo el programa
    while True:
        time.sleep(10)

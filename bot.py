import os
import threading
from flask import Flask, jsonify
from flask_cors import CORS
import telebot
from datetime import datetime

# 1. Configuración del servidor web
app = Flask(__name__)
CORS(app) # Permite que tu página web lea los datos

# 2. Memoria del bot (Aquí se guardan los datos)
datos_actuales = {
    "venta": 0.0,
    "recompra": 0.0,
    "timestamp": datetime.now().isoformat()
}
historial_precios = []

# 3. Configuración de tu Bot de Telegram
TOKEN = os.environ.get('TELEGRAM_TOKEN') # Se lee de forma segura desde Render
bot = telebot.TeleBot(TOKEN)

# --- AQUÍ VA TU LÓGICA REAL DE TELEGRAM ---
# Esta función simula lo que hace tu bot. 
# Mañana la cambiaremos por tu código real que saca el precio de Binance.
def actualizar_precio(venta, recompra):
    global datos_actuales, historial_precios
    timestamp = datetime.now().isoformat()
    datos_actuales = {"venta": venta, "recompra": recompra, "timestamp": timestamp}
    
    historial_precios.append(datos_actuales)
    if len(historial_precios) > 100:
        historial_precios.pop(0)

# Comando de prueba para Telegram
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Bot Radar en línea! Esperando datos de Binance...")

# --- ENDPOINTS PARA TU PÁGINA WEB ---
@app.route('/api/datos')
def get_datos():
    if datos_actuales["venta"] == 0.0:
        return jsonify({"error": "El bot aún no ha recibido precios"}), 202
    
    return jsonify({
        "precios_actuales": datos_actuales,
        "historial": historial_precios
    })

# --- ARRANQUE DEL SISTEMA ---
if __name__ == '__main__':
    # Arrancar Flask en un hilo separado
    def run_flask():
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("Bot de Telegram y API Web iniciados...")
    bot.polling()

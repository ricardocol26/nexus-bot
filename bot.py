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

from js import Response, WebSocketPair, JSON
import json
from datetime import datetime

async def on_fetch(request, env):
    # CORS Headers
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    if request.method == "OPTIONS":
        return Response.new("", headers=cors_headers)

    url = request.url
    path = "/" + "/".join(url.split("/")[3:])

    # API: Get History
    if path == "/api/history":
        try:
            # Query from D1
            result = await env.DB.prepare("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 50").all()
            return Response.new(json.dumps(result.results), headers={**cors_headers, "Content-Type": "application/json"})
        except Exception as e:
            return Response.new(json.dumps({"error": str(e)}), status=500, headers=cors_headers)

    # API: Receive Sensor Data
    if path == "/api/sensor-data" and request.method == "POST":
        try:
            data = await request.json()
            # Insert into D1
            await env.DB.prepare(
                "INSERT INTO sensor_data (status, temperature, pressure, speed, gas_concentration, valve_status) VALUES (?, ?, ?, ?, ?, ?)"
            ).bind(
                data.get("status"),
                data.get("temperature"),
                data.get("pressure"),
                data.get("speed"),
                data.get("gas_concentration"),
                data.get("valve_status")
            ).run()
            
            # Broadcast is handled by returning a signal or using Durable Objects
            # For simplicity in basic Workers, we just save to DB. 
            # Real-time updates ideally use Durable Objects for WebSocket broadcasting.
            return Response.new(json.dumps({"status": "success"}), headers=cors_headers)
        except Exception as e:
            return Response.new(json.dumps({"error": str(e)}), status=500, headers=cors_headers)

    # WebSocket: Monitoring
    if path == "/ws/monitoring":
        upgrade_header = request.headers.get("Upgrade")
        if upgrade_header != "websocket":
            return Response.new("Expected Upgrade: websocket", status=426)

        pair = WebSocketPair.new()
        client = pair.get(0)
        server = pair.get(1)

        await server.accept()
        
        # Note: Worker-to-Worker/Client broadcast usually requires Durable Objects.
        # This basic socket will stay open but won't receive broadcasts unless 
        # implemented with DO or a Pub/Sub mechanism.
        
        return Response.new(None, status=101, web_socket=client)

    return Response.new("Not Found", status=404, headers=cors_headers)

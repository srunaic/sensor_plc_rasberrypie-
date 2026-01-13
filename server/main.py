from js import Response, JSON, WebSocketPair, headers_from_dict
import json

# Cloudflare Workers Python Backend
async def on_fetch(request, env):
    url = request.url
    method = request.method
    
    # CORS Headers
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    if method == "OPTIONS":
        return Response.new("", headers=headers_from_dict(cors_headers))

    # --- API: GET History ---
    if "/api/history" in url:
        try:
            # D1 Query
            results = await env.DB.prepare(
                "SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 50"
            ).all()
            return Response.json(results.results, headers=headers_from_dict(cors_headers))
        except Exception as e:
            return Response.new(str(e), status=500)

    # --- API: POST Sensor Data ---
    if "/api/sensor-data" in url and method == "POST":
        try:
            body = await request.json()
            # Insert into D1
            await env.DB.prepare(
                "INSERT INTO sensor_data (status, temperature, pressure, speed, gas_concentration, valve_status) VALUES (?, ?, ?, ?, ?, ?)"
            ).bind(
                body.get("status"), 
                body.get("temperature"), 
                body.get("pressure"), 
                body.get("speed"),
                body.get("gas_concentration"),
                body.get("valve_status")
            ).run()
            
            # Note: Broad-casting to WebSockets would require Durable Objects or a pub/sub mechanism
            # For a simple Worker, we just return success.
            return Response.json({"status": "success"}, headers=headers_from_dict(cors_headers))
        except Exception as e:
            return Response.new(str(e), status=500)

    # --- WebSocket: Monitoring ---
    if "/ws/monitoring" in url:
        upgrade_header = request.headers.get("Upgrade")
        if upgrade_header != "websocket":
            return Response.new("Expected Upgrade: websocket", status=426)

        # Create WebSocket pair
        client, server = WebSocketPair.new()
        server.accept()
        
        # Simple echo/keep-alive for now (Full broadcast needs Durable Objects)
        return Response.new(None, status=101, web_socket=client)

    return Response.new("Not Found", status=404)

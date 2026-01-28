from js import Response, WebSocketPair, JSON
import json

async def on_fetch(request, env):
    # Standard CORS Headers
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    # Handle Preflight (OPTIONS)
    if request.method == "OPTIONS":
        return Response.new("", headers=cors_headers)

    url = request.url
    try:
        path = "/" + "/".join(url.split("/")[3:])
        path = path.split("?")[0]
    except:
        path = "/"

    try:
        # 1. Health Check
        if path == "/api/ping":
            return Response.new(json.dumps({"status": "ok"}), headers={**cors_headers, "Content-Type": "application/json"})

        # 2. Get History
        if path == "/api/history":
            try:
                query = await env.DB.prepare("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 50").all()
                # Ensure results is treated as a list
                results = list(query.results) if query.results else []
                return Response.new(json.dumps(results), headers={**cors_headers, "Content-Type": "application/json"})
            except Exception as e:
                return Response.new(json.dumps({"error": str(e)}), status=500, headers={**cors_headers, "Content-Type": "application/json"})

        # 3. Receive Sensor Data
        if path == "/api/sensor-data" and request.method == "POST":
            try:
                data = await request.json()
                await env.DB.prepare(
                    "INSERT INTO sensor_data (status, temperature, pressure, speed, gas_concentration, valve_status) VALUES (?, ?, ?, ?, ?, ?)"
                ).bind(
                    data.get("status", 0),
                    data.get("temperature", 0),
                    data.get("pressure", 0),
                    data.get("speed", 0),
                    data.get("gas_concentration", 0),
                    data.get("valve_status", 1)
                ).run()
                return Response.new(json.dumps({"status": "success"}), headers={**cors_headers, "Content-Type": "application/json"})
            except Exception as e:
                return Response.new(json.dumps({"error": str(e)}), status=500, headers={**cors_headers, "Content-Type": "application/json"})

        # 4. WebSocket: Monitoring
        if path == "/ws/monitoring":
            if request.headers.get("Upgrade") != "websocket":
                return Response.new("Expected Upgrade: websocket", status=426, headers=cors_headers)

            # In Python Workers, WebSocketPair.new() returns an object with .get(0) and .get(1)
            pair = WebSocketPair.new()
            client = pair.get(0)
            server = pair.get(1)

            await server.accept()
            # The connection is accepted. In a simple worker, it just stays alive.
            return Response.new(None, status=101, web_socket=client)

        return Response.new("Not Found", status=404, headers=cors_headers)

    except Exception as global_e:
        return Response.new(json.dumps({"error": str(global_e)}), status=500, headers={**cors_headers, "Content-Type": "application/json"})

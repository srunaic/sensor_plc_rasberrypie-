from js import Response, WebSocketPair
import json

async def on_fetch(request, env, ctx):
    # Base CORS headers for all responses
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    if request.method == "OPTIONS":
        return Response.new("", headers=cors_headers)

    try:
        url = request.url
        # Strip domain and extract path safely
        path_full = "/" + "/".join(url.split("/")[3:])
        path = path_full.split("?")[0] # remove query strings

        # 1. Health Check
        if path == "/" or path == "/api/ping":
            return Response.new(
                json.dumps({"status": "running", "msg": "Sensor PLC Backend is active"}), 
                status=200, 
                headers={**cors_headers, "Content-Type": "application/json"}
            )

        # 2. History (Database Read)
        if path == "/api/history":
            try:
                # result = await env.DB.prepare(...).all()
                # In Python Worker, results is an object that mirrors JS result.
                query = await env.DB.prepare("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 50").all()
                
                # Careful conversion of results to Python list
                results_list = []
                if query and hasattr(query, 'results'):
                    for i in range(len(query.results)):
                        results_list.append(query.results[i])
                
                return Response.new(
                    json.dumps(results_list), 
                    headers={**cors_headers, "Content-Type": "application/json"}
                )
            except Exception as e:
                return Response.new(
                    json.dumps({"error": f"D1 Error: {str(e)}"}), 
                    status=500, 
                    headers=cors_headers
                )

        # 3. Receive Sensor Data (Database Write)
        if path == "/api/sensor-data" and request.method == "POST":
            try:
                data = await request.json()
                await env.DB.prepare(
                    "INSERT INTO sensor_data (status, temperature, pressure, speed, gas_concentration, valve_status) VALUES (?, ?, ?, ?, ?, ?)"
                ).bind(
                    data.get("status", 0),
                    data.get("temperature", 0.0),
                    data.get("pressure", 0.0),
                    data.get("speed", 0),
                    data.get("gas_concentration", 0.0),
                    data.get("valve_status", 1)
                ).run()
                return Response.new(json.dumps({"status": "success"}), headers=cors_headers)
            except Exception as e:
                return Response.new(json.dumps({"error": str(e)}), status=500, headers=cors_headers)

        # 4. WebSocket: Monitoring
        if path == "/ws/monitoring":
            if request.headers.get("Upgrade") != "websocket":
                return Response.new("Expected Upgrade: websocket", status=426, headers=cors_headers)

            pair = WebSocketPair.new()
            # Standard access for Python binding
            client = pair.get(0)
            server = pair.get(1)

            await server.accept()
            # Connection accepted. Note: Python Workers keep sockets open but 
            # cloud-wide broadcast requires Durable Objects.
            return Response.new(None, status=101, web_socket=client)

        return Response.new(json.dumps({"error": "not found", "path": path}), status=404, headers=cors_headers)

    except Exception as e:
        # Ultimate fallback to avoid 1101
        return Response.new(
            json.dumps({"error": "Worker crashed", "details": str(e)}), 
            status=500, 
            headers={**cors_headers, "Content-Type": "application/json"}
        )

from js import Response, WebSocketPair
import json

async def on_fetch(request, env):
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
        # Safer path parsing
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        path = parsed_url.path
        if not path:
            path = "/"

        # 1. Root / Health Check
        if path == "/" or path == "/api/ping":
            return Response.new(
                json.dumps({"message": "Sensor PLC Backend is running", "path": path}), 
                status=200, 
                headers={**cors_headers, "Content-Type": "application/json"}
            )

        # 2. History
        if path == "/api/history" or path == "/history":
            try:
                if not hasattr(env, "DB"):
                    return Response.new(json.dumps({"error": "D1 DB binding 'DB' not found"}), status=500, headers=cors_headers)
                
                query = await env.DB.prepare("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 50").all()
                
                # Convert results to a serializable list
                data_list = []
                if hasattr(query, "results") and query.results:
                    # In some versions, results might need to be converted from JS to Python
                    # But usually it's already a list of dicts.
                    for row in query.results:
                        data_list.append(dict(row))
                
                return Response.new(
                    json.dumps(data_list), 
                    headers={**cors_headers, "Content-Type": "application/json"}
                )
            except Exception as e:
                return Response.new(
                    json.dumps({"error": f"D1 Query Failed: {str(e)}"}), 
                    status=500, 
                    headers={**cors_headers, "Content-Type": "application/json"}
                )

        # 3. Receive Sensor Data
        if (path == "/api/sensor-data" or path == "/sensor-data") and request.method == "POST":
            try:
                body = await request.text()
                data = json.loads(body)
                
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

        # 4. WebSocket
        if path == "/ws/monitoring":
            if request.headers.get("Upgrade") != "websocket":
                return Response.new("Expected Upgrade: websocket", status=426, headers=cors_headers)

            pair = WebSocketPair.new()
            # Most reliable way to access pair in Python Workers
            try:
                client = pair[0]
                server = pair[1]
            except:
                client = pair.get(0)
                server = pair.get(1)

            await server.accept()
            return Response.new(None, status=101, web_socket=client)

        return Response.new(json.dumps({"error": "Not Found", "path": path}), status=404, headers=cors_headers)

    except Exception as e:
        # Ultimate safety net to prevent 1101
        return Response.new(
            json.dumps({"error": "Worker Exception", "details": str(e)}), 
            status=500, 
            headers={**cors_headers, "Content-Type": "application/json"}
        )

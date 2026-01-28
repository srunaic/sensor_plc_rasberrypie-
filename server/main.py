from js import Response, WebSocketPair, fetch, JSON, Object
import json

async def on_fetch(request, env, ctx):
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    if request.method == "OPTIONS":
        return Response.new("", headers=cors_headers)

    # Supabase Credentials from env
    supabase_url = env.SUPABASE_URL
    supabase_key = getattr(env, "SUPABASE_KEY", "REPLACE_WITH_YOUR_ANON_KEY")

    supabase_headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    try:
        url = request.url
        path_segments = url.split("/")
        path = "/" + "/".join(path_segments[3:]) if len(path_segments) > 3 else "/"
        path = path.split("?")[0]

        # 1. Health Check
        if path == "/" or path == "/api/ping":
            return Response.new(
                json.dumps({"status": "running", "msg": "Sensor PLC Backend (Supabase) is active"}), 
                status=200, 
                headers={**cors_headers, "Content-Type": "application/json"}
            )

        # 2. History (Read from Supabase)
        if path == "/api/history":
            try:
                # Query Supabase REST API
                # GET /rest/v1/sensor_data?select=*&order=timestamp.desc&limit=50
                api_url = f"{supabase_url}/rest/v1/sensor_data?select=*&order=timestamp.desc&limit=50"
                
                resp = await fetch(api_url, method="GET", headers=supabase_headers)
                data = await resp.json()
                
                return Response.new(
                    JSON.stringify(data), 
                    headers={**cors_headers, "Content-Type": "application/json"}
                )
            except Exception as e:
                return Response.new(
                    json.dumps({"error": f"Supabase Fetch Error: {str(e)}"}), 
                    status=500, 
                    headers=cors_headers
                )

        # 3. Receive Sensor Data (Write to Supabase)
        if path == "/api/sensor-data" and request.method == "POST":
            try:
                data = await request.json()
                # POST /rest/v1/sensor_data
                api_url = f"{supabase_url}/rest/v1/sensor_data"
                
                payload = json.dumps({
                    "status": data.get("status", 0),
                    "temperature": data.get("temperature", 0.0),
                    "pressure": data.get("pressure", 0.0),
                    "speed": data.get("speed", 0),
                    "gas_concentration": data.get("gas_concentration", 0.0),
                    "valve_status": data.get("valve_status", 1)
                })

                resp = await fetch(api_url, method="POST", headers=supabase_headers, body=payload)
                
                if resp.status >= 400:
                    err_text = await resp.text()
                    return Response.new(json.dumps({"error": f"Supabase Insert Failed: {err_text}"}), status=500, headers=cors_headers)

                return Response.new(json.dumps({"status": "success"}), headers=cors_headers)
            except Exception as e:
                return Response.new(json.dumps({"error": f"Internal Error: {str(e)}"}), status=500, headers=cors_headers)

        # 4. WebSocket: Monitoring Proxy
        if path == "/ws/monitoring":
            if request.headers.get("Upgrade") != "websocket":
                return Response.new("Expected Upgrade: websocket", status=426, headers=cors_headers)

            pair = WebSocketPair.new()
            client = pair.get(0)
            server = pair.get(1)

            await server.accept()
            # Note: Real-time broadcast still ideally needs Durable Objects or Supabase Realtime
            # For now, this just maintains the connection status for the UI.
            return Response.new(None, status=101, web_socket=client)

        return Response.new(json.dumps({"error": "not found", "path": path}), status=404, headers=cors_headers)

    except Exception as e:
        return Response.new(
            json.dumps({"error": "Worker Exception", "details": str(e)}), 
            status=500, 
            headers={**cors_headers, "Content-Type": "application/json"}
        )

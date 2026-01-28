from js import Response, fetch
import json

async def on_fetch(request, env, ctx):
    # Standard CORS headers
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    if request.method == "OPTIONS":
        return Response.new("", headers=cors_headers)

    try:
        url_str = request.url
        # Simplest path parsing: split by '/' and take parts after the domain
        path = "/" + "/".join(url_str.split("/")[3:]).split("?")[0]
        
        # 1. Ping / Root
        if path == "/" or path == "/api/ping":
            return Response.new(
                json.dumps({"status": "ok", "message": "Sensor PLC Supabase REST active"}), 
                status=200, 
                headers={**cors_headers, "Content-Type": "application/json"}
            )

        # Supabase Config from Env
        supabase_url = str(env.SUPABASE_URL)
        supabase_key = str(env.SUPABASE_KEY)
        auth_headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }

        # 2. Get History
        if path == "/api/history":
            target = f"{supabase_url}/rest/v1/sensor_data?select=*&order=timestamp.desc&limit=50"
            resp = await fetch(target, method="GET", headers=auth_headers)
            body = await resp.text()
            return Response.new(
                body, 
                status=resp.status, 
                headers={**cors_headers, "Content-Type": "application/json"}
            )

        # 3. Post Sensor Data
        if path == "/api/sensor-data" and request.method == "POST":
            payload = await request.text()
            target = f"{supabase_url}/rest/v1/sensor_data"
            write_headers = {**auth_headers, "Prefer": "return=minimal"}
            resp = await fetch(target, method="POST", headers=write_headers, body=payload)
            
            if resp.status >= 400:
                err_text = await resp.text()
                return Response.new(json.dumps({"error": "Supabase Error", "details": err_text}), status=500, headers=cors_headers)
                
            return Response.new(json.dumps({"status": "success"}), status=200, headers=cors_headers)

        return Response.new("Endpoint Not Found", status=404, headers=cors_headers)

    except Exception as e:
        # Ultimate catch block to reveal issues
        return Response.new(
            json.dumps({"error": "Worker Internal Error", "details": str(e)}), 
            status=500, 
            headers={**cors_headers, "Content-Type": "application/json"}
        )

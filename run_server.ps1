# Gas Safety Monitoring System - Unified Startup Script

Write-Host "--- Gas Safety PLC Unified Server Starting ---" -ForegroundColor Cyan

# 1. Kill any existing processes (optional, but clean)
Stop-Process -Name "python" -ErrorAction SilentlyContinue

Write-Host "1. Building Frontend Assets..." -ForegroundColor Yellow
cd client
npm run build
cd ..

Write-Host "2. Starting Unified Backend (Serving UI + API)..." -ForegroundColor Yellow
Start-Process python -ArgumentList "server/main.py" -NoNewWindow
# Note: For production use: python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
# But for now, we assume direct execution or uvicorn in background.

Write-Host "3. Starting PLC Simulator..." -ForegroundColor Yellow
Start-Process python -ArgumentList "sim/plc_simulator.py" -NoNewWindow

Write-Host "4. Starting Edge Collector (Raspberry Pi Simulation)..." -ForegroundColor Yellow
Start-Process python -ArgumentList "edge/collector.py" -NoNewWindow

Write-Host "-------------------------------------------"
Write-Host "All components are running." -ForegroundColor Green
Write-Host "Open Dashboard: http://localhost:8000" -ForegroundColor Green
Write-Host "-------------------------------------------"

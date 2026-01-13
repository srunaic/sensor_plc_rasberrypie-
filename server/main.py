from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import sqlite3
import time

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. In production, specify ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
def init_db():
    conn = sqlite3.connect('sensor_history.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status INTEGER,
            temperature REAL,
            pressure REAL,
            speed INTEGER,
            gas_concentration REAL,
            valve_status INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Data Model
class SensorData(BaseModel):
    status: int
    temperature: float
    pressure: float
    speed: int
    gas_concentration: float
    valve_status: int

from typing import List

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.post("/api/sensor-data")
async def receive_sensor_data(data: SensorData):
    # Log to DB
    conn = sqlite3.connect('sensor_history.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sensor_data (status, temperature, pressure, speed, gas_concentration, valve_status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data.status, data.temperature, data.pressure, data.speed, data.gas_concentration, data.valve_status))
    conn.commit()
    conn.close()
    
    # Broadcast to Web UI
    await manager.broadcast(data.json())
    return {"status": "success"}

@app.get("/api/history")
async def get_history(limit: int = 50):
    conn = sqlite3.connect('sensor_history.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.websocket("/ws/monitoring")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

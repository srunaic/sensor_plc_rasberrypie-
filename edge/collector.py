import time
import requests
import json
from pyModbusTCP.client import ModbusClient

class EdgeCollector:
    def __init__(self, plc_host='127.0.0.1', plc_port=502):
        self.client = ModbusClient(host=plc_host, port=plc_port, auto_open=True, auto_close=True)
        # Supabase Configuration
        self.supabase_url = 'https://wjqtxvtlqswwxqdciuwm.supabase.co'
        self.supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndqcXR4dnRscXN3d3hxZGNpdXdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk1NzUxOTksImV4cCI6MjA4NTE1MTE5OX0.wjn1aDedu1CCxZWKg8lpxclrvPqGFWIPmc5hDIZuO6g'
        self.api_url = f"{self.supabase_url}/rest/v1/sensor_data"
        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        self.last_status = None

    def read_plc_data(self):
        # 1. Read Basic Status (Discrete Inputs)
        # 0: Stopped, 1: Running, 2: Fault
        regs = self.client.read_holding_registers(0, 10)
        if not regs:
            return None

        # Data mapping:
        # Register 0: System Status
        # Register 1: Temperature (Value * 0.01)
        # Register 2: Pressure (Value * 0.01)
        # Register 3: Speed
        # Register 4: Gas Concentration (PPM)
        # Register 5: Valve Status (0: Closed, 1: Open, 2: Interlock)
        
        data = {
            "status": regs[0],
            "temperature": regs[1] / 100.0,
            "pressure": regs[2] / 100.0,
            "speed": regs[3],
            "gas_concentration": regs[4] / 1.0, # PPM
            "valve_status": regs[5]
        }
        return data

    def send_to_cloud(self, data):
        try:
            response = requests.post(self.api_url, headers=self.headers, json=data, timeout=5)
            if response.status_code >= 400:
                print(f"Cloud upload failed: {response.text}")
            else:
                print(f"Data pushed to Supabase: Gas {data['gas_concentration']} PPM, Valve {data['valve_status']}")
        except Exception as e:
            print(f"Error connecting to Supabase: {e}")

    def check_sharing_status(self):
        try:
            # GET /rest/v1/system_settings?key=eq.data_sharing_enabled&select=value
            url = f"{self.supabase_url}/rest/v1/system_settings?key=eq.data_sharing_enabled&select=value"
            resp = requests.get(url, headers=self.headers, timeout=3)
            if resp.status_code == 200:
                settings = resp.json()
                if settings and len(settings) > 0:
                    return settings[0]['value'] == 'true'
            return True # Default to True if setting missing
        except:
            return True

    def run(self):
        print(f"Edge Collector started. Connecting to Supabase...")
        while True:
            # Check if sharing is enabled before reading/sending
            if self.check_sharing_status():
                data = self.read_plc_data()
                if data:
                    self.send_to_cloud(data)
            else:
                print("Data sharing is DISABLED by Dashboard. Waiting...")
            time.sleep(2)

if __name__ == "__main__":
    collector = EdgeCollector()
    collector.run()

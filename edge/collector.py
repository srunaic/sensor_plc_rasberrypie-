import time
import requests
from pyModbusTCP.client import ModbusClient

class EdgeCollector:
    def __init__(self, plc_host='127.0.0.1', plc_port=502, api_url='http://127.0.0.1:8000/api/sensor-data'):
        self.client = ModbusClient(host=plc_host, port=plc_port, auto_open=True, auto_close=True)
        self.api_url = api_url
        self.last_status = None

    def collect_and_push(self):
        print(f"Connecting to PLC at {self.client.host}...")
        try:
            while True:
                # Read 6 registers starting from address 0
                regs = self.client.read_holding_registers(0, 6)
                if regs:
                    status, temp_raw, press_raw, speed, gas_raw, valve = regs
                    
                    data = {
                        "status": status,
                        "temperature": temp_raw / 100.0,
                        "pressure": press_raw / 100.0,
                        "speed": speed,
                        "gas_concentration": gas_raw / 100.0,
                        "valve_status": valve,
                        "timestamp": time.time()
                    }
                    
                    print(f"Collected: {data}")
                    
                    # Push to Backend API
                    try:
                        response = requests.post(self.api_url, json=data, timeout=2)
                        print(f"Push Status: {response.status_code}")
                    except Exception as e:
                        print(f"API Push Error: {e}")
                else:
                    print("PLC Read Error")
                
                time.sleep(2)  # 2-second interval
        except KeyboardInterrupt:
            print("Edge Collector Stopped")

if __name__ == "__main__":
    collector = EdgeCollector()
    collector.collect_and_push()

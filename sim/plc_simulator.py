from pyModbusTCP.server import ModbusServer, DataBank
import time
import random

# Initializing simulated PLC registers
# Holding Registers (Offset 0):
# 0: Machine Status (0: STOP, 1: RUN, 2: FAULT)
# 1: Temperature (Scaled x100)
# 2: Pressure (Scaled x100)
# 3: Motor Speed (RPM)
# 4: Gas Concentration (PPM)
# 5: Valve Status (0: CLOSED, 1: OPEN, 2: INTERLOCK_CLOSED)

class PLCSimulator:
    def __init__(self, host='127.0.0.1', port=502):
        self.server = ModbusServer(host=host, port=port, no_block=True)
        self.status = 1  # Start as RUN
        self.valve_status = 1 # OPEN
        self.gas_threshold = 40.0 # Threshold for interlock
        
    def start(self):
        print(f"Starting Gas Safety PLC on {self.server.host}:{self.server.port}...")
        low_gas_count = 0
        try:
            self.server.start()
            while True:
                # Update simulated data
                temp = int((25.0 + random.uniform(-1.0, 1.0)) * 100)
                press = int((5.0 + random.uniform(-0.5, 0.5)) * 100)
                speed = 1500 + random.randint(-50, 50)
                
                # Gas Simulation: Much more stable for "Factory Reality"
                # 99% chance of being normal
                gas_ppm = 5.0 + random.uniform(-0.2, 0.2)
                
                # Rare leak event (1% per poll)
                if random.random() < 0.01: 
                    gas_ppm = random.uniform(35.0, 55.0)
                    print("!!! SIMULATED GAS LEAK DETECTED !!!")
                
                # Interlock Logic
                if gas_ppm > self.gas_threshold:
                    self.valve_status = 2 # INTERLOCK_CLOSED
                    self.status = 2 # System FAULT due to gas
                    low_gas_count = 0
                elif self.valve_status == 2 and gas_ppm < 10.0:
                    # In a real factory, a worker would reset this.
                    # For simulation, we'll auto-reset after 15 seconds of low gas
                    # to show the "Normal" state again.
                    low_gas_count += 1
                    if low_gas_count > 15:
                        print("--- SAFETY RESET: System returning to NORMAL ---")
                        self.valve_status = 1 # OPEN
                        self.status = 1 # RUN
                        low_gas_count = 0
                else:
                    low_gas_count = 0

                # Update Data Bank
                self.server.data_bank.set_holding_registers(0, [
                    self.status, 
                    temp, 
                    press, 
                    speed, 
                    int(gas_ppm * 100),
                    self.valve_status
                ])
                
                print(f"PLC Update - Status: {self.status}, Gas: {gas_ppm:.2f} PPM, Valve: {self.valve_status}, Reset Timer: {low_gas_count}/15")
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping PLC...")
            self.server.stop()

if __name__ == "__main__":
    sim = PLCSimulator()
    sim.start()

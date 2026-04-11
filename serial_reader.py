import time
import serial
from fastapi import APIRouter
import re
import threading

router = APIRouter()

# Global variables
ser = None
last_weight = 0
lock = threading.Lock()


def get_serial():
    global ser
    if ser is None:
        try:
            print("Opening serial port COM5 at 115200 baud...")
            ser = serial.Serial('COM5', 115200, timeout=0.1)
            time.sleep(2)
            ser.reset_input_buffer()
            print("✅ Serial connected!")
        except Exception as e:
            print(f"❌ Serial error: {e}")
    return ser


def read_fresh_weight():
    """Read fresh weight from serial - returns RAW weight without calibration"""
    global last_weight
    try:
        ser = get_serial()
        if ser and ser.is_open:
            # Read multiple lines to get latest
            for _ in range(3):
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"Raw line: {line}")
                    # Extract number from line (this is the RAW weight)
                    match = re.search(r'(\d+\.?\d*)', line)
                    if match:
                        raw_weight = float(match.group(1))
                        if 0 < raw_weight < 5000:  # Sanity check
                            with lock:
                                last_weight = raw_weight
                            print(f"✅ RAW Weight: {raw_weight}g")
                            return raw_weight
                time.sleep(0.05)
    except Exception as e:
        print(f"Read error: {e}")

    with lock:
        return last_weight


class WeightReader:
    def __init__(self):
        self.current_weight = 0

    def read_single_weight(self):
        return read_fresh_weight()

    def get_stable_weight_fast(self, timeout=0.5):
        readings = []
        start = time.time()
        while time.time() - start < timeout:
            weight = read_fresh_weight()
            if weight > 0:
                readings.append(weight)
            time.sleep(0.1)

        if readings:
            return sum(readings) / len(readings)
        return None


# Create instance for import
weight_reader = WeightReader()


# REST endpoints
@router.get("/weight")
def get_weight():
    """Get current RAW weight (no calibration)"""
    weight = read_fresh_weight()
    return {"weight": weight}


@router.get("/weight/stable")
def get_stable_weight():
    """Get stable RAW weight"""
    weight = weight_reader.get_stable_weight_fast(0.5)
    if weight:
        return {"weight": weight}
    return {"weight": 0}
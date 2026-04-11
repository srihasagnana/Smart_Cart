import time
import serial
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from threading import Lock
import asyncio
import re
from collections import deque

router = APIRouter()

# Serial connection setup
serial_lock = Lock()
last_weight = 0
last_read_time = 0
ser = None
active_connections = []


def get_serial():
    global ser
    if ser is None:
        try:
            ser = serial.Serial('COM5', 115200, timeout=0.1)
            time.sleep(2)
            ser.reset_input_buffer()
            ser.flush()
            print("✅ Serial connected at 115200 baud")
        except Exception as e:
            print(f"❌ Serial error: {e}")
    return ser


class FastWeightReader:
    def __init__(self):
        self.current_weight = 0
        self.last_stable_weight = 0
        self.weight_history = deque(maxlen=10)  # Store last 10 readings
        self.calibration_factor = 4.5183  # From your calibration
        self.tare_offset = -0.15  # From your tare reading
        self.debug_count = 0

    def apply_calibration(self, raw_value):
        """Convert raw sensor value to actual grams"""
        # Apply calibration factor
        actual = raw_value * self.calibration_factor

        # Apply tare offset
        actual = actual - (self.tare_offset * self.calibration_factor)

        return max(0, actual)  # Don't return negative weights

    def read_single_weight(self):
        """Read single weight with filtering"""
        try:
            ser = get_serial()
            if ser and ser.is_open:
                # Read multiple lines to get the latest
                latest_weight = None
                read_attempts = 0

                while ser.in_waiting and read_attempts < 5:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    read_attempts += 1

                    if line:
                        match = re.search(r'Weight:\s*([+-]?\d+\.?\d*)\s*g', line, re.IGNORECASE)
                        if match:
                            raw_value = float(match.group(1))
                            # Only accept reasonable values (between -200 and 200 raw)
                            if -200 < raw_value < 200:
                                latest_weight = raw_value

                if latest_weight is not None:
                    # Apply calibration
                    calibrated_weight = self.apply_calibration(latest_weight)

                    # Add to history for filtering
                    self.weight_history.append(calibrated_weight)

                    # Apply median filter (remove outliers)
                    if len(self.weight_history) >= 3:
                        sorted_history = sorted(self.weight_history)
                        median_weight = sorted_history[len(sorted_history) // 2]

                        # Only update if the reading is stable
                        if len(self.weight_history) >= 5:
                            # Check if readings are stable
                            recent = list(self.weight_history)[-5:]
                            avg = sum(recent) / len(recent)
                            is_stable = all(abs(w - avg) < 10 for w in recent)  # 10g stability threshold

                            if is_stable:
                                self.current_weight = median_weight
                                self.last_read_time = time.time()

                        # Always update with filtered value
                        self.current_weight = median_weight
                    else:
                        self.current_weight = calibrated_weight

                    # Debug print every 5th reading
                    self.debug_count += 1
                    if self.debug_count % 5 == 0:
                        print(
                            f"Raw: {latest_weight:.2f} → Calibrated: {calibrated_weight:.1f}g → Filtered: {self.current_weight:.1f}g")

                    return self.current_weight

        except Exception as e:
            print(f"Weight reading error: {e}")
        return self.current_weight

    def get_stable_weight_fast(self, timeout=3.0):
        """Get stable weight with better stability detection"""
        start_time = time.time()
        readings = []
        stable_readings = []

        print(f"Getting stable weight (timeout: {timeout}s)...")
        print("Place the item on the scale and hold still...")

        while time.time() - start_time < timeout:
            weight = self.read_single_weight()

            if weight > 0:
                readings.append(weight)
                print(f"  Reading {len(readings)}: {weight:.1f}g")

                # Need at least 5 readings to check stability
                if len(readings) >= 5:
                    # Take last 5 readings
                    recent = readings[-5:]
                    avg = sum(recent) / len(recent)

                    # Check if all readings are within 5g of average
                    if all(abs(w - avg) < 5 for w in recent):
                        stable_readings.append(avg)

                        # Need 3 stable readings in a row
                        if len(stable_readings) >= 3:
                            final_avg = sum(stable_readings[-3:]) / 3
                            print(f"✅ Stable weight found: {final_avg:.1f}g")
                            return final_avg
                    else:
                        # Reset stable counter if unstable
                        stable_readings = []

            time.sleep(0.1)  # 100ms between readings

        # Return average of all readings if no stable found
        if readings:
            avg = sum(readings) / len(readings)
            print(f"⚠️ No stable weight, using average: {avg:.1f}g")
            return avg

        print("❌ No weight readings found")
        return None


weight_reader = FastWeightReader()


# REST endpoints
@router.get("/weight")
def get_weight():
    """Get current weight instantly"""
    weight = weight_reader.read_single_weight()
    return {"weight": weight if weight > 0 else 0}


@router.get("/weight/stable")
def get_stable_weight():
    """Get stable weight (for admin calibration)"""
    weight = weight_reader.get_stable_weight_fast(timeout=3.0)
    if weight is None:
        return {"error": "No stable weight detected"}
    return {"weight": weight}


# WebSocket for real-time streaming
@router.websocket("/ws/weight")
async def websocket_weight(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    print("WebSocket client connected")

    try:
        last_sent_weight = 0
        while True:
            current_weight = await asyncio.to_thread(weight_reader.read_single_weight)

            if current_weight > 0 and abs(current_weight - last_sent_weight) > 2:
                await websocket.send_json({"weight": current_weight})
                last_sent_weight = current_weight

            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
            print("WebSocket client disconnected")
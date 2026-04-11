import serial
import time

try:
    ser = serial.Serial('COM5', 9600, timeout=1)
    time.sleep(2)

    print("Serial connected. Reading weight...")

    for i in range(10):
        line = ser.readline().decode(errors='ignore').strip()
        if line:
            print(f"Raw: {line}")
            if "Weight:" in line:
                weight = line.replace("Weight:", "").replace("g", "").strip()
                print(f"Weight: {weight}g")
        time.sleep(0.5)

    ser.close()
except Exception as e:
    print(f"Error: {e}")
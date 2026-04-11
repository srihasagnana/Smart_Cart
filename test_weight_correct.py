import serial
import time
import re

print("Testing load cell at 115200 baud rate...")
print("Press Ctrl+C to stop\n")

try:
    ser = serial.Serial('COM5', 115200, timeout=1)
    time.sleep(2)
    ser.reset_input_buffer()

    print("Connected! Reading data...\n")

    count = 0
    while count < 10:  # Read 10 samples
        if ser.in_waiting:
            # Read one line
            line = ser.readline().decode('utf-8', errors='ignore').strip()

            if line:
                print(f"Raw: {line}")

                # Parse weight
                match = re.search(r'Weight:\s*([+-]?\d+\.?\d*)\s*g', line)
                if match:
                    weight = float(match.group(1))
                    print(f"Weight: {weight:.2f} g")
                    count += 1
                else:
                    print("  (No weight pattern found)")

        time.sleep(0.1)

    ser.close()
    print("\nTest complete!")

except Exception as e:
    print(f"Error: {e}")
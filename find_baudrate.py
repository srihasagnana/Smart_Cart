import serial
import serial.tools.list_ports
import time


def test_baudrate(port, baudrate):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)
        ser.reset_input_buffer()

        print(f"\nTesting baudrate {baudrate}:")

        for i in range(10):
            # Read raw bytes
            if ser.in_waiting:
                data = ser.read(ser.in_waiting)
                print(f"Raw bytes: {data}")

                # Try to decode
                try:
                    text = data.decode('ascii', errors='ignore')
                    if text.strip():
                        print(f"Decoded: '{text}'")

                        # Look for numbers
                        import re
                        numbers = re.findall(r'\d+\.?\d*', text)
                        if numbers:
                            print(f"Numbers found: {numbers}")
                except:
                    pass

            time.sleep(0.1)

        ser.close()
        return True
    except Exception as e:
        print(f"Failed at {baudrate}: {e}")
        return False


# Find available ports
ports = serial.tools.list_ports.comports()
print("Available ports:")
for port in ports:
    print(f"  {port.device} - {port.description}")

# Use the correct COM port (change if needed)
PORT = 'COM5'

# Test common baud rates
baudrates = [9600, 115200, 57600, 4800, 2400, 19200, 38400]

print(f"\nTesting baud rates on {PORT}...")

for baud in baudrates:
    test_baudrate(PORT, baud)
    time.sleep(1)
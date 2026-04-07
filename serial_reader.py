import serial

ser = None

def get_serial():
    global ser
    if ser is None:
        ser = serial.Serial('COM5', 115200, timeout=1)
    return ser

def get_weight():
    try:
        ser = get_serial()   # 🔥 get connection here

        values = []

        while len(values) < 5:
            line = ser.readline().decode(errors='ignore').strip()
            print("RAW:", line)

            if line.startswith("Weight:"):
                value = float(line.replace("Weight:", "").replace("g", "").strip())

                if value > 5:
                    values.append(value)

        return sum(values) / len(values)

    except Exception as e:
        print("ERROR:", e)
        return None
import serial
from fastapi import APIRouter

router = APIRouter()
@router.get("/weight")
def get_weight():
    try:
        ser = serial.Serial('COM3', 9600, timeout=1)
        raw = ser.readline()
        print("RAW:", raw)

        weight = raw.decode().strip()
        print("DECODED:", weight)

        return {"weight": float(weight)}
    except Exception as e:
        print("ERROR:", e)
        return {"weight": 0}
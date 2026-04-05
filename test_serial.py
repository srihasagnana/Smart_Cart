import serial
import time

ser = serial.Serial('COM5', 9600)
time.sleep(2)

while True:
    print(ser.readline())
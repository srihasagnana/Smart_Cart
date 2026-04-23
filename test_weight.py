import requests
import time

BASE_URL = "http://127.0.0.1:8000"

print("Testing weight endpoint...")
print("Press Ctrl+C to stop\n")
import time
from frontend.frontend_app import get_weight_instant

while True:
    weight = get_weight_instant()
    print(f"Weight: {weight:.2f} g")
    time.sleep(0.1)

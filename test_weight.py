import requests
import time

BASE_URL = "http://127.0.0.1:8000"

print("Testing weight endpoint...")
print("Press Ctrl+C to stop\n")

try:
    while True:
        response = requests.get(f"{BASE_URL}/weight")
        if response.status_code == 200:
            weight = response.json().get("weight", 0)
            print(f"Weight: {weight:.2f} g")
        else:
            print(f"Error: {response.status_code}")

        time.sleep(0.5)  # Read every 0.5 seconds

except KeyboardInterrupt:
    print("\nStopped")
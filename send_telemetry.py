import time
import random
from datetime import datetime
import requests

# The live Azure reservoir URL
URL = "https://ahs-telemetry-ingest-api.azurewebsites.net/events"

def send_data():
    payload = {
        "event_id": random.randint(1000, 9999),
        "truck_id": str(random.randint(1, 10)),
        "event_type": "auto_telemetry",
        "event_timestamp": datetime.now().isoformat()
    }
    try:
        response = requests.post(URL, json=payload, timeout=5)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: {response.status_code} | Sent Payload for Truck #{payload['truck_id']}")
    except Exception as e:
        print(f"Error sending payload: {e}")

if __name__ == "__main__":
    print("Starting automated data stream to Azure... (Press CTRL+C to stop)")
    while True:
        send_data()
        time.sleep(10)  # Sends a new payload every 10 seconds
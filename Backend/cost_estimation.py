from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize FastAPI
app = FastAPI()

# Initialize Firebase
firebase_connected = False
try:
    cred = credentials.Certificate(r"serviceaccountkey.json") #Add File path here
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    firebase_connected = True
except Exception as e:
    print(f"Failed to connect to Firebase: {e}")

# Allowed device types
allowed_device_types = ["smart_phones", "pcs_laptops", "tablets"]

# Cost percentages based on issues
cost_percentages = {
    "smart_phones": {
        "broken_display": 2,
        "factory_reset_protection": 3,
        "passcode_unlock": 1,
        "randomly_turning_off": 3,
        "firmware_issue": 5,
        "touchscreen_issue": 6,
        "charging_port_issue": 10,
        "battery_replacement": 15,
        "microphone_issue": 7,
        "sound_issue": 5
    },
    "pcs_laptops": {
        "boot_issues": 5,
        "overheating": 2,
        "hard_drive_replacement": 4,
        "screen_replacement": 10,
        "keyboard_repair": 9,
        "touchpad_issue": 10,
        "battery_replacement": 5,
        "charger_port_repair": 3,
        "sound_issue": 5,
        "wifi_bluetooth_issue": 4
    },
    "tablets": {
        "screen_replacement": 10,
        "battery_replacement": 15,
        "charging_port_repair": 5,
        "touchscreen_issue": 10,
        "button_repair": 8,
        "software_issue": 9,
        "speaker_issue": 6,
        "camera_repair": 5,
        "connectivity_issue": 5,
        "storage_issue": 10
    }
}

# Pydantic model for the incoming request
class RepairRequest(BaseModel):
    device_type: str
    model: str  # Add model name for price lookup
    issue: str

@app.get("/")
async def read_root():
    if firebase_connected:
        return {"message": "Firebase connected successfully!"}
    else:
        return {"message": "Failed to connect to Firebase."}

@app.post("/calculate_cost/")
async def calculate_cost(request: RepairRequest):
    # Validate device type
    if request.device_type not in allowed_device_types:
        raise HTTPException(status_code=404, detail="Invalid device type")

    try:
        print(f"Received request: {request}")

        # Get device cost from Firestore
        doc_ref = db.collection("device_costs").document(request.device_type)
        doc = doc_ref.get()

        if not doc.exists:
            print(f"Device costs document for '{request.device_type}' not found in Firestore.")
            raise HTTPException(status_code=404, detail="Device costs document not found")

        devices_data = doc.to_dict()['devices']

        # Find the specific model and its price
        device_cost = next((device['Price'] for device in devices_data if device['Model'] == request.model), None)
        
        if device_cost is None:
            print(f"Model '{request.model}' not found for device type '{request.device_type}'.")
            raise HTTPException(status_code=404, detail="Model not found")

        print(f"Device cost for '{request.device_type} - {request.model}': {device_cost}")

        # Check if the issue is valid
        if request.issue not in cost_percentages[request.device_type]:
            print(f"Issue '{request.issue}' not found for device type '{request.device_type}'.")
            raise HTTPException(status_code=404, detail="Issue not found")

        percentage = cost_percentages[request.device_type][request.issue]
        estimated_cost = (percentage / 100) * device_cost
        
        return {
            "device_type": request.device_type,
            "model": request.model,
            "issue": request.issue,
            "device_cost": device_cost,
            "estimated_repair_cost": estimated_cost
        }

    except HTTPException as http_exc:
        print(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        print(f"Error in calculate_cost: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

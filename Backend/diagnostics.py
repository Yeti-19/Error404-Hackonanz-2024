from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize FastAPI
app = FastAPI()

# Initialize Firebase
cred = credentials.Certificate(r"serviceaccountkey.json")  # Add file path here
firebase_admin.initialize_app(cred)
db = firestore.client()

# Pydantic model for the incoming request
class DiagnosticRequest(BaseModel):
    device_type: str
    issue: str

@app.post("/diagnostics/")
async def run_diagnostics(request: DiagnosticRequest):
    # Fetch diagnostics data from Firestore
    try:
        doc_ref = db.collection("diagnostics").document("diagnostics_data")
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Diagnostics data document not found")

        diagnostics_data = doc.to_dict()

        # Validate device type
        if request.device_type not in diagnostics_data:
            raise HTTPException(status_code=404, detail="Invalid device type")

        # Validate issue
        if request.issue not in diagnostics_data[request.device_type]:
            raise HTTPException(status_code=404, detail="Issue not found for the specified device type")

        # Retrieve the steps to resolve
        steps_to_resolve = diagnostics_data[request.device_type][request.issue]['steps_to_resolve']

        return {
            "device_type": request.device_type,
            "issue": request.issue,
            "steps_to_resolve": steps_to_resolve
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


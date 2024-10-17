
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize FastAPI
app = FastAPI()

# Initialize Firebase
cred = credentials.Certificate(r"serviceaccountkey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()  # Ensure 'db' is initialized here

# Define the Pydantic model for the payment data
class Payment(BaseModel):
    paid_to: str
    amount: float

@app.post("/payments/")
async def create_payment(payment: Payment):
    if payment.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")

    try:
        # Get the reference to the payment history document
        doc_ref = db.collection("payment_history").document("payments")
        
        # Get existing data
        existing_data = doc_ref.get()
        if existing_data.exists:
            payment_history = existing_data.to_dict()
        else:
            payment_history = {"payments": []}

        # Append the new payment
        payment_history["payments"].append(payment.dict())
        
        # Update the document with the new payment history
        doc_ref.set(payment_history)
        
        return {"message": "Payment recorded successfully", "payment": payment.dict()}
    except Exception as e:
        print(f"Error saving payment: {e}")  # Print the actual error for debugging
        raise HTTPException(status_code=500, detail=f"Error saving payment: {e}")

@app.get("/payments/")
async def get_payment_history():
    try:
        doc_ref = db.collection("payment_history").document("payments")
        payment_data = doc_ref.get()
        
        if payment_data.exists:
            return payment_data.to_dict()
        else:
            return {"payments": []}  # No payments recorded yet
    except Exception as e:
        print(f"Error retrieving payment history: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving payment history")


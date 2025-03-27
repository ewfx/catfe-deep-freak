from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
from fastapi.middleware.cors import CORSMiddleware
# from starlette.middleware.cors import CORSMiddleware
import logging
from dotenv import load_dotenv
import os
import uvicorn

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    # allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

transactions = [
    {
        "transaction_id": "TXN001",
        "customer_id": "CUST123",
        "timestamp": datetime.now().isoformat(),
        "amount": 2500.5,
        "currency": "USD",
        "type": "Wire Transfer",
        "status": "Completed",
        "expected_result": "Successfully Processed"
    },
    {
        "transaction_id": "TXN002",
        "customer_id": "CUST456",
        "timestamp": datetime.now().isoformat(),
        "amount": 150,
        "currency": "EUR",
        "type": "Online Purchase",
        "status": "Completed",
        "expected_result": "Successfully Processed"
    }
]

fraud_cases = [
    {
        "fraud_id": "FRAUD001",
        "user": "CUST123",
        "location": "New York",
        "transaction_type": "Wire Transfer",
        "amount": 2500.5,
        "currency": "USD",
        "status": "Flagged",
        "risk_score": 0.95,
        "reason": "Unusual activity"
    }
]

# Models
class Transaction(BaseModel):
    transaction_id: str = Field(..., min_length=1, description="Unique transaction ID")
    customer_id: str = Field(..., min_length=1, description="Customer ID")
    timestamp: str = Field(..., description="Timestamp of the transaction")
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(..., min_length=3, max_length=3, description="Currency code (e.g., USD)")
    type: str = Field(..., description="Type of transaction (e.g., Wire Transfer)")
    status: str = Field(..., description="Status of the transaction (e.g., Completed)")
    expected_result: str = Field(..., description="Expected result of the transaction")

class FraudDetection(BaseModel):
    fraud_id: str = Field(..., min_length=1, description="Unique fraud ID")
    user: str = Field(..., min_length=1, description="User ID")
    location: str = Field(..., description="Location of the transaction")
    transaction_type: str = Field(..., description="Type of transaction (e.g., Wire Transfer)")
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(..., min_length=3, max_length=3, description="Currency code (e.g., USD)")
    status: str = Field(..., description="Status of the fraud case (e.g., Flagged)")
    risk_score: float = Field(..., ge=0, le=1, description="Risk score (0 to 1)")
    reason: str = Field(..., description="Reason for flagging the transaction")

# Endpoints
@app.get("/transactions/", response_model=List[Transaction], summary="Get all transactions")
def get_all_transactions():
    logger.info("Fetching all transactions")
    return transactions

@app.get(
    "/transactions/{transaction_id}",
    response_model=Transaction,
    summary="Get a transaction by ID",
    responses={404: {"description": "Transaction not found"}},
)
def get_transaction(transaction_id: str):
    logger.info(f"Fetching transaction with ID: {transaction_id}")
    transaction = next((t for t in transactions if t["transaction_id"] == transaction_id), None)
    if not transaction:
        logger.error(f"Transaction with ID {transaction_id} not found")
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@app.post(
    "/transactions/",
    response_model=Transaction,
    summary="Create a new transaction",
    description="Create a new transaction with the provided details.",
    response_description="The created transaction",
)
def create_transaction(transaction: Transaction):
    logger.info("Creating a new transaction")
    transactions.append(transaction.dict())
    return transaction

@app.get("/fraud/", response_model=List[FraudDetection], summary="Get all fraud cases")
def get_all_fraud_cases():
    logger.info("Fetching all fraud cases")
    return fraud_cases

@app.get(
    "/fraud/{fraud_id}",
    response_model=FraudDetection,
    summary="Get a fraud case by ID",
    responses={404: {"description": "Fraud case not found"}},
)
def get_fraud_case(fraud_id: str):
    logger.info(f"Fetching fraud case with ID: {fraud_id}")
    fraud_case = next((f for f in fraud_cases if f["fraud_id"] == fraud_id), None)
    if not fraud_case:
        logger.error(f"Fraud case with ID {fraud_id} not found")
        raise HTTPException(status_code=404, detail="Fraud case not found")
    return fraud_case

@app.post(
    "/fraud/",
    response_model=FraudDetection,
    summary="Create a new fraud case",
    description="Create a new fraud case with the provided details.",
    response_description="The created fraud case",
)
def create_fraud_case(fraud: FraudDetection):
    logger.info("Creating a new fraud case")
    fraud_cases.append(fraud.dict())
    return fraud

# Root endpoint
@app.get("/", summary="Root endpoint")
def read_root():
    return {"message": "Welcome to the FastAPI Testing Application!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
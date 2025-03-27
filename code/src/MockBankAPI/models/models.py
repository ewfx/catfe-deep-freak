from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
    
# Transaction Data Model
class Transaction(BaseModel):
    transaction_id: str
    transaction_type: str
    source_account: str
    source_currency: str
    destination_account: str = None
    destination_currency: str = None
    amount: float
    expected_result: str
    notes: str = None
    
class FraudDetection(BaseModel):
    fraud_id: str = Field(..., title="Fraud ID", description="Unique identifier for the fraud case")
    user: str = Field(..., title="User", description="Name of the user involved in the transaction")
    location: str = Field(..., title="Location", description="[Nigeria, Russia, India, North Korea, America, Venezuela]")
    transaction_type: str = Field(..., title="Transaction Type", description="[Credit Card, Wire Transfer, International Transfer, Online Payment, Microtransaction]")
    amount: float = Field(..., gt=0, title="Amount", description="Transaction amount")
    fraud_score: Optional[int] = Field(None, ge=0, le=100, title="Fraud Score", description="Score indicating fraud probability (0-100)")
    initial_fraud_pattern: Optional[str] = Field(None, title="Initial Fraud Pattern", description="Pattern detected initially in the fraud case")
    genai_evolved_fraud_pattern: Optional[str] = Field(None, title="GenAI Evolved Fraud Pattern", description="AI-predicted fraud pattern evolution")
    expected_alert_trigger: Optional[str] = Field(None, title="Expected Alert Trigger", description="The alert message generated for the fraud case")


# Regulatory Compliance Data Model    
class RegulatoryCompliance(BaseModel):
    transaction_id: str
    customer_id: str
    timestamp: datetime
    amount: float
    currency: str
    type: str
    status: str
    expected_result: str

# Loan Request Model
class LoanRequest(BaseModel):
    loan_id: str
    customer_id: str
    loan_amount: float
    credit_score: int
    employment_status: str
    debt_to_income_ratio: str
    approval_status: str
    expected_result: str
    
# AI Chatbot Models    
class ChatbotQuery(BaseModel):
    query_id: str
    user_query: str
    context: Optional[str] = None 


class ChatbotResponse(BaseModel):
    response_content: str
    compliance_flags: Optional[str] = None  
    result: Optional[str] = None
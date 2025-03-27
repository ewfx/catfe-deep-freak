import random
from fastapi import FastAPI, HTTPException
from models.models import Transaction, FraudDetection, RegulatoryCompliance, LoanRequest, ChatbotQuery, ChatbotResponse
import pandas as pd
import numpy as np
import os

app = FastAPI()

TRANSACTIONS_FILE = "db\\transactions.xlsx"
FRAUD_DETECTION_FILE = "db\\fraudDetectionData.xlsx"
REGULATORY_COMPLIANCE_FILE = "db\\regulatoryCompliance.xlsx"
LOAN_RISK_EXCEL_FILE = "db\\loan_risk.xlsx"
CHATBOT_INTERACTIONS_FILE = "db\\chatbotInteractions.xlsx"
SHEET_NAME = "Loan Risk"

if not os.path.exists(TRANSACTIONS_FILE):
    transactions_df = pd.DataFrame(columns=[
        "Transaction ID", "Transaction Type", "Source Account", "Source Currency",
        "Destination Account", "Destination Currency", "Amount", "Expected Result", "Notes"
    ])
    transactions_df.to_excel(TRANSACTIONS_FILE, index=False, engine="openpyxl")

if not os.path.exists(FRAUD_DETECTION_FILE):
    fraud_df = pd.DataFrame(columns=["Scenario ID", "User", "Location", "Transaction Type", "Amount", "Fraud Score",
                                     "Initial Fraud Pattern", "GenAI Evolved Fraud Pattern", "Expected Alert Trigger"])
    fraud_df.to_excel(FRAUD_DETECTION_FILE, index=False, engine="openpyxl")

if not os.path.exists(REGULATORY_COMPLIANCE_FILE):
    regulatoryCompliance_df = pd.DataFrame(columns=[
        "Transaction", "Customer", "ID", "Timestamp", "Amount", "Currency",
        "Type", "Status", "Expected Result"
    ])
    regulatoryCompliance_df.to_excel(REGULATORY_COMPLIANCE_FILE, index=False, engine="openpyxl")

if not os.path.exists(LOAN_RISK_EXCEL_FILE):
    df = pd.DataFrame(columns=[
        "Loan ID", "Customer ID", "Loan Amount (USD)", "Credit Score",
        "Employment Status", "Debt-to-Income Ratio", "Approval Status", "Expected Result"
    ])
    df.to_excel(LOAN_RISK_EXCEL_FILE, index=False, sheet_name=LOAN_RISK_EXCEL_FILE, engine="openpyxl")
    
if not os.path.exists(CHATBOT_INTERACTIONS_FILE):
    chatbot_interactions_df = pd.DataFrame(columns=[
        "Query ID", "User Query", "Context (Account Info/Alert)", "Chatbot Response",
        "Compliance Flags", "Result (Pass/Fail)"
    ])
    chatbot_interactions_df.to_excel(CHATBOT_INTERACTIONS_FILE, index=False, engine="openpyxl")

def clean_column_names(df):
    df.columns = df.columns.str.strip()
    return df

def read_excel(file_path):
    df = pd.read_excel(file_path, engine="openpyxl")
    return df.replace({np.nan: None})

def write_excel(file_path, df):
    df.to_excel(file_path, index=False, engine="openpyxl")
    
def generate_chatbot_response(query: ChatbotQuery) -> ChatbotResponse:
    if "balance" in query.user_query.lower():
        response_content = "Your balance is $5,000."
        compliance_flags = "None"
        result = "Pass"
    elif "transaction" in query.user_query.lower():
        response_content = "Your last transaction was $1,000 to XYZ Inc."
        compliance_flags = "None"
        result = "Pass"
    elif "fraud" in query.user_query.lower():
        response_content = "We've detected suspicious activity. Please contact support."
        compliance_flags = "Alert: Potential fraud"
        result = "Fail"
    else:
        response_content = "I'm sorry, I didn't understand your query."
        compliance_flags = "None"
        result = "Fail"

    return ChatbotResponse(
        response_content=response_content,
        compliance_flags=compliance_flags,
        result=result
    )    
    
# ─── TRANSACTION ENDPOINTS ───────────────────────────────────────────

@app.get("/transactions/", tags=["Transactions"])
async def get_all_transactions():
    df = read_excel(TRANSACTIONS_FILE)
    return df.to_dict(orient="records")


@app.get("/transactions/{transaction_id}", tags=["Transactions"])
async def get_transaction(transaction_id: str):
    df = read_excel(TRANSACTIONS_FILE)
    transaction = df[df["Transaction ID"] == transaction_id]

    if transaction.empty:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return transaction.to_dict(orient="records")[0]


@app.post("/transactions/", tags=["Transactions"])
async def create_transaction(transaction: Transaction):
    df = read_excel(TRANSACTIONS_FILE)

    if transaction.transaction_id in df["Transaction ID"].astype(str).values:
        raise HTTPException(status_code=400, detail="Transaction ID already exists")

    new_transaction = pd.DataFrame([[transaction.transaction_id, transaction.transaction_type,
                                    transaction.source_account, transaction.source_currency,
                                    transaction.destination_account, transaction.destination_currency,
                                    transaction.amount, transaction.expected_result, transaction.notes]],
                                   columns=df.columns)
    df = pd.concat([df, new_transaction], ignore_index=True)

    write_excel(TRANSACTIONS_FILE, df)

    return {"message": "Transaction added successfully", "transaction": transaction}


@app.put("/transactions/{transaction_id}", tags=["Transactions"])
async def update_transaction(transaction_id: str, updated_transaction: Transaction):
    df = read_excel(TRANSACTIONS_FILE)

    if transaction_id not in df["Transaction ID"].astype(str).values:
        raise HTTPException(status_code=404, detail="Transaction not found")

    df.loc[df["Transaction ID"] == transaction_id] = updated_transaction.dict().values()
    write_excel(TRANSACTIONS_FILE, df)

    return {"message": "Transaction updated successfully", "transaction": updated_transaction}


@app.delete("/transactions/{transaction_id}", tags=["Transactions"])
async def delete_transaction(transaction_id: str):
    df = read_excel(TRANSACTIONS_FILE)

    if transaction_id not in df["Transaction ID"].astype(str).values:
        raise HTTPException(status_code=404, detail="Transaction not found")

    df = df[df["Transaction ID"] != transaction_id]
    write_excel(TRANSACTIONS_FILE, df)

    return {"message": "Transaction deleted successfully"}


# ─── FRAUD DETECTION ENDPOINTS ────────────────────────────────────────

def calculate_fraud_score(transaction: FraudDetection):
    score = 0  
    if transaction.amount < 0:
        return -1
    elif transaction.amount > 100000:
        score += 39  
    elif transaction.amount > 50000:
        score += 34  
    elif transaction.amount > 10000:
        score += 24  
    elif transaction.amount > 5000:
        score += 14  
    elif transaction.amount > 1000:
        score += 7   

    high_risk_types = ["Wire Transfer", "Cryptocurrency", "International Transfer"]
    medium_risk_types = ["Online Payment", "Credit Card"]
    
    if transaction.transaction_type in high_risk_types:
        score += 26  
    elif transaction.transaction_type in medium_risk_types:
        score += 12  

    high_risk_countries = ["Nigeria", "Russia", "North Korea", "Venezuela"]
    if transaction.location in high_risk_countries:
        score += 18  

    if transaction.transaction_type == "Microtransaction" and transaction.amount < 50:
        score += 9  

    return score  

def assign_alert(score):
    if score > 90:
        return "Account breach alert"
    elif score > 80:
        return "Cyber attack alert"
    elif score > 70:
        return "Suspicious transaction alert"
    elif score > 50:
        return "Potential scam alert"
    elif score == -1:
        return "Invalid Details"
    else:
        return "No alert"


@app.post("/fraud-score/", tags=["Fraud Detection"])
async def score_fraud(fraud: FraudDetection):
    df = read_excel(FRAUD_DETECTION_FILE)

    fraud_score = calculate_fraud_score(fraud)
    alert = assign_alert(fraud_score)

    new_fraud_case = pd.DataFrame([{
        "Scenario ID": fraud.fraud_id,
        "User": fraud.user,
        "Location": fraud.location,
        "Transaction Type": fraud.transaction_type,
        "Amount": fraud.amount,
        "Fraud Score": fraud_score,
        "Expected Alert Trigger": alert
    }], columns=df.columns)

    df = pd.concat([df, new_fraud_case], ignore_index=True)
    write_excel(FRAUD_DETECTION_FILE, df)

    return {
        "message": "Fraud case scored successfully",
        "fraud_id": fraud.fraud_id,
        "fraud_score": fraud_score,
        "alert_trigger": alert
    }


# # ─── REGULATORY COMPLIANCE ENDPOINTS ──────────────────────────────────

# @app.get("/regulatory-compliance/", tags=["Regulatory Compliance"])
# async def get_all_regulatory_compliance():
#     df = read_excel(REGULATORY_COMPLIANCE_FILE)
#     return df.to_dict(orient="records")


# @app.get("/regulatory-compliance/{compliance_id}", tags=["Regulatory Compliance"])
# async def get_regulatory_compliance(compliance_id: str):
#     df = read_excel(REGULATORY_COMPLIANCE_FILE)
#     compliance = df[df["ID"] == compliance_id]

#     if compliance.empty:
#         raise HTTPException(status_code=404, detail="Regulatory compliance record not found")

#     return compliance.to_dict(orient="records")[0]


# @app.post("/regulatory-compliance/", tags=["Regulatory Compliance"])
# async def create_regulatory_compliance(compliance: RegulatoryCompliance):
#     df = read_excel(REGULATORY_COMPLIANCE_FILE)

#     if compliance.id in df["ID"].astype(str).values:
#         raise HTTPException(status_code=400, detail="Compliance ID already exists")

#     new_compliance = pd.DataFrame([compliance.dict()])
#     df = pd.concat([df, new_compliance], ignore_index=True)

#     write_excel(REGULATORY_COMPLIANCE_FILE, df)

#     return {"message": "Regulatory compliance record added successfully", "compliance": compliance}


# @app.put("/regulatory-compliance/{compliance_id}", tags=["Regulatory Compliance"])
# async def update_regulatory_compliance(compliance_id: str, updated_compliance: RegulatoryCompliance):
#     df = read_excel(REGULATORY_COMPLIANCE_FILE)

#     if compliance_id not in df["ID"].astype(str).values:
#         raise HTTPException(status_code=404, detail="Regulatory compliance record not found")

#     df.loc[df["ID"] == compliance_id] = updated_compliance.dict().values()
#     write_excel(REGULATORY_COMPLIANCE_FILE, df)

#     return {"message": "Regulatory compliance record updated successfully", "compliance": updated_compliance}


# @app.delete("/regulatory-compliance/{compliance_id}", tags=["Regulatory Compliance"])
# async def delete_regulatory_compliance(compliance_id: str):
#     df = read_excel(REGULATORY_COMPLIANCE_FILE)

#     if compliance_id not in df["ID"].astype(str).values:
#         raise HTTPException(status_code=404, detail="Regulatory compliance record not found")

#     df = df[df["ID"] != compliance_id]
#     write_excel(REGULATORY_COMPLIANCE_FILE, df)

#     return {"message": "Regulatory compliance record deleted successfully"}


# # ─── LOAN RISK ENDPOINTS ──────────────────────────────────

# # GET all loan applications
# @app.get("/loans/", tags=["Loan Risk"])
# async def get_all_loans():
#     df = pd.read_excel(LOAN_RISK_EXCEL_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
#     df = clean_column_names(df)
#     return df.to_dict(orient="records")

# # GET a specific loan by Loan ID
# @app.get("/loans/{loan_id}", tags=["Loan Risk"])
# async def get_loan(loan_id: str):
#     df = pd.read_excel(LOAN_RISK_EXCEL_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
#     df = clean_column_names(df)

#     if loan_id not in df["Loan ID"].astype(str).values:
#         raise HTTPException(status_code=404, detail="Loan not found")

#     loan = df[df["Loan ID"].astype(str) == loan_id].to_dict(orient="records")[0]
#     return loan

# # POST - Add new loan application
# @app.post("/loans/", tags=["Loan Risk"])
# async def add_loan(loan: LoanRequest):
#     df = pd.read_excel(LOAN_RISK_EXCEL_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
#     df = clean_column_names(df)

#     if loan.loan_id in df["Loan ID"].astype(str).values:
#         raise HTTPException(status_code=400, detail="Loan ID already exists")

#     new_loan = pd.DataFrame([[loan.loan_id, loan.customer_id, loan.loan_amount, loan.credit_score,
#                               loan.employment_status, loan.debt_to_income_ratio, loan.approval_status,
#                               loan.expected_result]],
#                             columns=df.columns)

#     # Append new data and save to Excel
#     df = pd.concat([df, new_loan], ignore_index=True)
#     df.to_excel(LOAN_RISK_EXCEL_FILE, index=False, sheet_name=SHEET_NAME, engine="openpyxl")

#     return {"message": "Loan application added successfully", "loan": loan}

# # PUT - Update existing loan
# @app.put("/loans/{loan_id}", tags=["Loan Risk"])
# async def update_loan(loan_id: str, loan: LoanRequest):
#     df = pd.read_excel(LOAN_RISK_EXCEL_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
#     df = clean_column_names(df)

#     if loan_id not in df["Loan ID"].astype(str).values:
#         raise HTTPException(status_code=404, detail="Loan not found")

#     df.loc[df["Loan ID"].astype(str) == loan_id, :] = [
#         loan.loan_id, loan.customer_id, loan.loan_amount, loan.credit_score,
#         loan.employment_status, loan.debt_to_income_ratio, loan.approval_status, loan.expected_result
#     ]

#     df.to_excel(LOAN_RISK_EXCEL_FILE, index=False, sheet_name=SHEET_NAME, engine="openpyxl")
#     return {"message": "Loan updated successfully", "loan": loan}

# # DELETE - Remove loan by Loan ID
# @app.delete("/loans/{loan_id}", tags=["Loan Risk"])
# async def delete_loan(loan_id: str):
#     df = pd.read_excel(LOAN_RISK_EXCEL_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
#     df = clean_column_names(df)

#     if loan_id not in df["Loan ID"].astype(str).values:
#         raise HTTPException(status_code=404, detail="Loan not found")

#     df = df[df["Loan ID"].astype(str) != loan_id]

#     df.to_excel(LOAN_RISK_EXCEL_FILE, index=False, sheet_name=SHEET_NAME, engine="openpyxl")
#     return {"message": "Loan deleted successfully"}


# ─── AI CHATBOT ENDPOINTS ─────────────────────────────────────────────

@app.post("/chatbot/query/", tags=["AI Chatbot"])
async def handle_chatbot_query(query: ChatbotQuery):
    """
    Handle user queries and return chatbot responses.
    Log the interaction for compliance and testing purposes.
    """
    df = read_excel(CHATBOT_INTERACTIONS_FILE)

    response = generate_chatbot_response(query)

    new_interaction = pd.DataFrame([{
        "Query ID": query.query_id,
        "User Query": query.user_query,
        "Context (Account Info/Alert)": query.context,
        "Chatbot Response": response.response_content,
        "Compliance Flags": response.compliance_flags,
        "Result (Pass/Fail)": response.result
    }])
    df = pd.concat([df, new_interaction], ignore_index=True)
    write_excel(CHATBOT_INTERACTIONS_FILE, df)

    return {"response": response}


@app.get("/chatbot/interactions/", tags=["AI Chatbot"])
async def get_all_chatbot_interactions():
    """
    Retrieve all chatbot interactions for testing and compliance review.
    """
    df = read_excel(CHATBOT_INTERACTIONS_FILE)
    return df.to_dict(orient="records")


@app.get("/chatbot/interactions/{query_id}", tags=["AI Chatbot"])
async def get_chatbot_interaction(query_id: str):
    """
    Retrieve a specific chatbot interaction by Query ID.
    """
    df = read_excel(CHATBOT_INTERACTIONS_FILE)
    interaction = df[df["Query ID"] == query_id]

    if interaction.empty:
        raise HTTPException(status_code=404, detail="Chatbot interaction not found")

    return interaction.to_dict(orient="records")[0]
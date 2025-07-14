from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
import httpx
import time
import sqlite3

# LangChain & Azure OpenAI imports
from langchain_openai import AzureChatOpenAI
from langchain.agents import initialize_agent, AgentType, Tool
import requests

# --- Azure OpenAI config (fill in your values) ---
AZURE_ENDPOINT = "YOUR_AZURE_OPENAI_ENDPOINT"
AZURE_AD_TOKEN = "YOUR_AZURE_AD_TOKEN"
AZURE_API_VERSION = "YOUR_API_VERSION"

# --- Payment Tool Implementation ---
def payment_tool(input_dict):
    policy_nbr = input_dict.get('policyNbr')
    session_id = input_dict.get('sessionId')
    if not policy_nbr:
        return "To make a payment, I need your policyNbr."
    payload = {'policyNbr': policy_nbr}
    if session_id:
        payload['sessionId'] = session_id
    try:
        resp = requests.post(
            'http://localhost:5002/payment',
            json=payload,
            timeout=5
        )
        if resp.headers.get('content-type', '').startswith('application/json'):
            data = resp.json()
            return data.get('message', 'Payment processed.')
        else:
            return f"Payment agent error: {resp.text}"
    except Exception as e:
        return f"Error contacting payment agent: {str(e)}"

def eazy_pay_tool(input_dict):
    return "Eazy Pay enrolled"

# --- Define tools for the agent ---
tools = [
    Tool(
        name="PaymentTool",
        func=payment_tool,
        description="Call this to make a payment. Input must include policyNumber, accountNumber, routingNumber."
    ),
    Tool(
        name="EazyPay",
        func=eazy_pay_tool,
        description="Call this to setup automatic payments. when user reponds yes to a message any questions similar to do you want to enroll for Auto pay or easy pay"
    ),
    # Add more tools here
]

# --- LangChain Agent Setup ---
llm = AzureChatOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    azure_ad_token=AZURE_AD_TOKEN,
    default_headers={},
    api_version=AZURE_API_VERSION
)

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import time
import sqlite3

SESSION_TTL = 600  # 10 minutes

# SQLite in-memory DB
conn = sqlite3.connect(':memory:', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    last_intent TEXT,
    policy_number TEXT,
    pending_action TEXT,
    last_used REAL,
    account_info TEXT,
    last_decision TEXT
)''')
conn.commit()

def cleanup_sessions():
    now = time.time()
    c.execute('DELETE FROM sessions WHERE ? - last_used > ?', (now, SESSION_TTL))
    conn.commit()

@app.post("/api/chatbot")
async def chatbot(req):
    cleanup_sessions()
    session_id = req.sessionId
    now = time.time()

    # Fetch session state from SQLite
    if session_id:
        c.execute('SELECT last_intent, policy_number, pending_action FROM sessions WHERE session_id=?', (session_id,))
        row = c.fetchone()
        if not row:
            c.execute('INSERT INTO sessions (session_id, last_intent, policy_number, pending_action, last_used) VALUES (?, NULL, NULL, NULL, ?)', (session_id, now))
            conn.commit()
            last_intent, policy, pending_action = None, None, None
        else:
            last_intent, policy, pending_action = row
    else:
        last_intent, policy, pending_action = None, None, None

    # --- EasyPay follow-up handling ---
    if session_id and pending_action == "eazypay_offer":
        user_reply = req.message.strip().lower()
        if user_reply in ["yes", "ok", "yep", "sure"]:
            # Instruct agent to call EasyPay tool
            followup_prompt = (
                f"The user previously received an offer to enroll in EasyPay. "
                f"They responded '{req.message}'. Call the EasyPay tool for policy number {policy}."
            )
            agent_result = agent.invoke({"input": followup_prompt})
            reply = agent_result["output"] if isinstance(agent_result, dict) and "output" in agent_result else str(agent_result)
            c.execute('UPDATE sessions SET pending_action=NULL, last_used=? WHERE session_id=?', (now, session_id))
            conn.commit()
            return {"reply": reply}
        elif user_reply in ["no", "nope"]:
            c.execute('UPDATE sessions SET pending_action=NULL, last_used=? WHERE session_id=?', (now, session_id))
            conn.commit()
            return {"reply": "Okay, you have not been enrolled in EasyPay."}
        # If not a clear yes/no, fall through to normal agent logic

    # Compose context for the agent
    session_context = {
        "policyNumber": policy,
        "last_intent": last_intent
    }

    # --- Improved agent prompt for payment/payment method intent ---
    agent_prompt = (
        "You are an AI Agent who assists customers with making payments and updating their payment methods.\n"
        "Thiru is a customer who is logged in, authenticated, and the system knows the policy number #79450054509.\n"
        "The customer may have an intent to: make a payment only, change the payment method only, or do both at the same time.\n"
        "If the customer’s message has the intent to change the payment method (alone or along with payment), respond strictly with: 'Please provide your account details to change your payment method.'\n"
        "If the user's intent is only to make a payment, respond strictly with: 'You have an outstanding payment of $50, please confirm to go ahead and make payment.' For this, use the payment tool to make the payment.\n"
        "Always use any known session information.\n"
        f"User message: {req.message}"
    )
    # Call the agent (sync call for now)
    agent_result = agent.invoke({"input": agent_prompt})
    reply = agent_result["output"] if isinstance(agent_result, dict) and "output" in agent_result else str(agent_result)

    # --- Session logic for account info and last decision tracking ---
    # If user is asked for account details, set pending_action and last_decision
    if session_id:
        if "please provide your account details to change your payment method" in reply.lower():
            c.execute('UPDATE sessions SET pending_action=?, last_decision=?, last_used=? WHERE session_id=?',
                      ("awaiting_account_info", "payment_method_change", now, session_id))
            conn.commit()
        elif "please confirm to go ahead and make payment" in reply.lower():
            c.execute('UPDATE sessions SET pending_action=?, last_decision=?, last_used=? WHERE session_id=?',
                      (None, "payment", now, session_id))
            conn.commit()

    # Optionally update session state (for demo, just update last_used)
    if session_id:
        c.execute('UPDATE sessions SET last_used=? WHERE session_id=?', (now, session_id))
        conn.commit()

    return {"reply": reply}


from fastapi import Body
import json

@app.post("/api/update_account_info")
async def update_account_info(
    sessionId: str = Body(...),
    first_name: str = Body(...),
    last_name: str = Body(...),
    routing_number: str = Body(...),
    account_number: str = Body(...),
    confirm_account_number: str = Body(...),
    account_type: str = Body(...),
    make_payment: bool = Body(False)
):
    # Basic validation
    if account_number != confirm_account_number:
        return {"success": False, "message": "Account numbers do not match."}
    account_info = {
        "first_name": first_name,
        "last_name": last_name,
        "routing_number": routing_number,
        "account_number": account_number,
        "account_type": account_type
    }
    now = time.time()
    # Determine last_decision
    last_decision = "both" if make_payment else "payment_method_changed"
    # Store account info and decision
    c.execute('UPDATE sessions SET account_info=?, last_decision=?, last_used=? WHERE session_id=?',
              (json.dumps(account_info), last_decision, now, sessionId))
    conn.commit()
    payment_result = None
    if make_payment:
        # Fetch policy number from session
        c.execute('SELECT policy_number FROM sessions WHERE session_id=?', (sessionId,))
        row = c.fetchone()
        policy_number = row[0] if row and row[0] else None
        # Call payment tool if policy number is present
        if policy_number:
            payment_result = payment_tool({
                'policyNbr': policy_number,
                'sessionId': sessionId
            })
        else:
            payment_result = 'Policy number not found, payment not made.'
    return {
        "success": True,
        "message": "Account information updated successfully." if not make_payment else "Account information updated and payment processed.",
        "payment_result": payment_result
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5001)

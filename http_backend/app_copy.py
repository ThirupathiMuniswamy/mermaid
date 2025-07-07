from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BPO_PAYMENT_URL = 'http://localhost:5002/payment'

class ChatbotRequest(BaseModel):
    message: str
    sessionId: str | None = None
    policyNumber: str | None = None
    accountNumber: str | None = None
    routingNumber: str | None = None

class ChatbotResponse(BaseModel):
    reply: str


def extract_payment_info(message: str):
    # Lowercase for easier matching
    msg = message.lower()
    # Regex for all fields, supporting flexible separators and ordering
    patterns = {
        'policyNumber': r'policy number(?: is|:)?\s*(\d+)',
        'accountNumber': r'account number(?: is|:)?\s*(\d+)',
        'routingNumber': r'routing number(?: is|:)?\s*(\d+)',
    }
    results = {}
    for key, pat in patterns.items():
        match = re.search(pat, msg)
        if not match:
            # Try to match with possible separators like ',', 'and', or '.'
            match = re.search(pat + r'(?=\s|,|\.|and|$)', msg)
        results[key] = match.group(1) if match else None
    return results


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
    account_number TEXT,
    routing_number TEXT,
    last_used REAL
)''')
conn.commit()

def cleanup_sessions():
    now = time.time()
    c.execute('DELETE FROM sessions WHERE ? - last_used > ?', (now, SESSION_TTL))
    conn.commit()

@app.post("/api/chatbot", response_model=ChatbotResponse)
async def chatbot(req: ChatbotRequest):
    cleanup_sessions()
    message = req.message.lower()
    info = extract_payment_info(message)
    session_id = req.sessionId
    now = time.time()
    if session_id:
        # Fetch or create session row
        c.execute('SELECT last_intent, policy_number, account_number, routing_number FROM sessions WHERE session_id=?', (session_id,))
        row = c.fetchone()
        if not row:
            c.execute('INSERT INTO sessions (session_id, last_intent, policy_number, account_number, routing_number, last_used) VALUES (?, NULL, NULL, NULL, NULL, ?)', (session_id, now))
            conn.commit()
            last_intent, policy, account, routing = None, None, None, None
        else:
            last_intent, policy, account, routing = row
        # Update intent
        if 'payment' in message:
            last_intent = 'payment'
        # Merge payment info
        policy = req.policyNumber or info['policyNumber'] or policy
        account = req.accountNumber or info['accountNumber'] or account
        routing = req.routingNumber or info['routingNumber'] or routing
        c.execute('UPDATE sessions SET last_intent=?, policy_number=?, account_number=?, routing_number=?, last_used=? WHERE session_id=?', (last_intent, policy, account, routing, now, session_id))
        conn.commit()
        # If last intent is payment, try to process
        if last_intent == 'payment':
            if policy and account and routing:
                try:
                    async with httpx.AsyncClient(timeout=5) as client:
                        resp = await client.post(BPO_PAYMENT_URL, json={
                            'policyNumber': policy,
                            'accountNumber': account,
                            'routingNumber': routing
                        })
                    if resp.status_code == 200:
                        # Clear session after success
                        c.execute('UPDATE sessions SET last_intent=NULL, policy_number=NULL, account_number=NULL, routing_number=NULL WHERE session_id=?', (session_id,))
                        conn.commit()
                        return {"reply": resp.json().get('message', 'Payment processed.')}
                    else:
                        return {"reply": 'Payment failed: ' + resp.json().get('message', 'Unknown error.')}
                except Exception as e:
                    return {"reply": f'Error contacting payment agent: {str(e)}'}
            else:
                missing = [k for k, v in [('policy number', policy), ('account number', account), ('routing number', routing)] if not v]
                return {"reply": f'To make a payment, I need your {", ".join(missing)}.'}
        return {"reply": 'Sorry, I did not understand. Can you please clarify your request?'}
    # No session: fallback
    policy = req.policyNumber or info['policyNumber']
    account = req.accountNumber or info['accountNumber']
    routing = req.routingNumber or info['routingNumber']
    if 'payment' in message:
        if policy and account and routing:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.post(BPO_PAYMENT_URL, json={
                        'policyNumber': policy,
                        'accountNumber': account,
                        'routingNumber': routing
                    })
                if resp.status_code == 200:
                    return {"reply": resp.json().get('message', 'Payment processed.')}
                else:
                    return {"reply": 'Payment failed: ' + resp.json().get('message', 'Unknown error.')}
            except Exception as e:
                return {"reply": f'Error contacting payment agent: {str(e)}'}
        else:
            missing = [k for k, v in [('policy number', policy), ('account number', account), ('routing number', routing)] if not v]
            return {"reply": f'To make a payment, I need your {", ".join(missing)}.'}
    elif 'asset' in message:
        return {"reply": 'To add an asset, I need the make, year, and model.'}
    else:
        return {"reply": 'Sorry, I did not understand. Can you please clarify your request?'}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5001)

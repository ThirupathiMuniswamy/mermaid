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

# In-memory session store: { sessionId: { 'last_intent': str, 'payment_info': {}, 'last_used': float } }
session_memory = {}
SESSION_TTL = 600  # 10 minutes

def cleanup_sessions():
    now = time.time()
    to_del = [sid for sid, v in session_memory.items() if now - v.get('last_used', 0) > SESSION_TTL]
    for sid in to_del:
        del session_memory[sid]

@app.post("/api/chatbot", response_model=ChatbotResponse)
async def chatbot(req: ChatbotRequest):
    cleanup_sessions()
    message = req.message.lower()
    session_id = req.sessionId
    info = extract_payment_info(message)
    # Session memory logic
    if session_id:
        session = session_memory.setdefault(session_id, {'last_intent': None, 'payment_info': {}, 'last_used': time.time()})
        session['last_used'] = time.time()
        # If this message is a payment intent, update intent
        if 'payment' in message:
            session['last_intent'] = 'payment'
        # Always update payment_info with any new info
        for k in ['policyNumber', 'accountNumber', 'routingNumber']:
            if info[k]:
                session['payment_info'][k] = info[k]
        # Also use explicitly provided fields
        for k in ['policyNumber', 'accountNumber', 'routingNumber']:
            v = getattr(req, k)
            if v:
                session['payment_info'][k] = v
        # If last intent was payment, try to process
        if session['last_intent'] == 'payment':
            policy = session['payment_info'].get('policyNumber')
            account = session['payment_info'].get('accountNumber')
            routing = session['payment_info'].get('routingNumber')
            if policy and account and routing:
                try:
                    async with httpx.AsyncClient(timeout=5) as client:
                        resp = await client.post(BPO_PAYMENT_URL, json={
                            'policyNumber': policy,
                            'accountNumber': account,
                            'routingNumber': routing
                        })
                    if resp.status_code == 200:
                        # Clear session payment info after success
                        session['payment_info'] = {}
                        session['last_intent'] = None
                        return {"reply": resp.json().get('message', 'Payment processed.')}
                    else:
                        return {"reply": 'Payment failed: ' + resp.json().get('message', 'Unknown error.')}
                except Exception as e:
                    return {"reply": f'Error contacting payment agent: {str(e)}'}
            else:
                missing = [k for k, v in [('policy number', policy), ('account number', account), ('routing number', routing)] if not v]
                return {"reply": f'To make a payment, I need your {", ".join(missing)}.'}
        # If no intent or not enough info, fallback
        return {"reply": 'Sorry, I did not understand. Can you please clarify your request?'}
    # No session: fallback to stateless
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
            return {"reply": 'To make a payment, I need your policy number, account number, and routing number.'}
    elif 'asset' in message:
        return {"reply": 'To add an asset, I need the make, year, and model.'}
    else:
        return {"reply": 'Sorry, I did not understand. Can you please clarify your request?'}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5001)

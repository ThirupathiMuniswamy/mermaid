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
    last_used REAL
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
        c.execute('SELECT last_intent, policy_number FROM sessions WHERE session_id=?', (session_id,))
        row = c.fetchone()
        if not row:
            c.execute('INSERT INTO sessions (session_id, last_intent, policy_number, last_used) VALUES (?, NULL, NULL, ?)', (session_id, now))
            conn.commit()
            last_intent, policy = None, None
        else:
            last_intent, policy = row
    else:
        last_intent, policy = None, None

    # Compose context for the agent
    session_context = {
        "policyNumber": policy,
        "last_intent": last_intent
    }
    agent_prompt = (
        f"You are an AI assistant. Extract the user's intent from their message and call the correct tool. "
        f"If making a payment, use any known info from session: {session_context}. "
        f"User message: {req.message}"
    )
    # Call the agent (sync call for now)
    agent_result = agent.invoke({"input": agent_prompt})
    reply = agent_result["output"] if isinstance(agent_result, dict) and "output" in agent_result else str(agent_result)

    # Optionally update session state (for demo, just update last_used)
    if session_id:
        c.execute('UPDATE sessions SET last_used=? WHERE session_id=?', (now, session_id))
        conn.commit()

    return {"reply": reply}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5001)

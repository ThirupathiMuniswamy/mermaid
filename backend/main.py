import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

# CONFIG
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")
LLM_MODEL = os.getenv("LLM_MODEL", "azure-openai/gpt-35-turbo")  # Use your Azure OpenAI deployment name

app = FastAPI(title="AI Agent Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP Client and Agent Setup (async)
agent = None

async def setup_agent():
    global agent
    client = MultiServerMCPClient(
        {
            "payments": {
                "url": MCP_SERVER_URL,
                "transport": "streamable_http",
            }
        }
    )
    tools = await client.get_tools()
    agent = create_react_agent(LLM_MODEL, tools)

@app.on_event("startup")
async def on_startup():
    await setup_agent()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            user_msg = await websocket.receive_text()
            await websocket.send_json({"step": "received", "detail": "Message received from client"})
            # Run the agent asynchronously, with tool-calling step tracking
            await websocket.send_json({"step": "agent_invoked", "detail": "AI Agent invoked"})
            # Patch agent to emit tool steps if possible
            # For now, just simulate tool call detection
            # In production, you should hook into the agent/tool call events
            if "payment" in user_msg.lower():
                await websocket.send_json({"step": "tool_invoked", "tool": "Payment history", "detail": "Calling MCP tool"})
            response = await agent.ainvoke(
                {"messages": [{"role": "user", "content": user_msg}]}
            )
            await websocket.send_json({"step": "completed", "detail": "Response ready", "message": response})
    except WebSocketDisconnect:
        pass

@app.get("/")
def root():
    return {"message": "AI Agent Backend Running"}

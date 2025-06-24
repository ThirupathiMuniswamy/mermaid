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
    # agent = create_react_agent(LLM_MODEL, tools)

@app.on_event("startup")
async def on_startup():
    await setup_agent()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            user_msg = await websocket.receive_text()
            # Send step events to the visualizer
            await websocket.send_json({"target": "visualizer", "step": "received", "detail": "Message received from client"})
            await websocket.send_json({"target": "visualizer", "step": "agent_invoked", "detail": "AI Agent invoked"})
            if "payment" in user_msg.lower():
                await websocket.send_json({"target": "visualizer", "step": "tool_invoked", "tool": "Payment history", "detail": "Calling MCP tool"})
            # response = await agent.ainvoke(
            #     {"messages": [{"role": "user", "content": user_msg}]}
            # )
            # Only the final response to chatbot
            await websocket.send_json({"target": "chatbot", "step": "completed", "detail": "Response ready"})
    except WebSocketDisconnect:
        pass

@app.get("/")
def root():
    return {"message": "AI Agent Backend Running"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PaymentRequest(BaseModel):
    policyNumber: str | None = None
    accountNumber: str | None = None
    routingNumber: str | None = None

class PaymentResponse(BaseModel):
    status: str
    message: str

@app.post("/payment", response_model=PaymentResponse)
async def payment(req: PaymentRequest):
    if req.policyNumber and req.accountNumber and req.routingNumber:
        return {"status": "success", "message": "Payment made successfully."}
    else:
        return {"status": "error", "message": "Missing payment information."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5002)

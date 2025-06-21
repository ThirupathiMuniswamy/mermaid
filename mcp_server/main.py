from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Payments")

@mcp.tool()
async def get_payment_history() -> str:
    """Get the payment history for the customer."""
    return (
        "2024-06-01: $100.0 Paid\n"
        "2024-07-01: $100.0 Late"
    )

@mcp.tool()
async def setup_autopay(account_number: str, routing_number: str, amount: float) -> str:
    """Set up automatic payments using account and routing number."""
    return (
        f"AutoPay set up for ${amount} using account {account_number}."
    )

if __name__ == "__main__":
    mcp.run(transport="streamable-http")


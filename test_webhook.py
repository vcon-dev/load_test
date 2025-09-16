#!/usr/bin/env python3
"""
Simple webhook server test to verify webhook functionality
"""

import asyncio
import json
import logging
from fastapi import FastAPI, Request
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
webhook_data = []

@app.post("/webhook")
async def webhook_endpoint(request: Request):
    """Receive webhook data from conserver"""
    try:
        logger.info("Webhook endpoint called!")
        data = await request.json()
        logger.info(f"Webhook data received: {data}")
        webhook_data.append(data)
        logger.info(f"Total webhooks received: {len(webhook_data)}")
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/webhooks")
async def get_webhooks():
    """Get all received webhooks"""
    return {"webhooks": webhook_data, "count": len(webhook_data)}

if __name__ == "__main__":
    print("Starting webhook server on port 8080...")
    print("Send test webhook with: curl -X POST http://localhost:8080/webhook -H 'Content-Type: application/json' -d '{\"test\": \"data\"}'")
    uvicorn.run(app, host="0.0.0.0", port=8080)

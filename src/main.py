import os
import json
import asyncio
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from .models import ChatCompletionRequest
from .browser_manager import browser_manager

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatGPT Free Reverse Proxy",
    description="Ubuntu X86_64 + Cloudflare Bypass Version",
    version="3.0"
)

@app.on_event("startup")
async def startup():
    logger.info("Starting FastAPI application...")
    await browser_manager.init_browser()
    asyncio.create_task(browser_manager.keep_alive())

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, raw_req: Request):
    logger.info(f"Incoming POST /v1/chat/completions from {raw_req.client.host}")
    
    if not browser_manager.page:
        logger.error("Browser page is not initialized.")
        raise HTTPException(503, "Browser is not ready yet")
    
    prompt = request.messages[-1].content
    logger.info(f"Received prompt (length: {len(prompt)}). Stream mode: {request.stream}")

    if request.stream:
        return StreamingResponse(
            browser_manager.send_message_and_stream(prompt),
            media_type="text/event-stream"
        )
    else:
        full_response = ""
        async for chunk in browser_manager.send_message_and_stream(prompt):
            if "error" in chunk:
                error_msg = None
                try:
                    data = json.loads(chunk.split("data: ")[1])
                    if "error" in data:
                        error_msg = data["error"]
                except Exception:
                    pass
                
                if error_msg:
                    logger.error(f"Error chunk received: {error_msg}")
                    raise HTTPException(500, detail=error_msg)

            if "content" in chunk:
                try:
                    data = json.loads(chunk.split("data: ")[1])
                    full_response += data["choices"][0]["delta"].get("content", "")
                except:
                    pass
        
        logger.info(f"Returning completed non-streaming response (length: {len(full_response)})")
        return {
            "choices": [{"message": {"role": "assistant", "content": full_response}}]
        }

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "3.0"}

if __name__ == "__main__":
    import uvicorn
    # Default port changed to 8005
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8005)))

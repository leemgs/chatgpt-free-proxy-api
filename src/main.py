import os
import json
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from .models import ChatCompletionRequest
from .browser_manager import browser_manager

load_dotenv()

app = FastAPI(
    title="ChatGPT Free Reverse Proxy",
    description="Raspberry Pi + Cloudflare Bypass Version",
    version="3.0"
)

@app.on_event("startup")
async def startup():
    await browser_manager.init_browser()
    asyncio.create_task(browser_manager.keep_alive())

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    if not browser_manager.page:
        raise HTTPException(503, "Browser is not ready yet")
    
    prompt = request.messages[-1].content

    if request.stream:
        return StreamingResponse(
            browser_manager.send_message_and_stream(prompt),
            media_type="text/event-stream"
        )
    else:
        full_response = ""
        async for chunk in browser_manager.send_message_and_stream(prompt):
            if "content" in chunk:
                try:
                    data = json.loads(chunk.split("data: ")[1])
                    full_response += data["choices"][0]["delta"].get("content", "")
                except:
                    pass
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

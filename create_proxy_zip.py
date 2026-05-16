# create_proxy_zip.py
import os
import zipfile

project_name = "chatgpt-free-reverse-proxy-pi"

# main.py 전체 코드
main_py_content = """import asyncio
import os
import json
import random
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="ChatGPT Free Reverse Proxy",
    description="Raspberry Pi + Strong Cloudflare Bypass",
    version="3.0"
)

# Global variables
browser = None
context = None
page = None

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-4o"
    messages: list[ChatMessage]
    stream: bool = False

async def init_browser():
    global browser, context, page
    playwright = await async_playwright().start()

    launch_args = [
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-background-timer-throttling",
        "--window-size=1280,720",
    ]

    browser = await playwright.chromium.launch(
        headless=os.getenv("HEADLESS", "true").lower() == "true",
        args=launch_args,
        ignore_default_args=["--enable-automation"]
    )

    context = await browser.new_context(
        user_data_dir=os.path.join(DATA_DIR, "browser"),
        viewport={"width": 1280, "height": 720},
        user_agent="Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        locale="ko-KR",
        timezone_id="Asia/Seoul",
    )

    # Stealth Script
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko']});
    """)

    page = await context.new_page()
    await stealth_page(page)

    await page.goto("https://chat.openai.com", wait_until="domcontentloaded")
    await asyncio.sleep(random.uniform(4, 7))

    if await need_login(page):
        await auto_login(page)

    print("✅ ChatGPT Proxy Browser Initialized Successfully (Cloudflare Bypass)")

async def stealth_page(page):
    await page.evaluate("""() => {
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
    }""")

async def need_login(page):
    try:
        await page.wait_for_selector('button[data-testid="login-button"]', timeout=8000)
        return True
    except:
        return False

async def auto_login(page):
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    if not email or not password:
        print("⚠️ EMAIL and PASSWORD not set. Please login manually via VNC (port 7900).")
        return

    try:
        print("🔑 Trying auto login...")
        await page.click('button[data-testid="login-button"]')
        await asyncio.sleep(4)
        await page.fill('input[type="email"]', email)
        await page.click('button[type="submit"]')
        await asyncio.sleep(5)
        await page.fill('input[type="password"]', password)
        await page.click('button[type="submit"]')
        await asyncio.sleep(10)
        print("✅ Auto login successful")
    except Exception as e:
        print(f"❌ Auto login failed: {e}")

async def human_delay(min_sec=0.7, max_sec=2.3):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

async def send_message_and_stream(prompt: str) -> AsyncGenerator[str, None]:
    try:
        textarea = await page.wait_for_selector('textarea', timeout=20000)
        await textarea.fill(prompt)
        await human_delay()
        await page.keyboard.press('Enter')

        await page.wait_for_selector('div[data-message-author-role="assistant"]', timeout=60000)

        last_text = ""
        while True:
            responses = await page.query_selector_all('div[data-message-author-role="assistant"]')
            if responses:
                current_text = await responses[-1].inner_text()
                if len(current_text) > len(last_text):
                    delta = current_text[len(last_text):]
                    last_text = current_text
                    if delta.strip():
                        yield f"data: {json.dumps({'choices': [{'delta': {'content': delta}}]})} \n\n"

            # Stop 버튼이 없으면 응답 완료
            if not await page.query_selector('button[aria-label*="Stop generating"]'):
                break

            await asyncio.sleep(0.35)

        yield "data: [DONE]\\n\\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\\n\\n"

@app.on_event("startup")
async def startup():
    await init_browser()

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    if not page:
        raise HTTPException(503, "Browser is not ready yet")
    
    prompt = request.messages[-1].content

    if request.stream:
        return StreamingResponse(
            send_message_and_stream(prompt),
            media_type="text/event-stream"
        )
    else:
        full_response = ""
        async for chunk in send_message_and_stream(prompt):
            if "content" in chunk:
                try:
                    data = json.loads(chunk.split("data: ")[1])
                    full_response += data["choices"][0]["delta"].get("content", "")
                except:
                    pass
        return {
            "id": "chatcmpl-freeproxy",
            "object": "chat.completion",
            "model": request.model,
            "choices": [{"message": {"role": "assistant", "content": full_response}}]
        }

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "3.0", "message": "Cloudflare Bypass + Pi Optimized"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
"""

files = {
    "README.md": """# ChatGPT Free Reverse Proxy (Raspberry Pi + Cloudflare Bypass)

무료 ChatGPT 웹을 Playwright로 자동화하여 **OpenAI 호환 API**로 제공합니다.

### 주요 기능
- 자동 로그인 (Email + Password)
- Streaming 응답 (`stream=true`)
- Cloudflare 우회 강화 (Stealth)
- Raspberry Pi 최적화
- Swagger UI (`/docs`)

### 설치 및 실행
```bash
cp .env.example .env
# .env 파일 편집 (EMAIL, PASSWORD 입력)

docker compose up --build -d

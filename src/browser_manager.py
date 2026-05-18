import asyncio
import os
import json
import random
import logging
from typing import AsyncGenerator
from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

class BrowserManager:
    def __init__(self):
        self.context = None
        self.page = None

    async def init_browser(self):
        logger.info("Initializing Playwright browser...")
        playwright = await async_playwright().start()

        launch_args = [
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-background-networking",
            "--window-size=1280,720",
        ]

        logger.info(f"Launching persistent context at {os.path.join(DATA_DIR, 'browser')}")
        self.context = await playwright.chromium.launch_persistent_context(
            user_data_dir=os.path.join(DATA_DIR, "browser"),
            headless=os.getenv("HEADLESS", "true").lower() == "true",
            args=launch_args,
            ignore_default_args=["--enable-automation"],
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            locale="ko-KR",
            timezone_id="Asia/Seoul",
        )

        logger.info("Applying stealth scripts...")
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
        """)

        # launch_persistent_context creates a default page
        self.page = self.context.pages[0]
        await self.stealth_page()

        logger.info("Navigating to https://chatgpt.com...")
        await self.page.goto("https://chatgpt.com", wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(4, 7))

        if await self.need_login():
            logger.info("Login required. Initiating auto-login sequence.")
            await self.auto_login()
        else:
            logger.info("Session already logged in or login not required.")

        logger.info("✅ ChatGPT Proxy Browser Initialized Successfully")

    async def stealth_page(self):
        await self.page.evaluate("""() => {
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        }""")

    async def need_login(self):
        try:
            await self.page.wait_for_selector('button[data-testid="login-button"]', timeout=7000)
            return True
        except:
            return False

    async def auto_login(self):
        email = os.getenv("EMAIL")
        password = os.getenv("PASSWORD")
        if not email or not password:
            logger.warning("⚠️ EMAIL and PASSWORD not set. Please login manually.")
            return

        try:
            logger.info("🔑 Trying auto login...")
            await self.page.click('button[data-testid="login-button"]')
            await asyncio.sleep(4)
            
            logger.info("Entering email...")
            await self.page.fill('input[type="email"], #username, input[name="email"]', email)
            await asyncio.sleep(1)
            await self.page.keyboard.press('Enter')
            await asyncio.sleep(5)
            
            logger.info("Entering password...")
            await self.page.fill('input[type="password"], #password, input[name="password"]', password)
            await asyncio.sleep(1)
            await self.page.keyboard.press('Enter')
            await asyncio.sleep(10)
            
            logger.info("✅ Auto login successful")
        except Exception as e:
            logger.error(f"❌ Auto login failed: {e}")

    async def human_delay(self, min_sec=0.7, max_sec=2.3):
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def keep_alive(self):
        while True:
            await asyncio.sleep(1800)  # 30 minutes
            if self.page:
                try:
                    logger.info("🔄 Performing keep-alive page reload...")
                    await self.page.reload(wait_until="domcontentloaded")
                except Exception as e:
                    logger.warning(f"⚠️ Keep-alive reload failed: {e}")

    async def send_message_and_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        try:
            logger.info("Waiting for prompt textarea...")
            try:
                textarea = await self.page.wait_for_selector('#prompt-textarea', timeout=20000)
            except Exception:
                logger.warning("⚠️ Textarea not found. Trying to reload the page...")
                await self.page.reload(wait_until="domcontentloaded")
                await asyncio.sleep(5)
                if await self.need_login():
                    logger.info("Session expired or logged out. Re-initiating login.")
                    await self.auto_login()
                textarea = await self.page.wait_for_selector('#prompt-textarea', timeout=20000)

            logger.info("Inputting user prompt...")
            await textarea.fill(prompt)
            await self.human_delay()
            
            logger.info("Clicking send button...")
            try:
                await self.page.click('button[data-testid="send-button"]', timeout=3000)
            except:
                logger.info("Send button not found, pressing Enter instead.")
                await self.page.keyboard.press('Enter')

            logger.info("Waiting for assistant's response to start...")
            await self.page.wait_for_selector('div[data-message-author-role="assistant"]', timeout=60000)

            last_text = ""
            logger.info("Streaming response back to client...")
            while True:
                responses = await self.page.query_selector_all('div[data-message-author-role="assistant"]')
                if responses:
                    current_text = await responses[-1].inner_text()
                    if len(current_text) > len(last_text):
                        delta = current_text[len(last_text):]
                        last_text = current_text
                        if delta.strip():
                            yield f"data: {json.dumps({'choices': [{'delta': {'content': delta}}]})} \n\n"

                if not await self.page.query_selector('button[aria-label*="Stop generating"], button[data-testid="stop-button"]'):
                    send_button = await self.page.query_selector('button[data-testid="send-button"]')
                    if send_button:
                        logger.info("Response generation completed.")
                        break

                await asyncio.sleep(0.35)

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"❌ Error during message inference: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

# Global instance
browser_manager = BrowserManager()

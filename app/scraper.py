import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, BrowserContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import get_latest_post

load_dotenv()

SESSION_PATH = "truth_state.json"
LOGIN_URL = "https://truthsocial.com/login"
USERNAME = os.getenv("TRUTH_USER")
PASSWORD = os.getenv("TRUTH_PASS")

user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/69.0.3497.100 Safari/537.36"
)


async def human_typing(page: Page, selector: str, text: str, delay: float = 0.05):
    for char in text:
        await page.fill(selector, await page.input_value(selector) + char)
        await asyncio.sleep(delay)


async def login_and_save_session(context: BrowserContext):
    page = await context.new_page()
    await page.goto(LOGIN_URL, timeout=60000)
    # await page.screenshot(path="test.png", full_page=True)
    try:
        await page.click('button[data-testid="button"]', timeout=5000)
    except:
        pass

    await page.wait_for_selector('input[name="username"]', timeout=10000)
    await page.click('input[name="username"]')
    await human_typing(page, 'input[name="username"]', USERNAME)
    await page.click('input[name="password"]')
    await human_typing(page, 'input[name="password"]', PASSWORD)

    await page.click('button[type="submit"]')
    await page.wait_for_selector(".sr-only", timeout=30000)
    await context.storage_state(path=SESSION_PATH)
    await page.close()


async def ensure_logged_in(context: BrowserContext) -> bool:
    page = await context.new_page()
    await page.goto("https://truthsocial.com/home", timeout=30000)
    try:
        await page.click('button[data-testid="button"]', timeout=5000)
    except:
        pass
    if await page.query_selector('input[name="username"]'):
        print("[INFO] Not logged in. Will log in again.")
        await page.close()
        return True
    else:
        print("[INFO] Already logged in with session.")
        await page.close()
        return False


async def scrape_latest_post(profile_url: str, session: AsyncSession):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=50)

        context = None
        if os.path.exists(SESSION_PATH):
            context = await browser.new_context(storage_state=SESSION_PATH, user_agent=user_agent)
            if await ensure_logged_in(context):
                await context.close()
                context = await browser.new_context(user_agent=user_agent)
                await login_and_save_session(context)
        else:
            context = await browser.new_context(user_agent=user_agent)
            await login_and_save_session(context)

        await context.close()
        context = await browser.new_context(storage_state=SESSION_PATH, user_agent=user_agent)
        page = await context.new_page()

        await page.goto(profile_url, timeout=60000)
        await page.wait_for_selector(".status__wrapper", timeout=20000)

        wrapper = await page.query_selector(".status__wrapper")
        if not wrapper:
            raise Exception("No latest post found")

        data_id = await wrapper.get_attribute("data-id")
        timestamp_el = await wrapper.query_selector("time")
        timestamp = await timestamp_el.get_attribute("title") if timestamp_el else None
        parsed_timestamp = datetime.strptime(timestamp, "%b %d, %Y, %I:%M %p")

        latest_post = await get_latest_post(session)
        if latest_post and latest_post.id == data_id:
            print("[INFO] No new post. Exiting scrape.")
            await browser.close()
            return None

        content_el = await wrapper.query_selector(".status__content-wrapper p")
        content = (await content_el.text_content()).strip() if content_el else None

        await browser.close()

        return {
            "id": data_id,
            "timestamp": parsed_timestamp,
            "content": content,
            "url": profile_url,
        }

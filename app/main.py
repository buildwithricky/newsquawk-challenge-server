from fastapi import FastAPI, Request, Depends
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import asyncio
import json
from sqlalchemy import select, desc
from fastapi.middleware.cors import CORSMiddleware
from app.scraper import scrape_latest_post
from app.db import AsyncSessionLocal, get_db
from app.crud import create_truth
from app.models import Truth
from app.schemas import TruthCreate, TruthOut
from typing import List

SCRAPE_INTERVAL = 30  
truth_stream_subscribers: list[asyncio.Queue] = []
origins = ["*"] 
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(periodic_scraper())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("[SCRAPER] Background scraper cancelled.")

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            
    allow_credentials=True,
    allow_methods=["*"],            
    allow_headers=["*"],
)

@app.get("/truths", response_model=List[TruthOut])
async def get_recent_truths(db=Depends(get_db)):
    stmt = select(Truth).order_by(desc(Truth.timestamp)).limit(20)
    result = await db.execute(stmt)
    return result.scalars().all()

@app.get("/stream")
async def stream_truths(request: Request):
    client_queue = asyncio.Queue()
    truth_stream_subscribers.append(client_queue)
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                truth = await client_queue.get()
                print(truth)
                yield f"data: {json.dumps(truth)}\n\n"
        finally:
            truth_stream_subscribers.remove(client_queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

async def periodic_scraper():
    profile_url = "https://truthsocial.com/@realDonaldTrump"
    print("[SCRAPER] Starting background scraper...")

    while True:
        try:
            async with AsyncSessionLocal() as db:
                post_data = await scrape_latest_post(profile_url, db)

                if not post_data:
                    print("[SCRAPER] No new post to save.")
                else:
                    truth = TruthCreate(**post_data)
                    db_obj = Truth(**truth.model_dump())
                    db.add(db_obj)
                    await db.commit()
                    print("[SCRAPER] Scraped and saved post:", post_data)

                    # Convert timestamp to string before broadcasting
                    truth_out = TruthOut(**post_data)
                    truth_dict = truth_out.model_dump()
                    truth_dict["timestamp"] = truth_dict["timestamp"].isoformat()

                    for queue in truth_stream_subscribers:
                        await queue.put(truth_dict)

        except Exception as e:
            print(f"[SCRAPER] Error: {e}")

        await asyncio.sleep(SCRAPE_INTERVAL)

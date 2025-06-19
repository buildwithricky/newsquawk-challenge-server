from sqlalchemy import select,desc
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Truth
from .schemas import TruthCreate

async def get_truth_by_data_id(db: AsyncSession, id: str):
    result = await db.execute(select(Truth).where(Truth.data_id == id))
    return result.scalars().first()

async def create_truth(db: AsyncSession, truth: TruthCreate):
    existing = await get_truth_by_data_id(db, truth.id)
    # Check if exists in db first
    if existing:
        return existing
    db_truth = Truth(**truth.model_dump())
    db.add(db_truth)
    await db.commit()
    await db.refresh(db_truth)
    return db_truth


async def get_latest_post(session: AsyncSession):
    stmt = select(Truth).order_by(desc(Truth.timestamp)).limit(1)
    result = await session.execute(stmt)
    latest_post = result.scalar_one_or_none()
    return latest_post

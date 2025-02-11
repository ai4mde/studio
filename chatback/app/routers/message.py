from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import MessageModel, MessageResponse
from app.database import get_db

router = APIRouter()

@router.get("/messages/", response_model=list[MessageResponse])
async def get_messages(db: AsyncSession = Depends(get_db)):
    query = select(MessageModel)
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return [MessageResponse.from_orm(msg) for msg in messages] 
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.resources import DashboardOverview
from app.services.resources import get_counts

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview, summary="Get persisted dashboard counts")
async def overview(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> DashboardOverview:
    return DashboardOverview(**await get_counts(db, user))

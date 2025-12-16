from fastapi import APIRouter, Depends
from ..domain import schemas
from ..repositories.interfaces import IStatsReader
from ..core.dependencies import get_stats_repository

router = APIRouter(
    prefix="/api/stats",
    tags=["stats"]
)

@router.get("", response_model=schemas.DashboardStats)
def read_dashboard_stats(stats_reader: IStatsReader = Depends(get_stats_repository)):
    return stats_reader.get_dashboard_stats()

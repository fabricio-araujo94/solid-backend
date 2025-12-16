from typing import Protocol, List, Optional, runtime_checkable
from ..domain import schemas, models

# --- Part Interfaces ---

@runtime_checkable
class IPartReader(Protocol):
    def get_part(self, part_id: int) -> Optional[models.Part]:
        ...

    def get_part_by_sku(self, sku: str) -> Optional[models.Part]:
        ...

    def get_parts(self, skip: int = 0, limit: int = 100) -> List[models.Part]:
        ...

@runtime_checkable
class IPartWriter(Protocol):
    def create_part(self, part: schemas.PartCreate) -> models.Part:
        ...

    def delete_part(self, part_id: int) -> Optional[models.Part]:
        ...

@runtime_checkable
class IPartRepository(IPartReader, IPartWriter, Protocol):
    """
    Full repository interface combining read and write operations.
    """
    ...

# --- Job Interfaces ---

@runtime_checkable
class IJobRetriever(Protocol):
    def get_job(self, job_id: int) -> Optional[models.ComparisonJob]:
        ...

@runtime_checkable
class IJobSearcher(Protocol):
    def get_jobs_by_part(self, part_id: int) -> List[models.ComparisonJob]:
        ...

@runtime_checkable
class IJobCreator(Protocol):
    def create_job(self, job: schemas.ComparisonJobCreate) -> models.ComparisonJob:
        ...

@runtime_checkable
class IJobUpdater(Protocol):
    def update_job_status(self, job_id: int, status: str, output_url: Optional[str] = None) -> Optional[models.ComparisonJob]:
        ...

@runtime_checkable
class IJobRepository(IJobRetriever, IJobSearcher, IJobCreator, IJobUpdater, Protocol):
    """
    Full repository interface combining all job operations.
    """
    ...

# --- Stats Interfaces ---

@runtime_checkable
class IStatsReader(Protocol):
    def get_dashboard_stats(self) -> dict:
        ...

@runtime_checkable
class IStatsRepository(IStatsReader, Protocol):
    """
    Full repository interface for stats.
    """
    ...

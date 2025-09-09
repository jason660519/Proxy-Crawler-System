from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime


class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    canceled = "canceled"


@dataclass
class JobResult:
    job_id: str
    status: JobStatus
    url: Optional[str] = None
    files: List[Dict[str, Any]] = field(default_factory=list)
    checksum: Optional[str] = None
    engine: Optional[str] = None
    processing_time_ms: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    error: Optional[str] = None



"""URL2Parquet 模組初始化

提供 URL → Fetch → Extract → Transform → Output (Parquet/CSV/JSON/MD) 的管線能力。
此模組為 html_to_markdown 的後續替代方案，並提供相容層逐步遷移。
"""

from .config import PipelineOptions
from .types import JobStatus, JobResult

__all__ = [
    "PipelineOptions",
    "JobStatus",
    "JobResult",
]

"""url2parquet package initialization"""

__all__ = [
    "config",
    "types",
]



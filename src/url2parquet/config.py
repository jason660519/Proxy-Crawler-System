from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PipelineOptions:
    urls: List[str]
    engine: str = "smart"
    output_formats: List[str] = field(default_factory=lambda: ["parquet"])  # parquet|csv|json|md
    work_dir: str = "data/url2parquet"
    obey_robots_txt: bool = True
    timeout_seconds: int = 20
    max_concurrency: int = 4
    compression: Optional[str] = "snappy"  # parquet default
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )


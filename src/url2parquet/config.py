from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class PipelineOptions:
    output_formats: List[str] = field(default_factory=lambda: ["parquet"])  # parquet,csv,json,md
    work_dir: Path = Path("data")
    cache_enabled: bool = True
    cache_ttl: int = 86400
    max_concurrent: int = 5
    request_timeout: int = 30
    extract_mode: str = "smart"  # smart|full_html|trafilatura
    clean_ads: bool = True
    absolutize_links: bool = True
    detect_language: bool = True
    parquet_compression: str = "snappy"
    user_agent: str = "url2parquet/1.0"



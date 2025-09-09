from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class OutputFile:
    format: str
    path: str
    size: Optional[int] = None
    rows: Optional[int] = None


@dataclass
class ConvertResult:
    url: str
    title: Optional[str] = None
    language: Optional[str] = None
    files: List[OutputFile] = field(default_factory=list)
    checksum: Optional[str] = None
    engine: Optional[str] = None
    processing_time_ms: Optional[int] = None
    warnings: List[str] = field(default_factory=list)
    extra: Dict[str, object] = field(default_factory=dict)



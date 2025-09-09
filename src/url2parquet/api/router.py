from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..config import PipelineOptions
from ..core.pipeline import Url2ParquetPipeline


class JobCreateRequest(BaseModel):
    url: Optional[str] = Field(None, description="單一 URL")
    urls: Optional[List[str]] = Field(None, description="多個 URL")
    options: Optional[Dict] = Field(default_factory=dict)


router = APIRouter(prefix="/api/url2parquet", tags=["url2parquet"])

_pipeline = Url2ParquetPipeline(PipelineOptions())


@router.post("/jobs")
def create_job(req: JobCreateRequest) -> Dict:
    if not req.url and not req.urls:
        raise HTTPException(status_code=400, detail="url 或 urls 必須提供其一")

    options = PipelineOptions(**(req.options or {}))
    pipeline = Url2ParquetPipeline(options)

    if req.url:
        result = pipeline.convert_url(req.url)
        return {"job_id": "job_inline", "status": "completed", "result": result.__dict__}
    else:
        results = [r.__dict__ for r in pipeline.batch_convert(req.urls or [])]
        return {"job_id": "job_inline_batch", "status": "completed", "results": results}


@router.get("/health")
def health() -> Dict:
    return {"status": "healthy"}



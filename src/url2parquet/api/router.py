from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time

from ..config import PipelineOptions
from ..types import JobStatus, JobResult
from ..core.pipeline import Url2ParquetPipeline
from ..core.cache import FileCache
from ..checksum import compute_checksum
import httpx


router = APIRouter(prefix="/api/url2parquet", tags=["URL2Parquet"])

_jobs: Dict[str, JobResult] = {}


class CreateJobRequest(BaseModel):
    # 新後端格式（推薦）
    urls: Optional[List[str]] = None
    engine: Optional[str] = "smart"
    output_formats: Optional[List[str]] = ["parquet"]
    obey_robots_txt: Optional[bool] = True
    timeout_seconds: Optional[int] = 20
    max_concurrency: Optional[int] = 4
    work_dir: Optional[str] = "data/url2parquet"

    # 舊前端相容層
    url: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


@router.post("/jobs")
async def create_job(req: CreateJobRequest) -> Dict[str, Any]:
    job_id = f"job_{int(time.time()*1000)}"
    _jobs[job_id] = JobResult(job_id=job_id, status=JobStatus.queued)

    # 相容處理：支援 {url, options:{output_formats}} 舊格式
    urls_list: List[str] = []
    if req.urls:
        urls_list = req.urls
    elif req.url:
        urls_list = [req.url]

    # 合併 options 與頂層欄位
    effective_formats = req.output_formats or []
    if req.options and isinstance(req.options, dict):
        if isinstance(req.options.get("output_formats"), list):
            effective_formats = req.options.get("output_formats")

    options = PipelineOptions(
        urls=urls_list,
        engine=req.engine or "smart",
        output_formats=effective_formats or ["parquet"],
        obey_robots_txt=bool(req.obey_robots_txt),
        timeout_seconds=int(req.timeout_seconds or 20),
        max_concurrency=int(req.max_concurrency or 4),
        work_dir=req.work_dir or "data/url2parquet",
    )

    cache = FileCache(options.work_dir)
    pipeline = Url2ParquetPipeline(options)

    # Process URLs and handle redirects
    _jobs[job_id].status = JobStatus.processing
    try:
        if not options.urls:
            raise ValueError("No URL provided")
        
        # Process all URLs
        results = []
        redirects = []
        
        for url in options.urls:
            try:
                checksum = compute_checksum(url, vars(options)).replace("sha256:", "")
                cached = cache.hit(checksum)
                
                if cached:
                    print(f"📦 使用快取結果: {url}")
                    result = cached
                else:
                    print(f"🌐 處理新URL: {url}")
                    result = await pipeline.process_single(url)
                    print(f"💾 儲存結果到快取: {result}")
                    cache.save(checksum, result)
                
                # Check if URL was redirected
                print(f"🔍 檢查URL {url} 的結果: {result}")
                if result.get("status") == "redirected":
                    print(f"🔄 檢測到重定向: {result}")
                    redirects.append(result)
                else:
                    print(f"✅ 正常結果: {result}")
                    results.append(result)
            except httpx.HTTPStatusError as e:
                # 專門處理httpx HTTP錯誤
                if e.response.status_code in [301, 302, 303, 307, 308]:
                    redirect_url = e.response.headers.get("location")
                    if redirect_url:
                        redirect_result = {
                            "url": url,
                            "status": "redirected",
                            "original_url": url,
                            "final_url": redirect_url,
                            "message": f"URL已跳轉至 {redirect_url}，是否繼續測試新的URL？"
                        }
                        redirects.append(redirect_result)
                        print(f"🔄 檢測到HTTP重定向 {url} -> {redirect_url}")
                        continue
                print(f"HTTP錯誤 {url}: {e}")
                continue
            except Exception as e:
                # 檢查錯誤是否包含重定向信息
                error_msg = str(e)
                if "Redirect response" in error_msg and "Redirect location:" in error_msg:
                    # 從錯誤訊息中提取重定向URL
                    import re
                    match = re.search(r"Redirect location: '([^']+)'", error_msg)
                    if match:
                        redirect_url = match.group(1)
                        redirect_result = {
                            "url": url,
                            "status": "redirected",
                            "original_url": url,
                            "final_url": redirect_url,
                            "message": f"URL已跳轉至 {redirect_url}，是否繼續測試新的URL？"
                        }
                        redirects.append(redirect_result)
                        print(f"🔄 檢測到重定向 {url} -> {redirect_url}")
                        continue
                
                # 如果單個URL處理失敗，記錄錯誤但繼續處理其他URL
                print(f"處理URL {url} 時出錯: {e}")
                continue

        # If there are redirects, return redirect information
        if redirects:
            return {
                "job_id": job_id,
                "status": "redirected",
                "redirects": redirects,
                "message": "檢測到URL重定向，請確認是否繼續"
            }

        # Process successful results
        if results:
            result = results[0]  # Use first successful result
            _jobs[job_id].status = JobStatus.completed
            _jobs[job_id].url = result.get("url", options.urls[0])
            _jobs[job_id].checksum = result.get("checksum")
            _jobs[job_id].files = result.get("files", [])
            _jobs[job_id].engine = result.get("engine")
            _jobs[job_id].processing_time_ms = result.get("processing_time_ms")
            
            return {
                "job_id": job_id,
                "status": "completed",
                "result": {
                    "files": result.get("files", [])
                }
            }
        else:
            raise ValueError("No successful results")

    except Exception as e:
        _jobs[job_id].status = JobStatus.failed
        _jobs[job_id].error = str(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_job(job_id: str) -> JobResult:
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@router.get("/jobs/{job_id}/download")
async def download_info(job_id: str) -> Dict[str, Any]:
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return {"files": job.files}


@router.get("/jobs/{job_id}/files/{format}")
async def get_file_content(job_id: str, format: str) -> Dict[str, Any]:
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    
    # 找到對應格式的文件
    file_info = None
    for file in job.files:
        if file.get("format") == format:
            file_info = file
            break
    
    if not file_info:
        raise HTTPException(status_code=404, detail=f"file with format {format} not found")
    
    try:
        # 讀取文件內容
        with open(file_info["path"], "r", encoding="utf-8") as f:
            content = f.read()
        
        return {
            "format": format,
            "content": content,
            "size": file_info.get("size", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.post("/jobs/{job_id}/confirm-redirect")
async def confirm_redirect(job_id: str, redirect_urls: List[str]) -> Dict[str, Any]:
    """確認重定向並使用新的URL重新處理"""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    
    if job.status != JobStatus.processing:
        raise HTTPException(status_code=400, detail="job not in processing state")
    
    try:
        # 重新處理重定向的URL
        options = PipelineOptions(
            urls=redirect_urls,
            engine="smart",
            output_formats=["md", "json", "parquet"],
            obey_robots_txt=True,
            timeout_seconds=30,
            max_concurrency=4,
            work_dir="data/url2parquet",
        )
        
        cache = FileCache(options.work_dir)
        pipeline = Url2ParquetPipeline(options)
        
        results = []
        for url in redirect_urls:
            checksum = compute_checksum(url, vars(options)).replace("sha256:", "")
            cached = cache.hit(checksum)
            
            if cached:
                result = cached
            else:
                result = await pipeline.process_single(url)
                cache.save(checksum, result)
            
            results.append(result)
        
        # 更新任務狀態
        if results:
            result = results[0]
            _jobs[job_id].status = JobStatus.completed
            _jobs[job_id].url = result.get("url", redirect_urls[0])
            _jobs[job_id].checksum = result.get("checksum")
            _jobs[job_id].files = result.get("files", [])
            _jobs[job_id].engine = result.get("engine")
            _jobs[job_id].processing_time_ms = result.get("processing_time_ms")
            
            return {
                "job_id": job_id,
                "status": "completed",
                "result": {
                    "files": result.get("files", [])
                }
            }
        else:
            raise ValueError("No successful results")
            
    except Exception as e:
        _jobs[job_id].status = JobStatus.failed
        _jobs[job_id].error = str(e)
        raise HTTPException(status_code=500, detail=str(e))


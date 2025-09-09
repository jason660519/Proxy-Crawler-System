import time
from pathlib import Path
from typing import Dict, Any

import httpx

from ..config import PipelineOptions
from ..checksum import compute_checksum


class Url2ParquetPipeline:
    def __init__(self, options: PipelineOptions):
        self.options = options
        self.base = Path(options.work_dir)
        (self.base / "jobs").mkdir(parents=True, exist_ok=True)

    async def process_single(self, url: str) -> Dict[str, Any]:
        started = time.time()
        checksum = compute_checksum(url, vars(self.options)).replace("sha256:", "")

        # Fetch with redirect handling - 確保永遠不會拋出httpx錯誤
        html = None
        final_url = url
        
        try:
            async with httpx.AsyncClient(
                timeout=self.options.timeout_seconds,
                follow_redirects=False,  # 不自動跟隨重定向
                max_redirects=0
            ) as client:
                resp = await client.get(url, headers={"User-Agent": self.options.user_agent})
                
                # 檢查重定向狀態碼
                if resp.status_code in [301, 302, 303, 307, 308]:
                    redirect_url = resp.headers.get("location")
                    if redirect_url:
                        # 確保重定向URL是完整的
                        if redirect_url.startswith('/'):
                            from urllib.parse import urljoin
                            redirect_url = urljoin(url, redirect_url)
                        
                        return {
                            "status": "redirected",
                            "original_url": url,
                            "final_url": redirect_url,
                            "message": f"URL已跳轉至 {redirect_url}，是否繼續測試新的URL？"
                        }
                
                # 只有在非重定向狀態碼時才檢查狀態
                if resp.status_code not in [301, 302, 303, 307, 308]:
                    resp.raise_for_status()
                html = resp.text
                final_url = str(resp.url)
                
                # Check if URL was redirected (即使狀態碼不是重定向)
                if final_url != url:
                    return {
                        "status": "redirected",
                        "original_url": url,
                        "final_url": final_url,
                        "message": f"URL已跳轉至 {final_url}，是否繼續測試新的URL？"
                    }
                        
        except Exception as e:
            # 統一處理所有錯誤，包括httpx錯誤
            error_msg = str(e)
            print(f"🔍 處理URL {url} 時發生錯誤: {error_msg}")
            
            # 檢查是否為重定向錯誤
            if ("Redirect response" in error_msg and "Redirect location:" in error_msg) or \
               ("301" in error_msg or "302" in error_msg or "303" in error_msg or "307" in error_msg or "308" in error_msg):
                # 從錯誤訊息中提取重定向URL
                import re
                match = re.search(r"Redirect location: '([^']+)'", error_msg)
                if match:
                    redirect_url = match.group(1)
                    return {
                        "status": "redirected",
                        "original_url": url,
                        "final_url": redirect_url,
                        "message": f"URL已跳轉至 {redirect_url}，是否繼續測試新的URL？"
                    }
            
            # 檢查是否為httpx.HTTPStatusError
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                if e.response.status_code in [301, 302, 303, 307, 308]:
                    redirect_url = e.response.headers.get("location")
                    if redirect_url:
                        # 確保重定向URL是完整的
                        if redirect_url.startswith('/'):
                            from urllib.parse import urljoin
                            redirect_url = urljoin(url, redirect_url)
                        
                        return {
                            "status": "redirected",
                            "original_url": url,
                            "final_url": redirect_url,
                            "message": f"URL已跳轉至 {redirect_url}，是否繼續測試新的URL？"
                        }
            
            # 如果不是重定向錯誤，則拋出
            raise
        
        # 如果沒有獲取到HTML，則返回錯誤
        if html is None:
            raise ValueError(f"無法獲取URL內容: {url}")

        # Transform: trivial extract to markdown via markdownify if available; else plain text fallback
        try:
            from markdownify import markdownify

            markdown = markdownify(html)
        except Exception:
            # naive fallback
            markdown = html

        # Output: write minimal files according to formats
        files = []
        out_dir = self.base / "outputs"
        out_dir.mkdir(parents=True, exist_ok=True)

        if "md" in self.options.output_formats or "markdown" in self.options.output_formats:
            md_path = out_dir / f"{checksum[7:15]}_content.md"
            md_path.write_text(markdown, encoding="utf-8")
            files.append({"format": "md", "path": str(md_path), "size": md_path.stat().st_size})

        if "json" in self.options.output_formats:
            import json

            json_path = out_dir / f"{checksum[7:15]}_content.json"
            json_path.write_text(
                json.dumps({"url": url, "markdown": markdown}, ensure_ascii=False),
                encoding="utf-8",
            )
            files.append({"format": "json", "path": str(json_path), "size": json_path.stat().st_size})

        # CSV output (optional)
        if "csv" in self.options.output_formats:
            try:
                import pandas as pd  # type: ignore

                csv_path = out_dir / f"{checksum[7:15]}_content.csv"
                row = {
                    "url": url,
                    "markdown": markdown,
                    "engine": self.options.engine,
                    "checksum": checksum,
                    "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
                    "content_length": len(html or ""),
                }
                pd.DataFrame([row]).to_csv(csv_path, index=False)
                files.append({"format": "csv", "path": str(csv_path), "size": csv_path.stat().st_size})
            except Exception as e:
                print(f"CSV 輸出失敗: {e}")

        # Parquet output (optional)
        if "parquet" in self.options.output_formats:
            try:
                import pandas as pd  # type: ignore

                parquet_path = out_dir / f"{checksum[7:15]}_content.parquet"
                row = {
                    "url": url,
                    "markdown": markdown,
                    "engine": self.options.engine,
                    "checksum": checksum,
                    "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
                    "content_length": len(html or ""),
                }
                # 使用 pyarrow 引擎寫入 Parquet
                pd.DataFrame([row]).to_parquet(parquet_path, index=False, engine="pyarrow")
                files.append({"format": "parquet", "path": str(parquet_path), "size": parquet_path.stat().st_size})
            except Exception as e:
                print(f"Parquet 輸出失敗: {e}")

        elapsed_ms = int((time.time() - started) * 1000)
        return {
            "url": url,
            "files": files,
            "checksum": checksum,
            "engine": self.options.engine,
            "processing_time_ms": elapsed_ms,
        }


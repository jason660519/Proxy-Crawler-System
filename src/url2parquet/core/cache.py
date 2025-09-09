from pathlib import Path
import json
from typing import Dict, Any, Optional


class FileCache:
    def __init__(self, work_dir: str):
        self.base = Path(work_dir)
        self.cache_dir = self.base / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def hit(self, checksum: str) -> Optional[Dict[str, Any]]:
        meta = self.cache_dir / checksum / "result.json"
        if meta.exists():
            try:
                return json.loads(meta.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None

    def save(self, checksum: str, result: Dict[str, Any]) -> None:
        target_dir = self.cache_dir / checksum
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )



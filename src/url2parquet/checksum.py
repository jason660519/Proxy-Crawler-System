import hashlib
import json
from typing import Any, Dict


def compute_checksum(url: str, options: Dict[str, Any]) -> str:
    canonical = {
        "url": url.strip(),
        "engine": options.get("engine"),
        "formats": sorted(options.get("output_formats", [])),
        "obey_robots": bool(options.get("obey_robots_txt", True)),
    }
    payload = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()



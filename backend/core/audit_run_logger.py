import hashlib
import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import fcntl  # type: ignore
except Exception:  # pragma: no cover - non-POSIX fallback
    fcntl = None

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_PATH = PROJECT_ROOT / "paper" / "data" / "audit_runs.jsonl"
VERSION_PATH = PROJECT_ROOT / "VERSION"

_APPEND_LOCK = threading.Lock()
_PIPELINE_VERSION_CACHE: Optional[str] = None


def normalize_mode(mode: Optional[str]) -> str:
    mode_norm = (mode or "research").strip().lower()
    return "demo" if mode_norm == "demo" else "research"


def read_pipeline_version() -> str:
    global _PIPELINE_VERSION_CACHE
    if _PIPELINE_VERSION_CACHE is not None:
        return _PIPELINE_VERSION_CACHE

    if not VERSION_PATH.exists():
        _PIPELINE_VERSION_CACHE = "unknown"
        return _PIPELINE_VERSION_CACHE

    try:
        for line in VERSION_PATH.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                _PIPELINE_VERSION_CACHE = stripped
                return _PIPELINE_VERSION_CACHE
    except Exception:
        logger.exception("Failed to read VERSION file at %s", VERSION_PATH)

    _PIPELINE_VERSION_CACHE = "unknown"
    return _PIPELINE_VERSION_CACHE


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_audit_record(
    input_text: str,
    mode: Optional[str],
    result: Dict[str, Any],
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    result_obj = result if isinstance(result, dict) else {"raw_result": result}

    record: Dict[str, Any] = {
        "run_id": str(uuid.uuid4()),
        "ts_iso": _utc_now_iso(),
        "mode": normalize_mode(mode),
        "input_text": input_text,
        "input_chars": len(input_text),
        "input_sha256": _sha256_text(input_text),
        "pipeline_version": read_pipeline_version(),
        "result": result_obj,
        "overall_risk": result_obj.get("overall_risk"),
        "hallucination_score": result_obj.get("hallucination_score"),
        "summary": result_obj.get("summary"),
        "timings_ms": result_obj.get("debug_timings_ms") if isinstance(result_obj.get("debug_timings_ms"), dict) else None,
    }
    if extra_metadata:
        for key, value in extra_metadata.items():
            if key not in record:
                record[key] = value
    return record


class AuditRunLogger:
    def __init__(self, log_path: Path = DEFAULT_LOG_PATH):
        self.log_path = Path(log_path)

    def append_record(self, record: Dict[str, Any]) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False, default=str) + "\n"
        encoded = line.encode("utf-8")

        with _APPEND_LOCK:
            with open(self.log_path, "ab") as handle:
                if fcntl is not None:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    handle.write(encoded)
                    handle.flush()
                    os.fsync(handle.fileno())
                finally:
                    if fcntl is not None:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def log_run(
        self,
        input_text: str,
        mode: Optional[str],
        result: Dict[str, Any],
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            record = build_audit_record(
                input_text=input_text,
                mode=mode,
                result=result,
                extra_metadata=extra_metadata,
            )
            self.append_record(record)
        except Exception:
            logger.exception("Failed to append audit run log.")

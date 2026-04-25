import hashlib
import json
import datetime
from pathlib import Path
from typing import Any


def compute_config_hash(config_dict: dict) -> str:
    """Deterministic hash of the configuration"""
    canonical = json.dumps(config_dict, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def create_audit_record(
    skill_name: str,
    config_dict: dict,
    results: Any,
    outputs_dir: str,
) -> dict:
    """
    Tamper-evident audit record linking config  results.
    Anyone can independently verify by re-hashing.
    """
    config_hash = compute_config_hash(config_dict)
    results_str = json.dumps(results, sort_keys=True, default=str)
    results_hash = hashlib.sha256(results_str.encode()).hexdigest()

    # Chain them together for a combined integrity proof
    combined = f"{config_hash}:{results_hash}"
    execution_hash = hashlib.sha256(combined.encode()).hexdigest()

    timestamp = datetime.datetime.now(datetime.timezone.utc)

    record = {
        "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "skill": skill_name,
        "config_hash_sha256": config_hash,
        "results_hash_sha256": results_hash,
        "execution_hash_sha256": execution_hash,
        "config_snapshot": config_dict,
        "results_snapshot": results,
        "verification_method": (
            "SHA-256(config) + SHA-256(results) -> SHA-256(combined)"
        ),
    }

    # Persist
    audit_dir = Path(outputs_dir) / "audit_trail"
    audit_dir.mkdir(parents=True, exist_ok=True)
    ts_safe = record["timestamp"].replace(":", "-")
    short_hash = execution_hash[:8]                          # ← FIX 1: indented
    audit_file = audit_dir / f"audit_{skill_name}_{ts_safe}_{short_hash}.json"
    audit_file.write_text(
        json.dumps(record, indent=2, default=str),           # ← FIX 2: indented
        encoding="utf-8",                                    # ← FIX 2: indented
    )                                                        # ← FIX 2: indented

    print(f"[Audit]  Record saved: {audit_file}")
    print(f"[Audit]    Config hash:    {config_hash[:16]}...")
    print(f"[Audit]    Execution hash: {execution_hash[:16]}...")

    return record
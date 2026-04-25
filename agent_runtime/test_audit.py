import hashlib
import json
import shutil
from pathlib import Path
from agent_runtime.audit import compute_config_hash, create_audit_record


def test_create_audit_record():
    """Verify the hash chain is correct and the audit file is persisted."""
    test_config = {"backend": "ibm_brisbane", "shots": 4096, "optimization_level": 3}
    test_results = {"counts": {"00": 2048, "11": 2048}, "fidelity": 0.97}
    outputs_dir = "./test_outputs"

    record = create_audit_record(
        skill_name="bell_state_test",
        config_dict=test_config,
        results=test_results,
        outputs_dir=outputs_dir,
    )

    # 1. Independently recompute the hash chain
    recomputed_config_hash = compute_config_hash(test_config)
    recomputed_results_hash = hashlib.sha256(
        json.dumps(test_results, sort_keys=True, default=str).encode()
    ).hexdigest()
    recomputed_exec = hashlib.sha256(
        f"{recomputed_config_hash}:{recomputed_results_hash}".encode()
    ).hexdigest()

    assert record["config_hash_sha256"] == recomputed_config_hash
    assert record["results_hash_sha256"] == recomputed_results_hash
    assert record["execution_hash_sha256"] == recomputed_exec

    # 2. Verify the audit file was actually written
    audit_dir = Path(outputs_dir) / "audit_trail"
    audit_files = list(audit_dir.glob("audit_bell_state_test_*.json"))
    assert len(audit_files) >= 1

    # 3. Verify the saved file content matches
    saved = json.loads(audit_files[-1].read_text(encoding="utf-8"))
    assert saved["execution_hash_sha256"] == recomputed_exec

    print("✅ All checks passed!")

    # Cleanup
    shutil.rmtree(outputs_dir, ignore_errors=True)


if __name__ == "__main__":
    test_create_audit_record()

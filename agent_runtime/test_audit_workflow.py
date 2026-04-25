import hashlib
import json
import shutil
import copy
from pathlib import Path
import pytest

from agent_runtime.audit import compute_config_hash, create_audit_record


# ──────────────────────────────────────────────
# Shared fixtures
# ──────────────────────────────────────────────

OUTPUTS_DIR = "./test_workflow_outputs"

@pytest.fixture
def sample_config():
    return {
        "backend": "ibm_brisbane",
        "shots": 4096,
        "optimization_level": 3,
        "circuit_depth": 12,
    }

@pytest.fixture
def sample_results():
    return {
        "counts": {"00": 2048, "11": 2048},
        "fidelity": 0.97,
        "execution_time_ms": 342,
    }

@pytest.fixture
def audit_record(sample_config, sample_results):
    """Generate a real audit record for testing."""
    record = create_audit_record(
        skill_name="workflow_test",
        config_dict=sample_config,
        results=sample_results,
        outputs_dir=OUTPUTS_DIR,
    )
    yield record
    # Cleanup after all tests using this fixture
    shutil.rmtree(OUTPUTS_DIR, ignore_errors=True)


# ──────────────────────────────────────────────
# PRINCIPLE 1: Config Integrity
# ──────────────────────────────────────────────

class TestConfigIntegrity:
    """Any modification to config must produce a different hash."""

    def test_config_hash_is_deterministic(self, sample_config):
        """Same config → same hash, every single time."""
        hash1 = compute_config_hash(sample_config)
        hash2 = compute_config_hash(sample_config)
        assert hash1 == hash2, "Identical configs must produce identical hashes"

    def test_config_hash_changes_on_modification(self, sample_config):
        """Even a tiny change must break the hash."""
        original_hash = compute_config_hash(sample_config)

        # Tamper: change shots by just 1
        tampered = copy.deepcopy(sample_config)
        tampered["shots"] = 4097

        tampered_hash = compute_config_hash(tampered)
        assert original_hash != tampered_hash, "Modified config must produce different hash"

    def test_config_hash_is_key_order_independent(self, sample_config):
        """Dict key order must NOT affect the hash (deterministic serialization)."""
        reversed_config = dict(reversed(list(sample_config.items())))
        assert compute_config_hash(sample_config) == compute_config_hash(reversed_config)

    def test_config_snapshot_matches_original(self, sample_config, audit_record):
        """The stored snapshot must exactly match what was passed in."""
        assert audit_record["config_snapshot"] == sample_config


# ──────────────────────────────────────────────
# PRINCIPLE 2: Results Integrity
# ──────────────────────────────────────────────

class TestResultsIntegrity:
    """Any modification to results must be detectable."""

    def test_results_hash_matches_independent_computation(
        self, sample_results, audit_record
    ):
        """Recompute the results hash from scratch and compare."""
        results_str = json.dumps(sample_results, sort_keys=True, default=str)
        expected_hash = hashlib.sha256(results_str.encode()).hexdigest()
        assert audit_record["results_hash_sha256"] == expected_hash

    def test_tampered_results_detected(self, sample_results, audit_record):
        """If someone changes even one count, the hash must differ."""
        tampered = copy.deepcopy(sample_results)
        tampered["counts"]["00"] = 9999  # Tamper!

        tampered_str = json.dumps(tampered, sort_keys=True, default=str)
        tampered_hash = hashlib.sha256(tampered_str.encode()).hexdigest()

        assert tampered_hash != audit_record["results_hash_sha256"], (
            "Tampered results must NOT match the original hash"
        )

    def test_results_snapshot_matches_original(self, sample_results, audit_record):
        """The stored results snapshot must be an exact copy."""
        assert audit_record["results_snapshot"] == sample_results


# ──────────────────────────────────────────────
# PRINCIPLE 3: Execution Binding
# ──────────────────────────────────────────────

class TestExecutionBinding:
    """Config and results are cryptographically chained together."""

    def test_execution_hash_binds_config_and_results(self, audit_record):
        """
        execution_hash = SHA-256( config_hash + ":" + results_hash )
        This is the glue. Break it and the whole chain falls apart.
        """
        config_hash = audit_record["config_hash_sha256"]
        results_hash = audit_record["results_hash_sha256"]
        combined = f"{config_hash}:{results_hash}"
        expected = hashlib.sha256(combined.encode()).hexdigest()

        assert audit_record["execution_hash_sha256"] == expected

    def test_swapping_config_and_results_breaks_binding(
        self, sample_config, sample_results
    ):
        """
        If someone swaps results from a different run with this config,
        the execution hash must NOT match.
        """
        record = create_audit_record(
            skill_name="binding_test",
            config_dict=sample_config,
            results=sample_results,
            outputs_dir=OUTPUTS_DIR,
        )

        # Simulate a forged result from a "different experiment"
        forged_results = {"counts": {"01": 4096}, "fidelity": 0.50}
        forged_str = json.dumps(forged_results, sort_keys=True, default=str)
        forged_results_hash = hashlib.sha256(forged_str.encode()).hexdigest()

        # Recompute what the execution hash WOULD be with forged results
        forged_combined = f"{record['config_hash_sha256']}:{forged_results_hash}"
        forged_exec_hash = hashlib.sha256(forged_combined.encode()).hexdigest()

        assert forged_exec_hash != record["execution_hash_sha256"], (
            "Forged results must not produce the same execution hash"
        )

    def test_verification_method_is_documented(self, audit_record):
        """The record must self-document how to verify it."""
        assert "SHA-256" in audit_record["verification_method"]
        assert "config" in audit_record["verification_method"].lower()
        assert "results" in audit_record["verification_method"].lower()


# ──────────────────────────────────────────────
# PRINCIPLE 4: Persistence
# ──────────────────────────────────────────────

class TestPersistence:
    """Audit records must survive on disk with correct content."""

    def test_audit_file_is_created(self, audit_record):
        """At least one audit file must exist after creating a record."""
        audit_dir = Path(OUTPUTS_DIR) / "audit_trail"
        files = list(audit_dir.glob("audit_workflow_test_*.json"))
        assert len(files) >= 1, "Audit file must be persisted to disk"

    def test_audit_file_content_matches_record(self, audit_record):
        """What's on disk must exactly match what was returned."""
        audit_dir = Path(OUTPUTS_DIR) / "audit_trail"
        files = sorted(audit_dir.glob("audit_workflow_test_*.json"))
        latest = files[-1]

        saved = json.loads(latest.read_text(encoding="utf-8"))

        assert saved["execution_hash_sha256"] == audit_record["execution_hash_sha256"]
        assert saved["config_hash_sha256"] == audit_record["config_hash_sha256"]
        assert saved["results_hash_sha256"] == audit_record["results_hash_sha256"]
        assert saved["config_snapshot"] == audit_record["config_snapshot"]
        assert saved["results_snapshot"] == audit_record["results_snapshot"]

    def test_audit_filename_contains_execution_hash(self, audit_record):
        """Filename must include the short hash for quick identification."""
        audit_dir = Path(OUTPUTS_DIR) / "audit_trail"
        files = list(audit_dir.glob("audit_workflow_test_*.json"))
        short_hash = audit_record["execution_hash_sha256"][:8]

        assert any(short_hash in f.name for f in files), (
            f"Filename must contain short hash {short_hash}"
        )

    def test_audit_directory_created_automatically(self):
        """The audit_trail directory must be auto-created if missing."""
        fresh_dir = "./test_fresh_outputs"
        try:
            record = create_audit_record(
                skill_name="fresh_test",
                config_dict={"test": True},
                results={"ok": True},
                outputs_dir=fresh_dir,
            )
            assert (Path(fresh_dir) / "audit_trail").exists()
        finally:
            shutil.rmtree(fresh_dir, ignore_errors=True)


# ──────────────────────────────────────────────
# TEST SUITE SANITY CHECK
# ──────────────────────────────────────────────

def test_audit_test_count():
    """
    Ensure test count matches the documented coverage matrix.
    Update the count in TESTING.md if this fails.
    See: docs/TESTING.md → Test Coverage Matrix
    """
    import ast
    from pathlib import Path
    source = Path(__file__).read_text()
    tree = ast.parse(source)
    test_count = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("test_")
    )
    assert test_count == 16, (
        f"Expected 16 tests (per coverage matrix), found {test_count}. "
        f"Update the Test Coverage Matrix in TESTING.md."
    )

# ──────────────────────────────────────────────
# PRINCIPLE 5: Reproducible Verification
# ──────────────────────────────────────────────

class TestReproducibleVerification:
    """
    A completely independent party must be able to verify
    the audit record using ONLY the stored data.
    """

    def test_full_independent_verification(self, audit_record):
        """
        Simulate a third-party auditor who:
        1. Reads the saved file
        2. Recomputes every hash from the snapshots
        3. Verifies the entire chain
        """
        # Step 1: Read from disk (as an auditor would)
        audit_dir = Path(OUTPUTS_DIR) / "audit_trail"
        files = sorted(audit_dir.glob("audit_workflow_test_*.json"))
        saved = json.loads(files[-1].read_text(encoding="utf-8"))

        # Step 2: Recompute config hash from the snapshot
        config_str = json.dumps(saved["config_snapshot"], sort_keys=True, default=str)
        verified_config_hash = hashlib.sha256(config_str.encode()).hexdigest()

        # Step 3: Recompute results hash from the snapshot
        results_str = json.dumps(saved["results_snapshot"], sort_keys=True, default=str)
        verified_results_hash = hashlib.sha256(results_str.encode()).hexdigest()

        # Step 4: Recompute execution hash
        combined = f"{verified_config_hash}:{verified_results_hash}"
        verified_exec_hash = hashlib.sha256(combined.encode()).hexdigest()

        # Step 5: Assert everything matches
        assert verified_config_hash == saved["config_hash_sha256"], (
            "❌ Config integrity check FAILED"
        )
        assert verified_results_hash == saved["results_hash_sha256"], (
            "❌ Results integrity check FAILED"
        )
        assert verified_exec_hash == saved["execution_hash_sha256"], (
            "❌ Execution binding check FAILED"
        )

    def test_verification_detects_file_tampering(self, audit_record):
        """
        If someone edits the persisted JSON (e.g., changes a result),
        the hash chain must break.
        """
        audit_dir = Path(OUTPUTS_DIR) / "audit_trail"
        files = sorted(audit_dir.glob("audit_workflow_test_*.json"))
        target_file = files[-1]

        # Read and tamper
        saved = json.loads(target_file.read_text(encoding="utf-8"))
        saved["results_snapshot"]["fidelity"] = 0.99  # Sneaky edit 👀

        # Recompute from tampered data
        results_str = json.dumps(saved["results_snapshot"], sort_keys=True, default=str)
        tampered_results_hash = hashlib.sha256(results_str.encode()).hexdigest()

        # This MUST fail — the stored hash won't match
        assert tampered_results_hash != saved["results_hash_sha256"], (
            "❌ Tampering was NOT detected — this is a critical failure"
        )
# Testing Strategy: Audit Integrity

## Test Coverage Matrix
> **Source:** [`agent_runtime/test_audit_workflow.py`](../agent_runtime/test_audit_workflow.py)

| Principle                | Tests | Type        |
|--------------------------|-------|-------------|
| Config Integrity         | 4     | Unit        |
| Results Integrity        | 3     | Unit        |
| Execution Binding        | 3     | Unit        |
| Persistence              | 4     | Integration |
| Reproducible Verification | 2     | E2E         |
| **Total**                | **16**| —           |

## Running Tests
```bash
# All audit tests
pytest agent_runtime/test_audit_workflow.py -v
# Specific principle
pytest agent_runtime/test_audit_workflow.py::TestConfigIntegrity -v
# With coverage (adjust module path to match your project structure)
pytest agent_runtime/test_audit_workflow.py --cov=agent_runtime/audit --cov-report=term-missing
```

### What Each Test Class Validates
- **TestConfigIntegrity**
  - Deterministic hashing (same input → same hash)
  - Sensitivity (tiny change → different hash)
  - Key-order independence
  - Snapshot accuracy
- **TestResultsIntegrity**
  - Independent hash recomputation
  - Tampering detection
  - Snapshot fidelity
- **TestExecutionBinding**
  - Hash chain correctness
  - Cross-run swap detection
  - Audit record contains all fields required for independent verification
- **TestPersistence**
  - File creation
  - Content accuracy
  - Filename convention
  - Auto-directory creation
- **TestReproducibleVerification**
  - Full third-party verification flow
  - File tampering detection

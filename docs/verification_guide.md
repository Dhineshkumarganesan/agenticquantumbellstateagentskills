# Audit Verification Guide

## Who Is This For?
Anyone who needs to verify that a quantum experiment's results haven't been tampered with:
- Security auditors
- Peer reviewers
- Compliance teams
- Your future self 😄

---

## Quick Verification (Python)
```python
import hashlib
import json
from pathlib import Path

def verify_audit_record(filepath: str) -> dict:
    """
    Independently verify an audit record's hash chain integrity.
    Args:
        filepath: Path to the audit record JSON file.
    Returns:
        dict with pass/fail for each integrity principle
        and an overall 'verified' boolean.
    Raises:
        FileNotFoundError: If the audit file doesn't exist.
        KeyError: If required fields are missing from the record.
        json.JSONDecodeError: If the file isn't valid JSON.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Audit file not found: {filepath}")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Audit file is not valid JSON: {e.msg}",
            e.doc,
            e.pos,
        )
    # Validate required fields exist before proceeding
    required_fields = [
        "config_snapshot",
        "results_snapshot",
        "config_hash_sha256",
        "results_hash_sha256",
        "execution_hash_sha256",
    ]
    missing = [f for f in required_fields if f not in record]
    if missing:
        raise KeyError(f"Audit record missing required fields: {missing}")
    results = {}
    # 1. Verify config integrity (NO default=str per ADR-001)
    config_str = json.dumps(record["config_snapshot"], sort_keys=True)
    computed_config_hash = hashlib.sha256(config_str.encode()).hexdigest()
    results["config_integrity"] = (
        computed_config_hash == record["config_hash_sha256"]
    )
    # 2. Verify results integrity (WITH default=str per ADR-001)
    results_str = json.dumps(
        record["results_snapshot"], sort_keys=True, default=str
    )
    computed_results_hash = hashlib.sha256(results_str.encode()).hexdigest()
    results["results_integrity"] = (
        computed_results_hash == record["results_hash_sha256"]
    )
    # 3. Verify execution binding
    combined = f"{computed_config_hash}:{computed_results_hash}"
    computed_exec_hash = hashlib.sha256(combined.encode()).hexdigest()
    results["execution_binding"] = (
        computed_exec_hash == record["execution_hash_sha256"]
    )
    # 4. Overall verdict
    results["verified"] = all([
        results["config_integrity"],
        results["results_integrity"],
        results["execution_binding"],
    ])
    return results

# Usage
verdict = verify_audit_record("outputs/audit_trail/audit_bell_state_xxx.json")
print("✅ VERIFIED" if verdict["verified"] else "❌ TAMPERING DETECTED")
print(verdict)
```

### Expected Output — Clean Record

```
✅ VERIFIED
{'config_integrity': True, 'results_integrity': True, 'execution_binding': True, 'verified': True}
```

### Expected Output — Tampered Record

```
❌ TAMPERING DETECTED
{'config_integrity': True, 'results_integrity': False, 'execution_binding': False, 'verified': False}
```

> **Note:** If `results_integrity` fails, `execution_binding` will *always* fail too — the execution hash depends on the results hash. This is by design: the hash chain propagates any single tampering event upward.

---

## Cross-Language Verification

The hash chain uses only standard SHA-256 and JSON. You can verify in any language:

| Language | SHA-256 Source | JSON Source |
|----------|---------------|-------------|
| Python   | `hashlib.sha256` | `json.dumps(sort_keys=True)` |
| Node.js  | `crypto.createHash('sha256')` | `JSON.stringify(sortKeys(obj))` |
| Go       | `crypto/sha256` | `encoding/json` (map keys sorted as of Go 1.12+) |
| Rust     | `sha2` crate | `serde_json` with ordered features |

> ⚠️ **Critical:** You must sort JSON keys before hashing. Different key ordering = different hash = false tampering alert.

---

## Manual Verification (CLI)

For environments without the full Python verification function, you can run these standalone one-shot checks directly from your terminal.

#### Step 1: Verify Config Integrity
```bash
python3 -c "import json, hashlib, sys, os
f = sys.argv[1]
if not os.path.exists(f):
    print(f'Error: File not found: {f}')
    sys.exit(1)
record = json.load(open(f))
config_hash = hashlib.sha256(json.dumps(record['config_snapshot'], sort_keys=True).encode()).hexdigest()
stored = record['config_hash_sha256']
match = config_hash == stored
print(f'Config Hash - Computed: {config_hash}')
print(f'Config Hash - Stored:   {stored}')
print('Config Match: ' + ('\u2705 PASS' if match else '\u274c FAIL'))
" audit_file.json
```

#### Step 2: Verify Results Integrity
```bash
python3 -c "import json, hashlib, sys, os
f = sys.argv[1]
if not os.path.exists(f):
    print(f'Error: File not found: {f}')
    sys.exit(1)
record = json.load(open(f))
results_hash = hashlib.sha256(json.dumps(record['results_snapshot'], sort_keys=True, default=str).encode()).hexdigest()
stored = record['results_hash_sha256']
match = results_hash == stored
print(f'Results Hash - Computed: {results_hash}')
print(f'Results Hash - Stored:   {stored}')
print('Results Match: ' + ('\u2705 PASS' if match else '\u274c FAIL'))
" audit_file.json
```

#### Step 3: Verify Execution Binding
```bash
python3 -c "import json, hashlib, sys, os
f = sys.argv[1]
if not os.path.exists(f):
    print(f'Error: File not found: {f}')
    sys.exit(1)
record = json.load(open(f))
config_hash = hashlib.sha256(json.dumps(record['config_snapshot'], sort_keys=True).encode()).hexdigest()
results_hash = hashlib.sha256(json.dumps(record['results_snapshot'], sort_keys=True, default=str).encode()).hexdigest()
exec_hash = hashlib.sha256(f'{config_hash}:{results_hash}'.encode()).hexdigest()
stored = record['execution_hash_sha256']
match = exec_hash == stored
print(f'Execution Hash - Computed: {exec_hash}')
print(f'Execution Hash - Stored:   {stored}')
print('Binding Match: ' + ('\u2705 PASS' if match else '\u274c FAIL'))
" audit_file.json
```

### Alternative: All-in-One Verification Script

```bash
python3 -c "import json, hashlib, sys, os
f = sys.argv[1]
if not os.path.exists(f):
    print(f'Error: File not found: {f}')
    sys.exit(1)
record = json.load(open(f))
# Config integrity (NO default=str per ADR-001)
config_hash = hashlib.sha256(json.dumps(record['config_snapshot'], sort_keys=True).encode()).hexdigest()
config_ok = config_hash == record['config_hash_sha256']
print(f'Config:    {config_hash}')
key = 'config_hash_sha256'
print(f'Expected:  {record[key]}')
print('Config: ' + ('\u2705 PASS' if config_ok else '\u274c FAIL'))
print()
# Results integrity (WITH default=str per ADR-001)
results_hash = hashlib.sha256(json.dumps(record['results_snapshot'], sort_keys=True, default=str).encode()).hexdigest()
key = 'results_hash_sha256'
results_ok = results_hash == record[key]
print(f'Results:   {results_hash}')
print(f'Expected:  {record[key]}')
print('Results: ' + ('\u2705 PASS' if results_ok else '\u274c FAIL'))
print()
# Execution binding
exec_hash = hashlib.sha256(f'{config_hash}:{results_hash}'.encode()).hexdigest()
key = 'execution_hash_sha256'
exec_ok = exec_hash == record[key]
print(f'Binding:   {exec_hash}')
print(f'Expected:  {record[key]}')
print('Binding: ' + ('\u2705 PASS' if exec_ok else '\u274c FAIL'))
print()
# Overall
if config_ok and results_ok and exec_ok:
    print('\u2705 ALL CHECKS PASSED')
else:
    print('\u274c VERIFICATION FAILED')
    sys.exit(1)
" audit_file.json
```


# ADR-001: Audit Hash Chain Design

## Status
Accepted

## Date
2025-01-15

## Authors
- [DHINESH KUMAR GANESHAN]

## Reviewers
- [Reviewer 1]
- [Reviewer 2]

---

## Context
We need tamper-evident records for quantum experiment executions to ensure scientific reproducibility and compliance.

### Problem Statement
Quantum experiments involve:
- **Expensive compute** — IBM Quantum jobs cost real money and queue time
- **Non-deterministic results** — You can't just "re-run" and expect identical output
- **Regulatory requirements** — Research integrity mandates provable audit trails
- **Collaboration risks** — Multiple team members access shared result stores

Without integrity guarantees, there is no way to prove that:
1. A config wasn't tweaked after seeing unfavorable results
2. Results weren't cherry-picked or modified
3. A specific result actually came from a specific config

### Motivating Scenarios
| Scenario | Risk Without Audit |
|----------|-------------------|
| Researcher adjusts `optimization_level` after execution | Config fraud — can't detect |
| Measurement counts edited to boost fidelity | Results tampering — invisible |
| Results from run A paired with config from run B | Cross-contamination — undetectable |
| Audit file manually edited on disk | Silent data corruption |
| External reviewer asks "prove this is authentic" | No verification mechanism |

---

## Decision
Use SHA-256 hash chains binding config → results → execution, persisted as self-contained JSON audit records.

### The 5 Integrity Principles
| # | Principle | Implementation |
|---|-----------|---------------|
| 1 | Config Integrity | SHA-256 of deterministically serialized config |
| 2 | Results Integrity | SHA-256 of deterministically serialized results |
| 3 | Execution Binding | SHA-256 of combined config + results hashes |
| 4 | Persistence | JSON files in `{outputs_dir}/audit_trail/` |
| 5 | Reproducible Verification | All data needed for verification stored in the record |

### Hash Chain Architecture
```
┌──────────────┐          ┌──────────────────┐
│  Config Dict │          │  Results Dict     │
└──────┬───────┘          └────────┬──────────┘
       │                           │
  json.dumps(                 json.dumps(
    sort_keys=True)             sort_keys=True,
       │                        default=str)
       │                           │
   SHA-256                     SHA-256
       │                           │
       ▼                           ▼
┌──────────────┐          ┌──────────────────┐
│ config_hash  │          │ results_hash     │
│  (32 bytes)  │          │  (32 bytes)      │
└──────┬───────┘          └────────┬──────────┘
       │                           │
       └───────────┬───────────────┘
                   │
         "{config_hash}:{results_hash}"
                   │
               SHA-256
                   │
                   ▼
         ┌──────────────────┐
         │ execution_hash   │
         │  (32 bytes)      │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │  Audit Record    │
         │  (.json file)    │
         └──────────────────┘
```

### Audit Record Schema
```json
{
  "skill_name": "string",
  "timestamp_utc": "ISO-8601",
  "config_hash_sha256": "hex string (64 chars)",
  "results_hash_sha256": "hex string (64 chars)",
  "execution_hash_sha256": "hex string (64 chars)",
  "config_snapshot": { "...original config..." },
  "results_snapshot": { "...original results..." },
  "verification_method": "SHA-256 hash chain: config → results → execution"
}
```

## Rationale
### Why SHA-256?
| Criteria | SHA-256 | MD5 | SHA-3 | BLAKE3 |
|----------|--------|-----|-------|--------|
| Classical Security (bits) | 256 | ❌ Broken | 256 | 256 |
| Post-Quantum Security (Grover) | 128 | ❌ N/A | 128 | 128 |
| Python stdlib support | ✅ hashlib | ✅ | ✅ | ❌ External |
| Industry adoption | Universal | Legacy | Growing | Niche |
| NIST approved | ✅ | ❌ | ✅ | ❌ |
| Performance (for our scale) | Sufficient | N/A | Similar | Faster |

The math on quantum resistance:
Grover's algorithm reduces brute-force search from $O(2^n)$ to $O(2^{n/2})$.

$$
\text{SHA-256 post-quantum security} = \frac{256}{2} = 128\ \text{bits}
$$

128-bit security is considered sufficient through 2030+ by NIST.

### Why Hash Chains (Not Alternatives)?
**vs. HMAC:**
- HMAC = Hash(key, message)
- Requires a shared secret key
- Key management adds operational complexity
- We need public verifiability, not authenticated messaging
- Overkill: we're proving integrity, not authenticity to a specific party

**vs. Digital Signatures:**
- Signature = Sign(private_key, message); Verify(public_key, message, signature)
- Requires PKI (Public Key Infrastructure)
- Key generation, storage, rotation, revocation
- Who holds the private key? Single point of failure
- Massive operational overhead for our use case

**vs. Blockchain:**
- Requires consensus mechanism (unnecessary for single-system)
- Storage overhead grows unboundedly
- Network dependency for verification
- Like using a sledgehammer to hang a picture frame 🔨

**vs. Database with access controls:**
- Access controls prevent modification, not detect it
- Admin can always bypass controls
- No cryptographic proof of integrity
- "Trust me bro" is not a verification method

### Why JSON Serialization?
| Requirement | JSON | pickle | protobuf | msgpack |
|-------------|------|--------|----------|---------|
| Human readable | ✅ | ❌ | ❌ | ❌ |
| Cross-language | ✅ | ❌ Python only | ✅ | ✅ |
| Deterministic with sort_keys | ✅ | ❌ | ❌ | ❌ |
| No deserialization attacks | ✅ | ❌ RCE risk | ✅ | ✅ |
| Stdlib support | ✅ | ✅ | ❌ | ❌ |

### Why sort_keys=True?
Critical for deterministic hashing.

```python
# Without sort_keys — DANGEROUS
json.dumps({"b": 2, "a": 1})  # '{"b": 2, "a": 1}'
json.dumps({"a": 1, "b": 2})  # '{"a": 1, "b": 2}'
# Different strings → different hashes → false tampering alert!

# With sort_keys — SAFE  ✅
json.dumps({"b": 2, "a": 1}, sort_keys=True)  # '{"a": 1, "b": 2}'
json.dumps({"a": 1, "b": 2}, sort_keys=True)  # '{"a": 1, "b": 2}'
# Same string → same hash → correct verification
```

---

## Alternatives Considered
| Option | Considered For | Rejected Because |
|--------|---------------|-----------------|
| MD5 | Faster hashing | Broken collision resistance (2004) |
| SHA-3 | Future-proofing | Unnecessary — SHA-256 is sufficient and more widely supported |
| HMAC | Authenticated integrity | Requires shared secret; we need public verifiability |
| Blockchain | Distributed trust | Overkill for single-system audit; adds network dependency |
| Digital Signatures | Non-repudiation | Requires PKI infrastructure we don't have |
| BLAKE3 | Performance | External dependency; speed is not our bottleneck |
| Database audit log | Simplicity | No cryptographic proof; admin can modify |
| Git commit hashes | Version control | Ties audit to repo structure; not self-contained |

---

## Consequences
**Positive**
✅ All audit code uses only Python stdlib (hashlib, json, pathlib)
✅ Zero external dependencies for core integrity
✅ Verification requires no special tools — any language with SHA-256 works
✅ Self-contained audit files — each record carries everything needed to verify it
✅ 128-bit post-quantum security without any cryptographic migration needed
✅ Human-readable records (JSON) for manual inspection

**Negative / Trade-offs**
⚠️ No non-repudiation — we can prove data hasn't changed, but not WHO created it
⚠️ No encryption — audit records are readable by anyone with file access
⚠️ Single-file integrity — no chain between successive audit records (each stands alone)
⚠️ Clock trust — timestamps rely on system clock accuracy

---

## Future Considerations
| Enhancement | When To Consider | Effort |
|-------------|------------------|--------|
| SHA-3 migration | If SHA-256 shows weakness | Low — swap hashlib.sha256 → hashlib.sha3_256 |
| Inter-record chaining | If sequential integrity needed | Medium — add previous_hash field |
| Digital signatures | If non-repudiation required | High — requires PKI setup |
| Encryption at rest | If confidentiality required | Medium — add Fernet wrapper |
| Remote attestation | If distributed verification needed | High — requires server infra |

---

## Compliance Mapping
| Requirement | How This ADR Addresses It |
|-------------|--------------------------|
| Data Integrity (ISO 27001 A.8.1) | SHA-256 hash chain detects any modification |
| Audit Logging (SOC 2 CC7.2) | Persistent JSON records with timestamps |
| Scientific Reproducibility | Config + results snapshots enable re-verification |
| Change Detection | Any byte-level change breaks the hash chain |

---

## Test Coverage
16 automated tests validate all 5 principles:

| Principle | Tests | File |
|-----------|-------|------|
| Config Integrity | 4 | test_audit_workflow.py::TestConfigIntegrity |
| Results Integrity | 3 | test_audit_workflow.py::TestResultsIntegrity |
| Execution Binding | 3 | test_audit_workflow.py::TestExecutionBinding |
| Persistence | 4 | test_audit_workflow.py::TestPersistence |
| Reproducible Verification | 2 | test_audit_workflow.py::TestReproducibleVerification |

```bash
pytest tests/test_audit_workflow.py -v
```

---

## References
- [NIST FIPS 180-4: Secure Hash Standard](https://csrc.nist.gov/publications/detail/fips/180/4/final)
- [Grover's Algorithm (1996)](https://arxiv.org/abs/quant-ph/9605043)
- [NIST Post-Quantum Cryptography FAQ](https://csrc.nist.gov/projects/post-quantum-cryptography/faqs)
- [Architecture Decision Records](https://adr.github.io/)

---


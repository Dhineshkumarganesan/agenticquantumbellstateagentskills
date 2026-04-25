# Audit Trail Integrity Principles

## Overview
The audit subsystem guarantees tamper-evident execution records for all quantum experiments. It is built on **5 cryptographic integrity principles**.

---

## Principle 1: Config Integrity
**Guarantee:** The experiment configuration has not been modified after execution.

**How:**
- Config dict is serialized with `json.dumps(sort_keys=True)`
- SHA-256 hash is computed and stored as `config_hash_sha256`
- A full snapshot of the original config is preserved

**Hash Formula:**
config_hash = SHA-256(JSON(config, sort_keys=True))

**What It Catches:**
- Post-execution parameter changes
- Accidental config mutations
- Unauthorized optimization level tweaks

---

## Principle 2: Results Integrity
**Guarantee:** Execution results have not been tampered with.

**How:**
- Results dict is serialized with `json.dumps(sort_keys=True, default=str)`
- SHA-256 hash stored as `results_hash_sha256`
- Full results snapshot is preserved

**Hash Formula:**
results_hash = SHA-256(JSON(results, sort_keys=True, default=str))

**What It Catches:**
- Altered measurement counts
- Forged fidelity scores
- Modified execution metadata

---

## Principle 3: Execution Binding
**Guarantee:** Config and results are cryptographically bound — you cannot mix-and-match across different runs.

**How:**
- Combines both hashes into a single chain
- Stored as `execution_hash_sha256`

**Hash Formula:**
execution_hash = SHA-256(config_hash + ":" + results_hash)

**What It Catches:**
- Swapping results from a different experiment
- Pairing high-fidelity results with a different config
- Any cross-contamination between runs

---

## Principle 4: Persistence
**Guarantee:** Audit records survive on disk and are retrievable.

**Implementation:**
- Records saved to `{outputs_dir}/audit_trail/`
- Filename format: `audit_{skill}_{timestamp}_{short_hash}.json`
- Directory auto-created if missing
- JSON format for universal readability

---

## Principle 5: Reproducible Verification
**Guarantee:** Any third party can independently verify the entire hash chain using only the saved audit file.

**Verification Steps:**
1. Read the audit JSON file
2. Recompute `config_hash`:   `SHA-256(JSON(config_snapshot, sort_keys=True))`
3. Recompute `results_hash`:  `SHA-256(JSON(results_snapshot, sort_keys=True, default=str))`
4. Recompute `execution_hash`: `SHA-256(config_hash + ":" + results_hash)`
5. Compare all three against stored values

**If any mismatch → tampering detected** 🚨

---

## Security Properties
| Property               | Status         |
|------------------------|-----------------|
| Hash Algorithm         | SHA-256         |
| Classical Security     | 256-bit         |
| Post-Grover Security   | 128-bit         |
| Collision Resistance   | $2^{128}$       |
| Quantum Resistant?     | ✅ Sufficient   |

> **Note:** Grover's algorithm reduces SHA-256's preimage resistance to 128-bit equivalent under a quantum threat model. This remains well above the ~80-bit minimum threshold for near-term security. For long-term post-quantum guarantees, consider migrating to SHA-3 or XMSS-based commitments if the threat model evolves.

---

## Visual: Hash Chain Flow
```
┌──────────────┐ ┌───────────────┐
│ Config Dict  │ │ Results Dict  │
└──────┬───────┘ └───────┬───────┘
      │                    │
 JSON serialize      JSON serialize
 (sort_keys=True)    (sort_keys=True)
      │                    │
   SHA-256              SHA-256
      │                    │
┌──────────────┐ ┌───────────────┐
│ config_hash  │ │ results_hash  │
└──────┬───────┘ └───────┬───────┘
      │                    │
      └──────────┬───────────┘
                 │
        "{config}:{results}"
                 │
              SHA-256
                 │
           ┌───────────────┐
           │ execution_hash│
           └───────────────┘
                 │
           ┌───────────────┐
           │ Saved to disk │
           │ as .json file │
           └───────────────┘
```

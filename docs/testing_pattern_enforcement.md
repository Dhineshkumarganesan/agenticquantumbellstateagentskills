# Extended Testing Scenarios: Pattern Enforcement

## 1. Agent/Runtime Separation

- **Test:** Add unsupported fields or code to a YAML skill file (e.g., `malicious_code: os.system('rm -rf /')`).
- **Expected:** Runtime should reject or ignore unsupported fields, raising a validation error or warning.
- **How to Test:**
  1. Edit a skill YAML and add an unsupported field or code.
  2. Run `python runtime/handler.py`.
  3. Confirm the runtime prints a validation error and does not execute the skill.
- **Note:** Only YAML edits are allowed. Agents/users must never edit runtime code. Code changes require code review and are not part of the agent workflow.

## 2. Schema Validation (Governance Firewall)

- **Test:** Provide YAML configs missing required fields or with wrong types (e.g., omit `shots`, set `qubits: "two"`).
- **Expected:** Runtime raises a Pydantic ValidationError and skips execution.
- **How to Test:**
  1. Create invalid YAML skill files.
  2. Run the pipeline and confirm errors are raised for each invalid config.

## 3. Runtime Immutability

- **Test:** Add a CI check or test that computes a checksum (e.g., SHA-256) of `runtime/handler.py` and core runtime files. Fail if files are modified unexpectedly.
- **How to Test:**
  1. Add a script to CI that checksums runtime files and compares to a known-good value.
  2. Attempt to modify runtime code; CI should fail.
- **Documentation:**
  - The runtime is immutable. Only YAML skill files are agent-editable. Any code change must go through code review and CI.

## 4. Variational Policy Handling

- **Test:** Create YAMLs specifying variational policy/bounds (e.g., `policy: {type: grid_search, bounds: [0, 1]}`) and confirm runtime executes the optimization loop.
- **How to Test:**
  1. Add a skill YAML with a variational policy.
  2. Run the pipeline and confirm the runtime performs the expected optimization (e.g., multiple runs, parameter sweeps).
  3. Check outputs for evidence of policy-driven execution.

## 5. Manual/Integration Test Instructions

- **Contract-Breaking Attempts:**
  - Tamper with output files or audit records and run verification scripts. Expect verification to fail.
  - Provide invalid YAML or inject code. Expect validation errors.
  - Attempt to edit runtime code as an agent. Expect CI or process to block/flag the change.

- **How to Run:**
  1. Edit YAMLs and outputs as described above.
  2. Run `python runtime/handler.py` and/or verification scripts.
  3. Observe and document outcomes (errors, warnings, verification failures).

---

**By following these tests and instructions, you ensure strict enforcement of agent/runtime separation, schema validation, runtime immutability, auditability, and policy-driven execution.**

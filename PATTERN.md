# PATTERN.md — The Declarative Agent Loop Pattern for Quantum Computing

## Pattern Name
**Quantum-as-Code** (also: Declarative Agent Loop Pattern)

## Author
**DHINESH KUMAR GANESHAN**  
[[Github](https://github.com/Dhineshkumarganesan) / [LinkedIn](https://www.linkedin.com/in/dhinesh-kumar-ganeshan745/) ]  
First published: [20-APR-2026]

## Origin Statement
This architectural pattern was conceived and first implemented by 
DHINESH KUMAR GANESHAN in APRIL 2026. It applies the infrastructure-as-code
paradigm (as seen in Terraform, Kubernetes, and Ansible) to quantum
computing experiment orchestration, with specific innovations in:

1. **Declarative agent loops** — AI agents edit YAML configuration, 
   never executable code
2. **Schema-governed execution** — Pydantic validation as a governance 
   firewall between intent and implementation  
3. **Seed-mode duality** — A single configuration field switches between 
   deterministic (reproducible) and stochastic (sampling) execution
4. **Variational policy control** — Agents define parameter bounds and 
   optimization policy; the runtime handles the inner optimization loop
5. **Cryptographic audit trails** — Every execution produces a 
   tamper-evident record linking configuration to results

## Problem Statement

Quantum computing experiments are complex, error-prone, and difficult to audit. Traditional approaches mix intent (what to run) with implementation (how to run it), making reproducibility, compliance, and automation challenging. YAML configuration is flexible but vulnerable to drift, silent errors, and lack of traceability. There is no clear boundary between agent intent, runtime execution, and auditability, especially for advanced workflows like variational algorithms or regulatory environments.

## Solution

This pattern enforces a strict separation of concerns and governs the trust boundary between agent-driven exploration and certified, reproducible results:

The declarative certification layer must remain architecturally independent from the adaptive exploration system. Certification by the same system that generated the result does not constitute an independent audit trail.
- **Agents** edit only declarative YAML skill files, never code.
- **Schema validation** (Pydantic) acts as a governance firewall, rejecting invalid or out-of-contract configs before execution.
- **Runtime** is immutable and executes only validated, contract-compliant configs.
- **Determinism** is controlled by config (seeded or stochastic runs) for both audit and research needs.
- **Variational algorithms** are handled at the policy level: agents set bounds and optimization policy, runtime owns the inner loop.
- **Audit trails** cryptographically link every config to its results, enabling full traceability and regulator-grade verification.

**Scope and Limitations:**
- For known circuit families (e.g., Bell, GHZ, QAOA with fixed ansatz), declarative governance applies from the start.
- For novel, adaptively generated circuits, the declarative pattern governs the certification phase: once an adaptive agent converges on a result, the final circuit and parameters are captured, schema-validated, and locked as a "golden config" for reproducibility, audit, and publication.
- Declarative methods do not replace adaptive exploration; they certify and preserve its outputs for trust, compliance, and collaboration.

This architecture enables safe, scalable, and auditable quantum experimentation—ready for both research and compliance-driven environments, and acts as the notary for adaptive agent discoveries.


## Key Principles
1. Agents edit configuration, not implementation
2. Schema validation is the governance firewall
3. The runtime is immutable — agents cannot modify it
4. Every execution is auditable
5. Reproducibility is a configuration choice, not a code change

## Prior Art and Influences
- Terraform (HashiCorp) — infrastructure as code
- Kubernetes — declarative desired-state configuration  
- GitOps (Weaveworks) — git as single source of truth
- PennyLane (Xanadu) — device configuration model for reproducible quantum ML
- IBM Qiskit Runtime — Estimator and Sampler primitives for declarative quantum execution

## What's New Here

This pattern introduces several innovations that go beyond traditional agentic or declarative orchestration:

1. **Schema-Governed Execution:** Every skill YAML is validated by a strict Pydantic schema before execution. This eliminates "YAML drift" and ensures only contract-compliant configurations are ever run.
2. **Configurable Determinism:** Agents can toggle between deterministic (seeded) and stochastic (random) quantum runs by setting a single field in YAML. This enables both audit-grade reproducibility and true quantum sampling from the same pipeline.
3. **Variational Policy Control [Planned v2.0]:** For algorithms like QAOA and VQE, agents will specify parameter bounds and optimization policy—not the actual parameters. The runtime will own the optimization loop, keeping the agent declarative and the system scalable. This feature is planned for a future release.
4. **Cryptographic Audit Trails:** Every execution produces a tamper-evident audit record, cryptographically linking the config and results. This enables regulator-grade traceability and independent verification.

These features collectively make the system production-credible, regulator-ready, and uniquely agent-friendly.

## License
This pattern description is published under CC BY 4.0.
The reference implementation is published under Apache 2.0.
Both require attribution to [Your Full Name] as the original author.
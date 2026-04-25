# Agents Edit Config, Not Code: A Declarative Loop to Run Quantum Experiments

> *Agentic AI driving quantum circuit simulation — same pattern as Terraform Module Expert.*

Series: Engineering Platforms for the Agentic AI Era

💬 Perspective

“Exploring how agentic AI can be applied to build product-grade enterprise platform capabilities for infrastructure automation, system orchestration, and reusable workflow systems across classical and emerging computing workloads.”

Introduction

After exploring agentic platform engineering with Terraform module expert agents and skills, I was inspired to apply the same GitHub Copilot agent–skill orchestration pattern to quantum computing. My @QuLearnLab training provided a foundation in the quantum computing fundamentals, informing the approach and examples throughout. This post demonstrates how an orchestrator — powered by GitHub Copilot agents and skills — can manage quantum circuit workflows, making advanced experimentation more accessible, reproducible, and automation-friendly for developers.

This is a proof-of-concept demonstrating a pattern — not a production system. The value is in the boundary it establishes, not the scale it operates at.

Principle: Agents should edit configuration, not implementation.

Most articles about “agentic AI and quantum computing” talk about LLMs designing quantum circuits. This post is about something far more practical: using an agent to control a configuration state machine, not execution logic.

This post is for developers comfortable with Python and Qiskit, and curious to see what “agentic AI” looks like in real quantum experiments — not just in trend reports. The tools: GitHub Copilot, Qiskit, and the Aer simulator. No new frameworks. No cloud hardware required.

---

## Architecture

```
User Intent (natural language)
        │
        ▼
┌───────────────────┐
│  AGENT.md         │  ← Quantum Circuit Expert
│  (Orchestrator)   │    reads intent, selects skill,
│                   │    edits YAML frontmatter
└────────┬──────────┘
         │  edits YAML only
         ▼
┌─────────────────────────────────────────┐
│  skills/                                │
│  ├── circuits/                          │
│  │   ├── bell_state.md      ← Step 1   │
│  │   ├── ghz_state.md                  │
│  │   └── superposition.md              │
│  ├── execution/                         │
│  │   ├── execute_circuit.md ← Step 2   │
│  │   └── measure_circuit.md ← Step 3   │
│  └── output/                            │
│      ├── visualize_circuit.md ← Step 4 │
│      └── export_counts.md    ← Step 5  │
└────────┬────────────────────────────────┘
         │  reads YAML, executes
         ▼
┌───────────────────┐
│  runtime/         │
│  handler.py       │  ← Never edited by agent
└────────┬──────────┘
         │
         ├──────────────────┐
         ▼                  ▼
┌───────────────────┐ ┌──────────────────────┐
│  outputs/         │ │  outputs/audit_trail/ │
│  ├── circuit_diagram.png  │ ├── audit_{skill}_{ts}.json
│  ├── counts.json  │ │  SHA-256 hash chain   │
│  └── ...          │ │  (tamper-evident)     │
└───────────────────┘ └──────────────────────┘
```

---
## 🔒 Audit Trail
All quantum experiment executions produce tamper-evident audit records based on SHA-256 hash chains.

**Key guarantees:**
- Config and results integrity
- Cryptographic binding between config ↔ results
- Persistent, independently verifiable records

📖 [Full Principle Documentation](docs/audit_integrity_principles.md)
🔍 [Verification Guide](docs/verification_guide.md)
🧪 [Testing Strategy](docs/testing_strategy.md)

---

## Limitations and Extensibility

| What You Want to Do | Edit Skills (YAML)? | Edit Python? |
|---|---|---|
| Change shots, qubits, parameters | ✅ Yes | ❌ No |
| Add a new experiment with existing gates | ✅ Yes | ❌ No |
| Add a new gate type (e.g., Toffoli) | ✅ Declare it | ⚠️ Handler must support it |
| New visualization type (e.g., noise) | ❌ | ✅ Yes |
| New output format (e.g., OpenQASM) | ❌ | ✅ Yes |

## The Key Pattern

| Layer | Who Owns It | What It Contains |
|---|---|---|
| `AGENT.md` | Copilot/Claude reads | Orchestration rules |
| `skills/*.md` | Agent edits YAML only | Circuit configuration |
| `runtime/handler.py` | Runtime executes | Quantum logic (read-only for agent) |
| `outputs/` | Runtime writes | Results and diagrams |

The agent **never touches Python**. The runtime **never reads intent**.
They communicate only through YAML skill files.

---

## Supported Circuits

| Circuit | Qubits | Demonstrates |
|---|---|---|
| Bell State | 2 (fixed) | Quantum entanglement |
| GHZ State | 3–5 | Multi-qubit entanglement |
| Superposition | 1–4 | Quantum superposition |
| Declarative (YAML-defined) | Any | Arbitrary circuits via gates/measurements |

---

### Declarative Agent Loop (New!)

- You can now define any quantum experiment by listing gates and measurements in YAML (see `skills/circuits/custom_declarative.md`, `single_qubit_superposition.md`, etc.).
- The runtime dynamically builds and runs the circuit from the YAML—no Python code changes required.
- Example declarative skill:

```yaml
---
action: design_circuit
circuit_type: custom_declarative
qubits: 2
gates:
  - type: h
    target: [0]
  - type: cx
    control: 0
    target: 1
measurements: [0, 1]
---
```

This enables rapid prototyping and agent-driven automation for any quantum circuit.

## Quick Start

### Install dependencies
```bash
pip install qiskit qiskit-aer matplotlib pyyaml
```

### Run all available circuits (multi-skill batch mode)
```bash
python runtime/handler.py
```

This will automatically process every valid circuit skill in `skills/circuits/` (e.g., Bell, GHZ, Superposition), generating separate outputs for each. To control which circuits are run, simply add or remove skill files in that folder.

### Change circuit parameters via YAML
Edit the relevant skill file in `skills/circuits/` (e.g., `bell_state.md`, `ghz_state.md`) to adjust circuit type, qubits, or gates.

Edit `skills/execution/execute_circuit.md` frontmatter:
```yaml
shots: 512
```

Then run again:
```bash
python runtime/handler.py
```

---

## Example Agent Interactions

**User:** "Show me quantum entanglement"
**Agent:** Sets `circuit_type: bell_state`, `shots: 1024` → runs pipeline

**User:** "Create a 4-qubit entangled state with 512 shots"
**Agent:** Sets `circuit_type: ghz_state`, `qubits: 4`, `shots: 512` → runs pipeline

**User:** "Demonstrate superposition quickly"
**Agent:** Sets `circuit_type: superposition`, `shots: 256` → runs pipeline

---

## Why No Python Agent in Between?

The YAML frontmatter **is** the intent contract.
The agent reads `AGENT.md` to understand rules,
selects the right skill file,
fills valid parameter values,
and the runtime executes.

This is identical to how the Terraform Module Expert works —
the agent is a **smart configurator**, not a code writer.


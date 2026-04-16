---
action: design_circuit
circuit_type: bell_state
qubits: 2
gates: [H, CNOT]
constraints:
  valid_circuits: [bell_state, ghz_state, superposition]
  min_qubits: 2
  max_qubits: 2
  valid_gates: [H, CNOT]
  fixed_qubits: true
output_circuit: quantum-circuit-expert/outputs/bell_circuit.png
---

# Bell State Circuit Skill

## Goal
Design a Bell state (maximally entangled 2-qubit) circuit for simulation.

## What This Circuit Does
A Bell state is the simplest demonstration of quantum entanglement.
Measuring one qubit instantly determines the state of the other,
regardless of distance. This is the "hello world" of quantum computing.

## Gate Sequence
```
q0: ──[H]──●──
           │
q1: ───────X──
```
- **H gate** on q0: puts q0 into superposition (50/50 probability)
- **CNOT gate**: entangles q1 with q0

## Expected Output
Measurement results should show approximately:
- `00` : ~50% of shots
- `11` : ~50% of shots
- `01` and `10` should never appear (proves entanglement)

## Agent Rules
- `qubits` is always 2 — Bell state is a 2-qubit circuit by definition
- `gates` is always [H, CNOT] — do not modify
- `fixed_qubits: true` means you cannot change qubit count
- Only edit `circuit_type` if switching to a different circuit

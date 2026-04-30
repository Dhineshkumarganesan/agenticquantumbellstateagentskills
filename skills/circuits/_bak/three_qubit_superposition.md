---
action: design_circuit
circuit_type: three_qubit_superposition
qubits: 3
gates:
  - type: h
    target: [0]
  - type: h
    target: [1]
  - type: h
    target: [2]
measurements: [0, 1, 2]
---

# Three-Qubit Superposition (Declarative)

## Goal
Demonstrate all three qubits in superposition (|+++⟩ state), not entangled.

## What This Circuit Does
- Applies H gate to each qubit
- Measures all qubits

## Expected Output
- All 8 possible states (000, 001, ..., 111) with ~12.5% probability each

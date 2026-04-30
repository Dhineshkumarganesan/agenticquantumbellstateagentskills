---
action: design_circuit
circuit_type: single_qubit_superposition
qubits: 1
gates:
  - type: h
    target: [0]
measurements: [0]
---

# Single Qubit Superposition (Declarative)

## Goal
Demonstrate a single qubit in superposition using only a Hadamard gate and measurement.

## What This Circuit Does
- Applies H gate to qubit 0
- Measures qubit 0

## Expected Output
- 0 and 1 with ~50% probability each

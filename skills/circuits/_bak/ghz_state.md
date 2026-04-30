---
action: design_circuit
circuit_type: ghz_state
qubits: 3
gates: [H, CNOT, CNOT]
initial_state: [1, 1, 1]
constraints:
  valid_circuits: [ghz_state, bell_state, w_state]
  min_qubits: 3
  max_qubits: 3
  valid_gates: [H, CNOT]
  fixed_qubits: true
output_circuit: outputs/ghz_circuit.png
---

# GHZ State Circuit Skill

## Goal
Design a 3-qubit GHZ (Greenberger–Horne–Zeilinger) state circuit for simulation.

## What This Circuit Does
A GHZ state is a maximally entangled 3-qubit state: (|000⟩ + |111⟩)/√2.

## Gate Sequence
```
q0: ──[H]──●────●──
           │    │
q1: ───────X────┼──
                │
q2: ────────────X──
```

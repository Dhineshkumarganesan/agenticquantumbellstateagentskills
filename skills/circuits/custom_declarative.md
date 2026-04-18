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

# Declarative Custom Circuit

## Goal
Demonstrate a Bell-like state using a fully declarative YAML skill.

## What This Circuit Does
This is a Bell state, but defined only by the gates/measurements list, not a hardcoded builder.

## Gate Sequence
- H gate on q0
- CX gate from q0 to q1
- Measure both qubits

## Expected Output
- 00 and 11 with ~50% probability each
- 01 and 10 should not appear

---
action: design_circuit
circuit_type: variational_demo
qubits: 2
gates:
  - type: ry
    target: [0]
    parameter: theta
  - type: cx
    control: 0
    target: 1
measurements: [0, 1]
variational_policy:
  optimizer: COBYLA
  max_iterations: 10
  parameter_bounds:
    - [0.0, 3.14]  # theta bounds
---

# Variational Circuit Skill

## Goal
Optimize the parameter theta in a 2-qubit circuit using COBYLA optimizer.

## Policy
- Optimizer: COBYLA
- Max iterations: 10
- Parameter bounds: theta ∈ [0, π]

## Expected
The runtime should perform an optimization loop, adjusting theta to minimize a cost function (e.g., maximize probability of |11⟩).

---
action: design_circuit
circuit_type: vqe_demo
qubits: 2
gates:
  - type: ry
    target: [0]
    parameter: theta1
  - type: ry
    target: [1]
    parameter: theta2
  - type: cx
    control: 0
    target: 1
measurements: [0, 1]
variational_policy:
  optimizer: SPSA
  max_iterations: 15
  parameter_bounds:
    - [0.0, 3.14]  # theta1
    - [0.0, 3.14]  # theta2
cost_function: minimize_energy
---

# VQE Demo Skill

## Goal
Find the ground state energy of a 2-qubit Hamiltonian using VQE.

## Policy
- Optimizer: SPSA
- Max iterations: 15
- Parameter bounds: theta1, theta2 ∈ [0, π]
- Cost function: minimize_energy

## Expected
The runtime should optimize both parameters to minimize the measured energy.
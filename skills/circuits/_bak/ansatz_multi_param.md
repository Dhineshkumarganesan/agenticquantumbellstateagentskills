---
action: design_circuit
circuit_type: ansatz_multi_param
qubits: 3
parameters:
  - name: "theta1"
    type: symbolic
    bounds: [0.0, 3.141593]
  - name: "theta2"
    type: symbolic
    bounds: [0.0, 3.141593]
  - name: "theta3"
    type: symbolic
    bounds: [0.0, 3.141593]
gates:
  - type: ry
    target: [0]
    parameter: theta1
  - type: ry
    target: [1]
    parameter: theta2
  - type: ry
    target: [2]
    parameter: theta3
  - type: cx
    control: 0
    target: 1
  - type: cx
    control: 1
    target: 2
measurements: [0, 1, 2]
variational_policy:
  enabled: true
  optimizer: COBYLA
  max_iterations: 20
  convergence_threshold: 0.001
  parameter_bounds:
    theta1:
      min: 0.0
      max: 3.141593
    theta2:
      min: 0.0
      max: 3.141593
    theta3:
      min: 0.0
      max: 3.141593
  initial_values:
    theta1: 1.0
    theta2: 1.0
    theta3: 1.0
  cost_function:
    type: expectation_value
    objective: maximize
---

# Multi-Parameter Ansatz Skill

## Goal
Optimize three parameters to maximize the probability of measuring |111⟩.

## Policy
- Optimizer: COBYLA
- Max iterations: 20
- Parameter bounds: theta1, theta2, theta3 ∈ [0, π]
- Cost function: maximize_111

## Expected
The runtime should optimize all three parameters to maximize the |111⟩ outcome.
---
action: "execute_circuit"
shots: 1024
seed: 42
execution_mode: "stochastic"
output_counts: "final_distribution"
title: "QAOA MaxCut Optimisation"
step_id: "qaoa_execute"
depends_on:
  - "qaoa_generate"
goal: >
  Optimise QAOA parameters using COBYLA to find
  the maximum cut. Expected optimal cut value is 4.
variational_policy:
  optimizer: "COBYLA"
  max_iterations: 50
  parameter_bounds:
    - [0.0, 6.2832]
    - [0.0, 3.1416]
---

# QAOA MaxCut — Step 2: Variational Execution

This skill runs the QAOA circuit with COBYLA optimisation.
Requires qaoa_generate to run first.

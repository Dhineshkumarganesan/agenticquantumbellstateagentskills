---
action: design_circuit
circuit_type: "universal_demo"
qubits: 2
gates:
  - type: "h"
    target: [0]
  - type: "rz"
    target: [0]
    parameter: 1.57  # π/2 phase shift
  - type: "cx"
    control: 0
    target: 1
measurements: [0, 1]
---
# Universal Quantum Circuit Demo
Applies H, phase (Rz), and CNOT gates to demonstrate universality.

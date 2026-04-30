---
action: design_circuit
circuit_type: ry_decomposition
gates:
  - type: s
    target: [0]
  - type: h
    target: [0]
  - type: rz
    parameter: 1.57
    target: [0]
  - type: h
    target: [0]
  - type: sdg
    target: [0]
measurements:
  - 0
qubits: 1
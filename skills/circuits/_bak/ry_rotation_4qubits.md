---
action: design_circuit
circuit_type: ry_decomposition_4q
qubits: 4
gates:
  # Apply the decomposition to all 4 qubits
  - type: s
    target: [0, 1, 2, 3]
  - type: h
    target: [0, 1, 2, 3]
  - type: rz
    parameter: 1.57
    target: [0, 1, 2, 3]
  - type: h
    target: [0, 1, 2, 3]
  - type: sdg
    target: [0, 1, 2, 3]
measurements:
  - [0, 1, 2, 3]
---
action: generate_circuit
circuit: bell        # bell | ghz | superposition
qubits: 2
measure: true
---
# Generate Circuit Skill
Goal: Generate a circuit

This skill generates a circuit based on YAML parameters.

# Generate Circuit

Goal: Build a Bell-state quantum circuit with two qubits and two classical bits.

The agent should prepare the entangled state, then measure both qubits.

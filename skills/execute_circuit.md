---
action: execute_circuit
backend: aer_simulator
shots: 256
output_counts: outputs/bell_counts_256.json
---
# Execute Circuit Skill
Goal: Execute the circuit and save counts

Controlled by YAML:
- shots
- output_counts

# Execute Circuit

Goal: Run the prepared circuit on a simulator backend and capture measurement counts.

Persist the counts as JSON for downstream analysis.

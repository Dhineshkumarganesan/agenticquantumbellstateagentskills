---
action: execute_circuit
shots: 100
backend: aer_simulator
constraints:
  min_shots: 256
  max_shots: 8192
  backend_locked: true
output_counts: outputs/counts.json
---

# Execute Circuit Skill

Runs the quantum circuit simulation using the Aer simulator.
- `shots`: Number of repetitions (default 1024)
- `backend`: Always `aer_simulator` for this POC
- Output: Raw measurement counts saved to outputs/counts.json

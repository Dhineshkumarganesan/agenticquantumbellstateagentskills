---
action: "generate_circuit"
circuit: "qaoa"
qubits: 4
measure: true
title: "QAOA MaxCut Circuit"
step_id: "qaoa_generate"
depends_on: []
goal: >
  Build a QAOA ansatz for MaxCut on a 4-node cycle graph
  with edges [(0,1),(1,2),(2,3),(3,0)] at depth p=1.
---

# QAOA MaxCut — Step 1: Circuit Generation

This skill generates a QAOA ansatz circuit for the MaxCut
problem on a 4-node cycle graph at depth p=1.

Paired with: `qaoa_execute_circuit.md`

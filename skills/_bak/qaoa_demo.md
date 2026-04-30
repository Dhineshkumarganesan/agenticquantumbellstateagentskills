steps:

  - action: "generate_circuit"
    circuit: "qaoa"
    qubits: 4
    measure: true
    title: "QAOA MaxCut Circuit"
    goal: >
      Build a QAOA ansatz for MaxCut on a 4-node cycle graph
      with edges [(0,1),(1,2),(2,3),(3,0)] at depth p=1.

  - action: "execute_circuit"
    shots: 1024
    seed: 42
    execution_mode: "stochastic"
    output_counts: "final_distribution"
    title: "QAOA MaxCut Optimisation"
    goal: >
      Optimise QAOA parameters using COBYLA to find
      the maximum cut. Expected optimal cut value is 4.
    variational_policy:
      optimizer: "COBYLA"
      max_iterations: 50
      parameter_bounds:
        - [0.0, 6.2832]
        - [0.0, 3.1416]

The runtime should optimize gamma and beta to maximize the |00⟩ outcome.
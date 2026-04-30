from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional, Any

from qiskit import QuantumCircuit
from .skills_loader import Skill  # Skill type hint
from .skills_loader import Skill



@dataclass
class RuntimeState:
    outputs_dir: str
    qc: Optional[QuantumCircuit] = None
    counts: Optional[dict] = None
    last_instruction: str = ""
    context: dict[str, Any] = None  # general stash


"""
runtime.py — Legacy compatibility shim.

All execution now routes through AgentRuntime in agent.py,
which correctly handles variational dispatch and parameter binding.

DO NOT add execution logic here. This file exists only so that
existing imports like `from agent_runtime.runtime import run`
don't break.
"""

from agent_runtime.agent import AgentRuntime

# Legacy entry point — now just delegates
def run(user_input: str = "") -> dict:
    """
    Legacy entry point. Delegates to AgentRuntime.run_agent().
    """
    runtime = AgentRuntime()
    return runtime.run_agent(user_input)

def execute_circuit(*args, **kwargs):
    raise RuntimeError(
        "execute_circuit() has been removed from runtime.py. "
        "Use AgentRuntime().run_agent() instead, which correctly "
        "dispatches variational vs direct execution. "
        "See agent_runtime/agent.py for the implementation."
    )

def execute_plan(*args, **kwargs):
    raise RuntimeError(
        "execute_plan() has been removed from runtime.py. "
        "Use AgentRuntime().run_agent() instead."
    )

    """
    Execute a validated plan. Each skill already has .validated_config
    attached by the governance firewall in agent._validate_plan().
    
    Pattern 1: YAML drives everything.
    Pattern 2: Only validated_config is read — never raw meta.
    """
    os.makedirs(state.outputs_dir, exist_ok=True)
    if state.context is None:
        state.context = {}
    results = []
    for skill in skills:
        config = skill.validated_config
        action = config.action
        goal = skill.goal or skill.title
        print(f"[Skill] {skill.filename} - action={action} - goal={goal}")
        if action == "generate_circuit":
            state.qc = generate_circuit(
                circuit_type=config.circuit,
                qubits=config.qubits,
                measure=config.measure,
                meta=dict(config),
            )
            results.append({"action": action, "status": "ok"})
        elif action == "execute_circuit":
            if state.qc is None:
                raise RuntimeError(
                    "Cannot execute: circuit is None (generate step missing)."
                )
            state.counts = execute_circuit(
                state.qc, config, state,
                output_counts=config.output_counts,
            )
            results.append({
                "action": action,
                "status": "ok",
                "counts": state.counts,
            })
        elif action == "draw_circuit":
            if state.qc is None:
                raise RuntimeError(
                    "Cannot draw: circuit is None (generate step missing)."
                )
            draw_circuit(
                state.qc,
                outputs_dir=state.outputs_dir,
                draw_output=config.draw_output,
                dpi=config.dpi,
                output_image=config.output_image,
                output_text=config.output_text,
            )
            results.append({
                "action": action,
                "status": "ok",
                "image": config.output_image,
            })
        elif action == "analyze_result":
            if state.counts is None:
                raise RuntimeError(
                    "Cannot analyze: counts is None (execute step missing)."
                )
            analyze_result(
                state.counts,
                expected_states=config.expected_states,
            )
            results.append({
                "action": action,
                "status": "ok",
                "expected_states": config.expected_states,
            })
        else:
            raise ValueError(
                f"Unknown action in skill '{skill.filename}': {action}"
            )
    return results


from qiskit.circuit import Parameter

def build_qaoa_circuit(meta: dict) -> QuantumCircuit:
    n_qubits = meta.get("qubits", 4)
    p_layers = meta.get("p", 1)
    measure = meta.get("measure", True)
    edges = meta.get("edges", [(i, (i + 1) % n_qubits) for i in range(n_qubits)])
    gammas = [Parameter(f"γ_{layer}") for layer in range(p_layers)]
    betas = [Parameter(f"β_{layer}") for layer in range(p_layers)]
    qc = QuantumCircuit(n_qubits)
    qc.h(range(n_qubits))
    for layer in range(p_layers):
        for i, j in edges:
            qc.cx(i, j)
            qc.rz(2 * gammas[layer], j)
            qc.cx(i, j)
        qc.rx(2 * betas[layer], range(n_qubits))
    if measure:
        qc.measure_all()
    print(f"[Runtime] Circuit generated: QAOA {n_qubits}q, {len(edges)} edges, p={p_layers}")
    return qc

def build_bell_circuit(meta: dict) -> QuantumCircuit:
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    if meta.get("measure", True):
        qc.measure_all()
    print("[Runtime] Circuit generated: Bell state")
    return qc

def build_ghz_circuit(meta: dict) -> QuantumCircuit:
    n_qubits = meta.get("qubits", 3)
    qc = QuantumCircuit(n_qubits)
    qc.h(0)
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)
    if meta.get("measure", True):
        qc.measure_all()
    print(f"[Runtime] Circuit generated: {n_qubits}-qubit GHZ")
    return qc

CIRCUIT_REGISTRY = {
    "qaoa": build_qaoa_circuit,
    "bell": build_bell_circuit,
    "ghz": build_ghz_circuit,
}

def generate_circuit(circuit_type: str = "bell", qubits: int = 2, measure: bool = True, meta: dict = None) -> QuantumCircuit:
    # meta is the full validated skill config (dict)
    if meta is None:
        meta = {"circuit": circuit_type, "qubits": qubits, "measure": measure}
    circuit_type = meta.get("circuit", "bell").lower()
    builder = CIRCUIT_REGISTRY.get(circuit_type)
    if builder is None:
        raise ValueError(f"Unknown circuit type: {circuit_type}. Available: {list(CIRCUIT_REGISTRY.keys())}")
    return builder(meta)


from .schema import ExecutionMode


def execute_variational(qc_template, validated_config, state, compute_cost):
    """
    Pattern 4: Agent defines bounds + policy, runtime owns the loop.
    The agent NEVER touches the optimization loop itself.
    """
    from qiskit_algorithms.optimizers import COBYLA, SPSA
    import numpy as np
    policy = validated_config.variational_policy
    if policy is None:
        raise ValueError("Variational skill requires variational_policy in YAML")
    OPTIMIZERS = {"COBYLA": COBYLA, "SPSA": SPSA}
    OptClass = OPTIMIZERS.get(policy.optimizer)
    if OptClass is None:
        raise ValueError(f"Unknown optimizer: {policy.optimizer}")
    optimizer = OptClass(maxiter=policy.max_iterations)
    print(f"[Runtime] Variational policy: {policy.optimizer}, max_iter={policy.max_iterations}")
    print(f"[Runtime] Parameter bounds: {policy.parameter_bounds}")
    print("[Runtime] Agent defined the WHAT. Runtime handles the HOW. 🔁")
    def cost_function(params):
        bound_circuit = qc_template.assign_parameters(params)
        counts = execute_circuit(
            bound_circuit, validated_config, state,
            output_counts=os.path.join(
                state.outputs_dir, ".variational_scratch.json"
            ),
        )
        return compute_cost(counts)
    initial_point = np.array([(lo + hi) / 2 for lo, hi in policy.parameter_bounds])
    result = optimizer.minimize(cost_function, initial_point)
    state.optimal_params = result.x
    state.optimal_cost = result.fun
    return result

def execute_circuit(
    qc: QuantumCircuit,
    validated_config,
    state,
    output_counts: str,
) -> dict:
    """
    Seed-mode duality in action:
    - deterministic → seeded simulator (reproducible)
    - stochastic   → true quantum sampling (no seed)
    """
    from qiskit_aer import AerSimulator
    backend = AerSimulator()
    shots = validated_config.shots
    run_options = {"shots": shots}
    if validated_config.execution_mode == ExecutionMode.DETERMINISTIC:
        run_options["seed_simulator"] = validated_config.seed
        print(f"[Runtime] DETERMINISTIC mode | seed={validated_config.seed}")
    else:
        print("[Runtime] STOCHASTIC mode | genuine quantum randomness")

    try:
        from qiskit import transpile
        tqc = transpile(qc, backend)
    except Exception:
        tqc = qc

    job = backend.run(tqc, **run_options)
    result = job.result()

    counts = result.get_counts()
    print(f"[Runtime] Counts: {counts} (shots={shots})")

    os.makedirs(os.path.dirname(output_counts) or ".", exist_ok=True)
    with open(output_counts, "w", encoding="utf-8") as f:
        json.dump(counts, f, indent=2, sort_keys=True)

    print(f"[Runtime] Saved counts -> {output_counts}")
    state.counts = counts
    return counts


def draw_circuit(
    qc: QuantumCircuit,
    outputs_dir: str,
    draw_output: str = "mpl",
    dpi: int = 200,
    output_image: str | None = None,
    output_text: str | None = None,
):
    if draw_output == "mpl":
        image_path = output_image or os.path.join(outputs_dir, "bell_diagram.png")
        fig = qc.draw(output="mpl")
        os.makedirs(os.path.dirname(image_path) or ".", exist_ok=True)
        fig.savefig(image_path, dpi=dpi, bbox_inches="tight")
        print(f"[Runtime] Saved diagram -> {image_path} (dpi={dpi})")
        return

    if draw_output == "text":
        text_path = output_text or os.path.join(outputs_dir, "bell_diagram.txt")
        diagram_text = str(qc.draw(output="text"))
        os.makedirs(os.path.dirname(text_path) or ".", exist_ok=True)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(diagram_text)
            if not diagram_text.endswith("\n"):
                f.write("\n")
        print(f"[Runtime] Saved text diagram -> {text_path}")
        return

    raise ValueError(f"Unsupported draw_output: {draw_output}")


def analyze_result(counts: dict, expected_states: list[str]):
    print("[Runtime] Analysis:")
    total = sum(counts.values()) if counts else 0
    print(f"  - total shots observed: {total}")
    for s in expected_states:
        print(f"  - {s}: {counts.get(s, 0)}")

    ok = all(counts.get(s, 0) > 0 for s in expected_states)
    if ok:
        print("  => Expected states observed; distribution looks plausible.")
    else:
        print("  => Expected states missing or zero; check circuit/measurement.")

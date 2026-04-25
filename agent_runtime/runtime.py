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


def execute_plan(state: RuntimeState, skills: list[Skill]) -> list[dict]:
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


def generate_circuit(circuit_type: str = "bell", qubits: int = 2, measure: bool = True) -> QuantumCircuit:
    circuit_type = circuit_type.lower()

    if circuit_type == "bell":
        if qubits != 2:
            raise ValueError("Bell circuit requires qubits=2")
        qc = QuantumCircuit(2, 2 if measure else 0)
        qc.h(0)
        qc.cx(0, 1)
        if measure:
            qc.measure([0, 1], [0, 1])
        print("[Runtime] Circuit generated: Bell state")
        return qc

    if circuit_type == "superposition":
        if qubits != 1:
            raise ValueError("superposition circuit requires qubits=1")
        qc = QuantumCircuit(1, 1 if measure else 0)
        qc.h(0)
        if measure:
            qc.measure([0], [0])
        print("[Runtime] Circuit generated: 1-qubit superposition")
        return qc

    if circuit_type == "ghz":
        if qubits < 3:
            raise ValueError("GHZ circuit requires qubits>=3")
        qc = QuantumCircuit(qubits, qubits if measure else 0)
        qc.h(0)
        for i in range(qubits - 1):
            qc.cx(i, i + 1)
        if measure:
            qc.measure(list(range(qubits)), list(range(qubits)))
        print(f"[Runtime] Circuit generated: {qubits}-qubit GHZ")
        return qc

    raise ValueError(f"Unknown circuit type: {circuit_type}")


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

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional, Any

from qiskit import QuantumCircuit
from .skills_loader import Skill


def _get_backend(backend_name: str = "aer_simulator"):
    # Prefer qiskit-aer AerSimulator
    try:
        from qiskit_aer import AerSimulator
        return AerSimulator()
    except Exception:
        from qiskit import Aer  # type: ignore
        return Aer.get_backend(backend_name)


@dataclass
class RuntimeState:
    outputs_dir: str
    qc: Optional[QuantumCircuit] = None
    counts: Optional[dict] = None
    last_instruction: str = ""
    context: dict[str, Any] = None  # general stash


def execute_plan(
    skills_list: list[str],
    instruction: str,
    state: RuntimeState,
    skills_catalog: dict[str, Skill],
):
    state.last_instruction = instruction
    os.makedirs(state.outputs_dir, exist_ok=True)
    if state.context is None:
        state.context = {}

    for filename in skills_list:
        skill = skills_catalog[filename]
        meta = skill.meta
        action = meta.get("action")

        print(f"[Skill] {filename} - action={action} - goal={skill.goal or skill.title}")

        if action == "generate_circuit":
            circuit_type = meta.get("circuit", "bell")
            qubits = int(meta.get("qubits", 2))
            measure = bool(meta.get("measure", True))
            state.qc = generate_circuit(circuit_type=circuit_type, qubits=qubits, measure=measure)

        elif action == "execute_circuit":
            if state.qc is None:
                raise RuntimeError("Cannot execute: circuit is None (generate step missing).")
            shots = int(meta.get("shots", 1024))
            backend = str(meta.get("backend", "aer_simulator"))
            output_counts = str(meta.get("output_counts", os.path.join(state.outputs_dir, "bell_counts.json")))
            state.counts = execute_circuit(state.qc, shots=shots, backend_name=backend, output_counts=output_counts)

        elif action == "draw_circuit":
            if state.qc is None:
                raise RuntimeError("Cannot draw: circuit is None (generate step missing).")
            draw_output = str(meta.get("draw_output", "mpl"))
            dpi = int(meta.get("dpi", 200))
            output_image = str(meta.get("output_image", os.path.join(state.outputs_dir, "bell_diagram.png")))
            output_text = str(meta.get("output_text", os.path.join(state.outputs_dir, "bell_diagram.txt")))
            draw_circuit(
                state.qc,
                outputs_dir=state.outputs_dir,
                draw_output=draw_output,
                dpi=dpi,
                output_image=output_image,
                output_text=output_text,
            )

        elif action == "analyze_result":
            if state.counts is None:
                raise RuntimeError("Cannot analyze: counts is None (execute step missing).")
            expected_states = meta.get("expected_states", ["00", "11"])
            analyze_result(state.counts, expected_states=list(expected_states))

        else:
            raise ValueError(f"Unknown action in skill '{filename}': {action}")


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


def execute_circuit(
    qc: QuantumCircuit,
    shots: int,
    backend_name: str,
    output_counts: str,
) -> dict:
    backend = _get_backend(backend_name)

    try:
        from qiskit import transpile
        tqc = transpile(qc, backend)
    except Exception:
        tqc = qc

    try:
        job = backend.run(tqc, shots=shots)
        result = job.result()
    except Exception:
        from qiskit import execute
        result = execute(tqc, backend, shots=shots).result()

    counts = result.get_counts()
    print(f"[Runtime] Counts: {counts} (shots={shots})")

    os.makedirs(os.path.dirname(output_counts) or ".", exist_ok=True)
    with open(output_counts, "w", encoding="utf-8") as f:
        json.dump(counts, f, indent=2, sort_keys=True)

    print(f"[Runtime] Saved counts -> {output_counts}")
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

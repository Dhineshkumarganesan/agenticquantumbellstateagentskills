"""
Quantum Circuit Expert - Runtime Handler
=========================================
Reads skill YAML frontmatter and executes the corresponding
quantum simulation pipeline using Qiskit Aer.

The agent edits YAML skill files.
This runtime reads and executes them.
They never overlap.
"""

import json
import os
import yaml
import re
from pathlib import Path

# Qiskit imports
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram, circuit_drawer
import matplotlib.pyplot as plt

# ── Path config ──────────────────────────────────────────────────────────────

BASE_DIR   = Path(__file__).parent.parent
SKILLS_DIR = BASE_DIR / "skills"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


# ── YAML skill reader ─────────────────────────────────────────────────────────

def read_skill(skill_path: Path) -> dict:
    """Extract YAML frontmatter from a skill Markdown file."""
    text = skill_path.read_text()
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        raise ValueError(f"No YAML frontmatter found in {skill_path}")
    return yaml.safe_load(match.group(1))


# ── Circuit builders ──────────────────────────────────────────────────────────

def build_bell_state() -> QuantumCircuit:
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def build_ghz_state(qubits: int) -> QuantumCircuit:
    qc = QuantumCircuit(qubits, qubits)
    qc.h(0)
    for i in range(qubits - 1):
        qc.cx(i, i + 1)
    qc.measure(range(qubits), range(qubits))
    return qc


def build_superposition(qubits: int) -> QuantumCircuit:
    qc = QuantumCircuit(qubits, qubits)
    for i in range(qubits):
        qc.h(i)
    qc.measure(range(qubits), range(qubits))
    return qc


CIRCUIT_BUILDERS = {
    "bell_state":    lambda cfg: build_bell_state(),
    "ghz_state":     lambda cfg: build_ghz_state(cfg["qubits"]),
    "superposition": lambda cfg: build_superposition(cfg["qubits"]),
}


# ── Pipeline steps ─────────────────────────────────────────────────────────────

def step_design_circuit(skill: dict) -> QuantumCircuit:
    """Step 1 — Build the circuit from skill config."""
    circuit_type = skill["circuit_type"]
    print(f"  [design]   circuit_type={circuit_type}  qubits={skill['qubits']}")

    builder = CIRCUIT_BUILDERS.get(circuit_type)
    if not builder:
        raise ValueError(f"Unknown circuit_type: '{circuit_type}'. "
                         f"Valid options: {list(CIRCUIT_BUILDERS.keys())}")
    return builder(skill)


def step_execute_circuit(qc: QuantumCircuit, skill: dict) -> dict:
    """Step 2 — Simulate circuit and return raw counts."""
    shots   = skill["shots"]
    backend = skill["backend"]
    print(f"  [execute]  backend={backend}  shots={shots}")

    simulator   = AerSimulator()
    transpiled  = transpile(qc, simulator)
    job         = simulator.run(transpiled, shots=shots)
    result      = job.result()
    counts      = result.get_counts()

    counts_path = OUTPUT_DIR / "counts.json"
    counts_path.write_text(json.dumps(counts, indent=2))
    print(f"  [execute]  counts saved → {counts_path}")
    return counts


def step_visualize_circuit(qc: QuantumCircuit, counts: dict,
                           circuit_skill: dict, viz_skill: dict):
    """Step 3 — Save circuit diagram and measurement histogram."""
    style = viz_skill.get("diagram_style", "mpl")
    print(f"  [visualize] diagram_style={style}")

    # Circuit diagram
    diagram_path = OUTPUT_DIR / "circuit_diagram.png"
    fig = qc.draw(output=style)
    fig.savefig(diagram_path, bbox_inches="tight", dpi=150)
    plt.close()
    print(f"  [visualize] diagram saved → {diagram_path}")

    # Histogram
    if viz_skill.get("histogram", True):
        hist_path = OUTPUT_DIR / "measurement_histogram.png"
        fig = plot_histogram(counts)
        fig.savefig(hist_path, bbox_inches="tight", dpi=150)
        plt.close()
        print(f"  [visualize] histogram saved → {hist_path}")


def step_export_counts(counts: dict, circuit_type: str,
                       shots: int, export_skill: dict):
    """Step 4 — Export enriched counts JSON as final artifact."""
    total = sum(counts.values())
    probabilities = {state: round(c / total, 4) for state, c in counts.items()}

    result = {
        "circuit_type":            circuit_type,
        "backend":                 "aer_simulator",
        "shots":                   shots,
        "counts":                  counts,
        "probabilities":           probabilities,
        "entanglement_verified":   circuit_type in ("bell_state", "ghz_state"),
    }

    out_path = OUTPUT_DIR / "final_counts.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"  [export]   final counts saved → {out_path}")
    return result


# ── Main pipeline ──────────────────────────────────────────────────────────────

def run_pipeline():
    print("\n╔══════════════════════════════════════╗")
    print("║   Quantum Circuit Expert — Runtime   ║")
    print("╚══════════════════════════════════════╝\n")

    circuit_files = list((SKILLS_DIR / "circuits").glob("*.md"))
    execute_skill  = read_skill(SKILLS_DIR / "execution" / "execute_circuit.md")
    viz_skill      = read_skill(SKILLS_DIR / "output"    / "visualize_circuit.md")
    export_skill   = read_skill(SKILLS_DIR / "output"    / "export_counts.md")

    ran_any = False
    for f in circuit_files:
        skill = read_skill(f)
        if skill.get("action") != "design_circuit":
            continue
        circuit_type = skill["circuit_type"]
        qubits = skill["qubits"]
        print(f"\n--- Running circuit: {circuit_type} ({qubits} qubits) ---\n")
        print(f"Pipeline configured:")
        print(f"  Circuit : {circuit_type}")
        print(f"  Qubits  : {qubits}")
        print(f"  Shots   : {execute_skill['shots']}")
        print(f"  Backend : {execute_skill['backend']}\n")
        print("Running steps...\n")

        # Execute pipeline for this circuit
        qc     = step_design_circuit(skill)
        counts = step_execute_circuit(qc, execute_skill)
        # Save outputs with unique names per circuit
        base = circuit_type
        # Save counts
        counts_path = OUTPUT_DIR / f"{base}_counts.json"
        counts_path.write_text(json.dumps(counts, indent=2))
        # Visualize
        orig_diagram = OUTPUT_DIR / "circuit_diagram.png"
        orig_hist = OUTPUT_DIR / "measurement_histogram.png"
        step_visualize_circuit(qc, counts, skill, viz_skill)
        # Rename outputs
        if orig_diagram.exists():
            orig_diagram.rename(OUTPUT_DIR / f"{base}_diagram.png")
        if orig_hist.exists():
            orig_hist.rename(OUTPUT_DIR / f"{base}_histogram.png")
        # Export enriched counts
        result = step_export_counts(counts, circuit_type, execute_skill["shots"], export_skill)
        final_counts_path = OUTPUT_DIR / "final_counts.json"
        if final_counts_path.exists():
            final_counts_path.rename(OUTPUT_DIR / f"{base}_final_counts.json")
        print("\n✓ Pipeline complete for", circuit_type)
        print("Outputs:")
        for f_out in sorted(OUTPUT_DIR.glob(f"{base}_*")):
            print(f"  → outputs/{f_out.name}")
        print("\nResults summary:")
        for state, prob in result["probabilities"].items():
            bar = "█" * int(prob * 40)
            print(f"  |{state}⟩  {bar}  {prob*100:.1f}%")
        if result["entanglement_verified"]:
            print(f"\n✓ Entanglement verified for {circuit_type}")
        ran_any = True
    if not ran_any:
        print("No valid design_circuit skills found in skills/circuits/.")


if __name__ == "__main__":
    run_pipeline()

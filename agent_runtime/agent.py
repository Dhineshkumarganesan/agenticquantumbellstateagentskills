from __future__ import annotations

import os


from .skills_loader import load_all_skills, Skill
from .audit import create_audit_record  # ← ADD THIS

DEFAULT_PLAN = [
    "generate_circuit.md",
    "optimize_circuit.md",
    "execute_circuit.md",
    "draw_circuit.md",
    "analyze_result.md",
]


from graphlib import TopologicalSorter, CycleError

# ------------------------------------
# RuntimeState — canonical definition
# Lives here to keep agent.py self-contained
# and break circular imports with runtime.py
# ------------------------------------

from dataclasses import dataclass, field
from typing import Any
from pathlib import Path
from qiskit.circuit import QuantumCircuit

@dataclass
class RuntimeState:
    """
    Mutable execution context threaded through the agent lifecycle.

    Constructed in AgentRuntime.__init__ as:
        RuntimeState(outputs_dir=self.outputs_dir)

    Then populated during execution:
        state.qc      → built/bound QuantumCircuit
        state.counts   → measurement results dict
    """
    # --- Set at construction time ---
    outputs_dir: Path | str = Path("outputs")

    # --- Populated during execution ---
    qc: QuantumCircuit | None = None          # current circuit (may have free params)
    counts: dict[str, int] | None = None      # measurement results after backend.run()

    # --- Variational / optimizer support ---
    parameters: dict[str, float] = field(default_factory=dict)
    status: str = "initialized"
    result: Any = None                        # final optimization result
    errors: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    def bind_current_parameters(self) -> QuantumCircuit:
        """
        Returns a copy of self.qc with all free parameters bound.
        This is the step that prevents AerError on simulation.
        """
        if self.qc is None:
            raise ValueError("No circuit (state.qc) to bind.")
        if not self.qc.parameters:
            return self.qc  # nothing to bind
        param_map = {
            p: self.parameters[p.name]
            for p in self.qc.parameters
            if p.name in self.parameters
        }
        if len(param_map) != len(self.qc.parameters):
            missing = {p.name for p in self.qc.parameters} - set(self.parameters)
            raise ValueError(f"Missing parameter values for: {missing}")
        return self.qc.assign_parameters(param_map)

    def save_counts(self, filename: str = "counts.json") -> Path:
        """Persist measurement results to outputs_dir."""
        import json
        out = Path(self.outputs_dir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / filename
        path.write_text(json.dumps(self.counts or {}, indent=2))
        return path

class AgentRuntime:
    def execute_plan(self, plan: list, state: "RuntimeState") -> "RuntimeState":
        """
        Walk through the plan steps and dispatch each one.
        Accepts both raw dicts and Skill objects — normalizes on entry.
        """
        from qiskit import transpile
        from qiskit_aer import AerSimulator

        # --------------------------------------------------
        # Normalize: Skill objects → dicts so dispatch is uniform
        # --------------------------------------------------
        # -----------------------------------------------
        # Skill name aliases: planner vocabulary → handler vocabulary
        # -----------------------------------------------
        SKILL_ALIASES = {
            # Build / Circuit Generation
            "generate_circuit":     "build",
            "build_circuit":        "build",
            "build_qaoa_circuit":   "build",
            "create_circuit":       "build",
            "construct_circuit":    "build",
            "build":                "build",

            # Optimize
            "optimize":             "optimize",
            "run_optimizer":        "optimize",
            "variational_loop":    "optimize",
            "optimize_parameters":  "optimize",
            "run_vqe":              "optimize",
            "run_qaoa":             "optimize",

            # Measure / Execute
            "execute_circuit":      "measure",
            "measure":              "measure",
            "simulate":             "measure",
            "run":                  "measure",
            "execute":              "measure",
            "sample":               "measure",
            "run_circuit":          "measure",

            # Save / Persist
            "save":                 "save",
            "save_results":         "save",
            "persist":              "save",
            "export":               "save",
        }

        def normalize_step(step) -> dict:
            if isinstance(step, dict):
                raw_skill = step.get("skill", "unknown")
                return {
                    "skill": SKILL_ALIASES.get(raw_skill, raw_skill),
                    "args": step.get("args", step),
                }
            meta = getattr(step, "meta", None)
            if meta is None or not isinstance(meta, dict):
                return {
                    "skill": "unknown",
                    "args": {},
                    "_raw_type": type(step).__name__,
                    "_debug": repr(step)[:200],
                }
            raw_action = meta.get("action", "unknown")
            canonical  = SKILL_ALIASES.get(raw_action, raw_action)
            skill_args = {k: v for k, v in meta.items() if k != "action"}
            skill_args["_skill_title"]    = getattr(step, "title", "")
            skill_args["_skill_goal"]     = getattr(step, "goal", "")
            skill_args["_skill_body"]     = getattr(step, "body", "")
            skill_args["_skill_filename"] = getattr(step, "filename", "")
            return {"skill": canonical, "args": skill_args}

        normalized_plan = [normalize_step(s) for s in plan]

        # -----------------------------------------------
        # 🛡️ Safety net: auto-insert "optimize" if missing
        # -----------------------------------------------
        step_skills = [s["skill"] for s in normalized_plan]
        has_build    = "build" in step_skills
        has_optimize = "optimize" in step_skills
        has_measure  = "measure" in step_skills
        if has_build and has_measure and not has_optimize:
            measure_idx = step_skills.index("measure")
            optimize_step = {
                "skill": "optimize",
                "args": {
                    "method": "COBYLA",
                    "maxiter": 100,
                },
            }
            normalized_plan.insert(measure_idx, optimize_step)
            print("🛡️  Auto-inserted 'optimize' step — can't measure unbound parameters!")
            print(f"   New plan order: {[s['skill'] for s in normalized_plan]}")
            print()

        audit_trail = []

        print(f"📋 Executing {len(normalized_plan)} steps:")
        for i, step in enumerate(normalized_plan):
            print(f"   {i+1}. {step['skill']}({[k for k in step['args'] if not k.startswith('_')]})")
        print()

        for i, step in enumerate(normalized_plan):
            skill = step["skill"]
            args  = step["args"]
            clean_args = {k: v for k, v in args.items() if not k.startswith("_")}
            print(f"⚡ Step {i+1}/{len(normalized_plan)}: {skill}")
            step_result = {"step": i + 1, "skill": skill, "status": "pending"}
            try:
                # ---- BUILD ----
                if skill in ("build_qaoa_circuit", "build_circuit", "build"):
                    state.qc = self._build_qaoa_circuit(**clean_args)
                    # Stash edges for the optimizer's cost function
                    state._problem_edges = clean_args.get(
                        "edges",
                        [(i, i+1) for i in range(clean_args.get("n_qubits", 4) - 1)]
                        + [(clean_args.get("n_qubits", 4) - 1, 0)]
                    )
                    state.status = "circuit_built"
                    step_result["status"] = "success"
                    step_result["qubits"] = state.qc.num_qubits
                    step_result["params"] = len(state.qc.parameters)
                    print(f"   ✅ Circuit: {state.qc.num_qubits}q, "
                          f"{len(state.qc.parameters)} params")

                # ---- OPTIMIZE ----
                elif skill in ("optimize", "run_optimizer", "variational_loop"):
                    state = self._run_variational_loop(state, **clean_args)
                    state.status = "optimized"
                    step_result["status"] = "success"
                    print(f"   ✅ Optimization complete")

                # ---- MEASURE / SIMULATE ----
                elif skill in ("measure", "simulate", "run", "execute"):
                    state = self._measure(state, **clean_args)
                    state.status = "measured"
                    step_result["status"] = "success"
                    top = dict(sorted(state.counts.items(), key=lambda x: -x[1])[:3])
                    step_result["top_counts"] = top
                    print(f"   ✅ Measured — top: {top}")

                # ---- SAVE ----
                elif skill in ("save", "save_results", "persist"):
                    path = state.save_counts(clean_args.get("filename", "counts.json"))
                    step_result["status"] = "success"
                    step_result["path"] = str(path)
                    print(f"   💾 Saved → {path}")

                # ---- UNKNOWN ----
                else:
                    msg = f"Unknown skill: '{skill}'"
                    state.errors.append(msg)
                    step_result["status"] = "skipped"
                    step_result["reason"] = msg
                    print(f"   ⚠️  {msg}")

            except Exception as e:
                state.errors.append(f"Step {i+1} ({skill}): {e}")
                state.status = "error"
                step_result["status"] = "error"
                step_result["error"] = str(e)
                print(f"   ❌ {e}")
                raise

            audit_trail.append(step_result)

        state.status = "complete" if not state.errors else "completed_with_errors"
        state.audit_trail = audit_trail  # attach for downstream consumers
        return state

    def _build_qaoa_circuit(self, **kwargs) -> "QuantumCircuit":
        from qiskit.circuit import QuantumCircuit, Parameter
        import numpy as np
        n_qubits = kwargs.get("n_qubits", 4)
        p_layers = kwargs.get("p", kwargs.get("layers", 1))
        edges    = kwargs.get("edges", [(0,1), (1,2), (2,3), (3,0)])
        qc = QuantumCircuit(n_qubits)
        qc.h(range(n_qubits))
        for layer in range(p_layers):
            gamma = Parameter(f"γ_{layer}")
            beta  = Parameter(f"β_{layer}")
            for (i, j) in edges:
                qc.cx(i, j)
                qc.rz(2 * gamma, j)
                qc.cx(i, j)
            for i in range(n_qubits):
                qc.rx(2 * beta, i)
        qc.measure_all()
        return qc

    def _run_variational_loop(self, state: "RuntimeState", **kwargs) -> "RuntimeState":
        from scipy.optimize import minimize
        from qiskit_aer import AerSimulator
        from qiskit import transpile
        import numpy as np
        backend    = AerSimulator()
        max_iter   = kwargs.get("max_iter", kwargs.get("maxiter", 100))
        shots      = kwargs.get("shots", 1024)
        param_names = [p.name for p in state.qc.parameters]
        def cost_function(param_values):
            state.parameters = dict(zip(param_names, param_values))
            bound_qc = state.bind_current_parameters()
            t_qc = transpile(bound_qc, backend)
            result = backend.run(t_qc, shots=shots).result()
            counts = result.get_counts()
            edges = kwargs.get("edges", [(0,1), (1,2), (2,3), (3,0)])
            avg_cost = 0.0
            for bitstring, count in counts.items():
                bits = [int(b) for b in bitstring]
                cut = sum(bits[i] != bits[j] for i, j in edges)
                avg_cost += cut * count
            avg_cost /= shots
            return -avg_cost
        x0 = np.random.uniform(0, 2 * np.pi, len(param_names))
        opt_result = minimize(
            cost_function,
            x0,
            method=kwargs.get("method", "COBYLA"),
            options={"maxiter": max_iter}
        )
        state.parameters = dict(zip(param_names, opt_result.x))
        state.result = {
            "optimal_value": -opt_result.fun,
            "optimal_params": state.parameters,
            "n_iterations": opt_result.nfev,
        }
        return state

    def _measure(self, state: "RuntimeState", **kwargs) -> "RuntimeState":
        from qiskit_aer import AerSimulator
        from qiskit import transpile
        backend = AerSimulator()
        shots   = kwargs.get("shots", 4096)
        bound_qc = state.bind_current_parameters()
        t_qc = transpile(bound_qc, backend)
        result = backend.run(t_qc, shots=shots).result()
        state.counts = dict(result.get_counts())
        return state


    def __init__(self, skills_dir: str | None = None, outputs_dir: str = "outputs"):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.repo_root = repo_root
        self.skills_dir = skills_dir or os.path.join(repo_root, "skills")
        self.outputs_dir = outputs_dir if os.path.isabs(outputs_dir) else os.path.join(repo_root, outputs_dir)

        self.skills = load_all_skills(self.skills_dir)
        self.state = RuntimeState(outputs_dir=self.outputs_dir)

    def help_text(self) -> str:
        available = "\n".join([f"- {k}" for k in self.skills.keys()]) or "(no skills found)"
        return (
            "Commands:\n"
            "  /run-agent <instruction>   Run agentic workflow\n"
            "  /run-traditional           Run non-agentic workflow\n"
            "  /draw-last                 Draw last circuit again\n"
            "  /analyze-last              Analyze last counts again\n"
            "  /help                      Show this help\n"
            "  /exit or /quit             Quit\n\n"
            f"Skills dir: {self.skills_dir}\n"
            f"Outputs dir: {self.outputs_dir}\n\n"
            "Detected skills:\n"
            f"{available}\n"
        )

    def build_plan(self, instruction: str = None) -> list[str]:
        """
        Build a dependency-aware plan using step_id/depends_on fields in skill frontmatter.
        If instruction is provided, can filter for relevant skills (future extension).
        """
        # Map step_id to skill key (filename)
        stepid_to_key = {}
        for k, skill in self.skills.items():
            step_id = skill.meta.get("step_id")
            if step_id:
                stepid_to_key[step_id] = k
        # Build dependency graph
        graph = {}
        for k, skill in self.skills.items():
            step_id = skill.meta.get("step_id")
            depends_on = skill.meta.get("depends_on", [])
            if step_id:
                graph[step_id] = set(depends_on)
        try:
            sorter = TopologicalSorter(graph)
            ordered_ids = list(sorter.static_order())
        except CycleError as e:
            raise RuntimeError(f"Circular dependency in skills: {e}")
        # Only include skills that exist in this agent's loaded set
        plan = [stepid_to_key[sid] for sid in ordered_ids if sid in stepid_to_key]
        print("\n📋 Execution plan:")
        for i, sid in enumerate(plan, 1):
            skill = self.skills[sid]
            deps = skill.meta.get("depends_on", [])
            dep_str = f" → after [{', '.join(deps)}]" if deps else " (root)"
            print(f"  {i}. [{skill.meta.get('step_id')}] {skill.meta.get('action')}{dep_str}")
        print()
        return plan

    def _validate_plan(self, plan: list[str]):
        """
        Pattern 2: Schema-governed firewall.
        Every skill MUST pass Pydantic validation before execution.
        """
        from .schema import validate_skill_config
        for step in plan:
            skill = self.skills[step]
            try:
                # Use schema_meta to strip planning fields before validation
                validated = validate_skill_config(skill.schema_meta)
                skill.validated_config = validated
                print(f"[Governance] ✅ {step} validated ({validated.action})")
            except Exception as e:
                raise RuntimeError(
                    f"[Governance] ❌ Skill '{step}' failed validation: {e}"
                ) from e

    def run_agent(self, instruction: str):
        print("\n[Agent] Step 1: Parsing instruction...")
        print(f"[Agent] Instruction: {instruction}")

        plan = self.build_plan(instruction)
        self._validate_plan(plan)

        print("[Agent] Step 2: Plan (YAML-driven skills):")
        for step in plan:
            sk = self.skills[step]
            goal = sk.goal or sk.title
            action = sk.validated_config.action  # ← use validated, not raw meta
            print(f"  - {step} :: action={action} :: {goal}")

        print("[Agent] Step 3: Execute plan...")
        skills_in_plan = [self.skills[p] for p in plan]
        state = self.execute_plan(skills_in_plan, self.state)  # 🐛 FIX: single return value

        print("[Agent] Step 4: Writing audit trail...")
        if hasattr(state, "audit_trail") and state.audit_trail:
            for entry in state.audit_trail:
                step = entry.get("skill", "unknown")
                skill = self.skills.get(step)
                create_audit_record(
                    skill_name=step,
                    config_dict=skill.validated_config.model_dump() if skill and hasattr(skill, "validated_config") else {},
                    results=entry,
                    outputs_dir=self.outputs_dir,
                )
        print("[Agent] ✅ All steps complete. Audit trail written.")
        return state

    def draw_last(self):
        if self.state.qc is None:
            print("No circuit in memory. Run /run-agent first.")
            return
        
        draw_circuit(self.state.qc, self.outputs_dir, output_image=os.path.join(self.outputs_dir, "bell_diagram.png"))

    def analyze_last(self):
        if self.state.counts is None:
            print("No counts in memory. Run /run-agent first.")
            return
        
        skill = self.skills.get("analyze_result.md")
        if skill and hasattr(skill, "validated_config"):
            expected = skill.validated_config.expected_states
        else:
            expected = ["00", "11"]  # sensible default
        analyze_result(self.state.counts, expected_states=expected)
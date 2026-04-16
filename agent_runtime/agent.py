from __future__ import annotations

import os

from .runtime import RuntimeState, execute_plan
from .skills_loader import load_all_skills, Skill

DEFAULT_PLAN = [
    "generate_circuit.md",
    "execute_circuit.md",
    "draw_circuit.md",
    "analyze_result.md",
]


class AgentRuntime:
    def __init__(self, skills_dir: str | None = None):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.repo_root = repo_root
        self.skills_dir = skills_dir or os.path.join(repo_root, "skills")
        self.outputs_dir = os.path.join(repo_root, "outputs")

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

    def build_plan(self, instruction: str) -> list[str]:
        """
        YAML is the source of truth for parameters (shots/output/etc).
        Instruction only controls which steps to include/exclude.
        """
        text = instruction.lower()
        plan = list(DEFAULT_PLAN)

        if "no draw" in text or "skip draw" in text:
            plan = [p for p in plan if p != "draw_circuit.md"]

        if "only generate" in text:
            plan = ["generate_circuit.md"]

        return plan

    def _validate_plan(self, plan: list[str]) -> None:
        missing = [p for p in plan if p not in self.skills]
        if missing:
            raise FileNotFoundError(
                "Missing required skill files in skills/: " + ", ".join(missing)
            )

        # Basic validation: each skill should have an action
        bad = []
        for p in plan:
            action = self.skills[p].meta.get("action")
            if not action:
                bad.append(p)
        if bad:
            raise ValueError(
                "Skills missing YAML 'action' in frontmatter: " + ", ".join(bad)
            )

    def run_agent(self, instruction: str):
        print("\n[Agent] Step 1: Parsing instruction...")
        print(f"[Agent] Instruction: {instruction}")

        plan = self.build_plan(instruction)
        self._validate_plan(plan)

        print("[Agent] Step 2: Plan (YAML-driven skills):")
        for step in plan:
            sk: Skill = self.skills[step]
            goal = sk.goal or sk.title
            action = sk.meta.get("action")
            print(f"  - {step} :: action={action} :: {goal}")

        print("[Agent] Step 3: Execute plan...")
        execute_plan(plan, instruction, self.state, self.skills)
        print("[Agent] Done.")

    def draw_last(self):
        if self.state.qc is None:
            print("No circuit in memory. Run /run-agent first.")
            return
        from .runtime import draw_circuit
        draw_circuit(self.state.qc, self.outputs_dir, output_image=os.path.join(self.outputs_dir, "bell_diagram.png"))

    def analyze_last(self):
        if self.state.counts is None:
            print("No counts in memory. Run /run-agent first.")
            return
        from .runtime import analyze_result
        analyze_result(self.state.counts, expected_states=["00", "11"])
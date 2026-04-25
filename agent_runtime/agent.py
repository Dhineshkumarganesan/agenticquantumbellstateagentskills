from __future__ import annotations

import os

from .runtime import RuntimeState, execute_plan
from .skills_loader import load_all_skills, Skill
from .audit import create_audit_record  # ← ADD THIS

DEFAULT_PLAN = [
    "generate_circuit.md",
    "execute_circuit.md",
    "draw_circuit.md",
    "analyze_result.md",
]


class AgentRuntime:
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

    def _validate_plan(self, plan: list[str]):
        """
        Pattern 2: Schema-governed firewall.
        Every skill MUST pass Pydantic validation before execution.
        """
        from .schema import validate_skill_config
        for step in plan:
            skill = self.skills[step]
            try:
                validated = validate_skill_config(skill.meta)
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
        results = execute_plan(self.state, skills_in_plan)  # ← fixed signature

        print("[Agent] Step 4: Writing audit trail...")
        for step, result in zip(plan, results):
            skill = self.skills[step]
            create_audit_record(
                skill_name=step,
                config_dict=skill.validated_config.model_dump(),
                results=result,
                outputs_dir=self.outputs_dir,
            )
        print("[Agent] ✅ All steps complete. Audit trail written.")
        return results

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
        skill = self.skills.get("analyze_result.md")
        if skill and hasattr(skill, "validated_config"):
            expected = skill.validated_config.expected_states
        else:
            expected = ["00", "11"]  # sensible default
        analyze_result(self.state.counts, expected_states=expected)
from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator

class ExecutionMode(str, Enum):
    """Seed-mode duality: deterministic vs stochastic"""
    DETERMINISTIC = "deterministic"
    STOCHASTIC = "stochastic"

class VariationalPolicy(BaseModel):
    """Pattern 4: Agents define bounds + policy, runtime owns the loop"""
    optimizer: str = Field(
        default="COBYLA",
        description="Optimizer name (COBYLA, SPSA, etc.)"
    )
    max_iterations: int = Field(default=100, ge=1, le=10000)
    parameter_bounds: list[tuple[float, float]] = Field(
        default_factory=list,
        description="(min, max) for each variational parameter"
    )
    @field_validator("parameter_bounds")
    @classmethod
    def bounds_are_valid(cls, v):
        for pair in v:
            if pair[0] >= pair[1]:
                raise ValueError(
                    f"Lower bound {pair[0]} must be < upper bound {pair[1]}"
                )
        return v

# --- Per-action schemas ---

class GenerateCircuitSchema(BaseModel):
    action: Literal["generate_circuit"]
    circuit: str = Field(default="bell")
    qubits: int = Field(default=2, ge=1, le=20)
    measure: bool = Field(default=True)
    title: Optional[str] = None
    goal: Optional[str] = None
    class Config:
        extra = "forbid"

class DrawCircuitSchema(BaseModel):
    action: Literal["draw_circuit"]
    draw_output: str = Field(default="mpl")
    dpi: int = Field(default=200, ge=50, le=1200)
    output_image: str = Field(default="outputs/bell_diagram.png")
    output_text: str = Field(default="outputs/bell_diagram.txt")  # ← ADD THIS
    title: Optional[str] = None
    goal: Optional[str] = None
    class Config:
        extra = "forbid"

class ExecuteCircuitSchema(BaseModel):
    action: Literal["execute_circuit"]
    shots: int = Field(default=1024, ge=1, le=100_000)
    seed: Optional[int] = Field(default=None, ge=0)
    execution_mode: ExecutionMode = Field(default=ExecutionMode.DETERMINISTIC)
    output_counts: str = Field(default="outputs/bell_counts.json")
    variational_policy: Optional[VariationalPolicy] = None
    title: Optional[str] = None
    goal: Optional[str] = None

    @model_validator(mode="after")
    def _check_seed_mode_consistency(self):
        import warnings
        if self.execution_mode == ExecutionMode.DETERMINISTIC and self.seed is None:
            self.seed = 42
            warnings.warn(
                "DETERMINISTIC mode requires a seed. Auto-assigned seed=42."
            )
        if self.execution_mode == ExecutionMode.STOCHASTIC and self.seed is not None:
            warnings.warn(
                f"STOCHASTIC mode ignores seed={self.seed}. Setting to None."
            )
            self.seed = None
        return self

    class Config:
        extra = "forbid"

class AnalyzeResultSchema(BaseModel):
    action: Literal["analyze_result"]
    expected_states: list[str] = Field(default=["00", "11"])  # ← ADD THIS
    title: Optional[str] = None
    goal: Optional[str] = None
    class Config:
        extra = "forbid"

# --- Action to schema mapping ---
# --- Schema dispatcher ---
_ACTION_SCHEMA_MAP = {
    "generate_circuit": GenerateCircuitSchema,
    "execute_circuit": ExecuteCircuitSchema,
    "draw_circuit": DrawCircuitSchema,
    "analyze_result": AnalyzeResultSchema,
}

def validate_skill_config(meta: dict) -> BaseModel:
    """
    Pattern 2: Schema-governed execution.
    Routes a skill's YAML metadata to the correct Pydantic schema.
    Raises ValidationError if anything is off.
    """
    action = meta.get("action")
    if not action:
        raise ValueError(f"Skill metadata missing 'action' key: {meta}")
    schema_cls = _ACTION_SCHEMA_MAP.get(action)
    if schema_cls is None:
        raise ValueError(
            f"Unknown action '{action}'. "
            f"Valid actions: {list(_ACTION_SCHEMA_MAP.keys())}"
        )
    return schema_cls.model_validate(meta)  # Pydantic v2
    # return schema_cls(**meta)             # ← use this for Pydantic v1


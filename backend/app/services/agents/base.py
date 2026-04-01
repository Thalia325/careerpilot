from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowState:
    workflow: str
    steps: list[str] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)


class BaseAgent:
    name = "base"

    def add_step(self, state: WorkflowState, message: str) -> None:
        state.steps.append(f"{self.name}: {message}")


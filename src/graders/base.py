from __future__ import annotations

from abc import ABC, abstractmethod


class BaseGrader(ABC):
    """Abstract grader for incident response tasks."""

    @abstractmethod
    def grade(self, action_history: list[dict], state: dict) -> float:
        """
        Compute total cumulative score given action history and current state.
        Returns float in [0.0, 1.0].
        """
        ...

    @abstractmethod
    def get_checkpoints(self) -> dict[str, float]:
        """Return mapping of checkpoint_name -> reward weight."""
        ...

    def compute_delta_reward(
        self,
        prev_checkpoints: list[str],
        new_checkpoints: list[str],
        penalties: float,
    ) -> tuple[float, list[str], str]:
        """
        Compute incremental reward: sum of newly hit checkpoint weights minus penalties.
        Returns (delta_reward, newly_hit_checkpoints, reason_string).
        """
        checkpoints = self.get_checkpoints()
        newly_hit = [c for c in new_checkpoints if c not in prev_checkpoints]
        gained = sum(checkpoints.get(c, 0.0) for c in newly_hit)
        delta = gained - penalties
        # Clamp to [-1.0, 1.0]
        delta = max(-1.0, min(1.0, delta))
        reason_parts = []
        if newly_hit:
            reason_parts.append(f"Unlocked: {', '.join(newly_hit)} (+{gained:.2f})")
        if penalties > 0:
            reason_parts.append(f"Penalty: -{penalties:.2f}")
        reason = "; ".join(reason_parts) if reason_parts else "No new progress"
        return delta, newly_hit, reason

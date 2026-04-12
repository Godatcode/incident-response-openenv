from __future__ import annotations

from abc import ABC, abstractmethod


class BaseGrader(ABC):
    """Abstract grader for incident response tasks."""

    @abstractmethod
    def grade(self, action_history: list[dict], state: dict) -> float:
        """
        Compute total cumulative score given action history and current state.
        Returns float strictly within (0, 1) — never 0.0 or 1.0.
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
    ) -> tuple[float, float, list[str], str]:
        """
        Compute incremental reward.

        Returns:
          public_delta: reward emitted by the environment, clamped to [0, 1]
          raw_delta: underlying delta before public clamping, clamped to [-1, 1]
          newly_hit: newly unlocked checkpoints
          reason: human-readable explanation

        The public reward is kept non-negative because the evaluator contract
        expects reward values in [0, 1]. Penalties still affect internal
        cumulative scoring through raw_delta.
        """
        checkpoints = self.get_checkpoints()
        newly_hit = [c for c in new_checkpoints if c not in prev_checkpoints]
        gained = sum(checkpoints.get(c, 0.0) for c in newly_hit)
        raw_delta = max(-1.0, min(1.0, gained - penalties))
        public_delta = max(0.0, min(1.0, raw_delta))
        reason_parts = []
        if newly_hit:
            reason_parts.append(f"Unlocked: {', '.join(newly_hit)} (+{gained:.2f})")
        if penalties > 0:
            reason_parts.append(f"Penalty: -{penalties:.2f}")
        reason = "; ".join(reason_parts) if reason_parts else "No new progress"
        return public_delta, raw_delta, newly_hit, reason

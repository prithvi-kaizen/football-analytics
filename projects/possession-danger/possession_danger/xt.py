from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


def cells(x, y, nx: int, ny: int) -> np.ndarray:
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if not ((np.isfinite(x) & np.isfinite(y) & (x >= 0) & (x <= 120) & (y >= 0) & (y <= 80)).all()):
        raise ValueError("Invalid grid coordinates")
    return np.minimum((y / 80 * ny).astype(int), ny-1) * nx + np.minimum((x / 120 * nx).astype(int), nx-1)


@dataclass
class XT:
    nx: int = 12
    ny: int = 8

    def fit(self, actions: pd.DataFrame, tolerance: float = 1e-10, max_iter: int = 10000):
        if actions.empty:
            raise ValueError("Cannot fit an empty xT model")
        n = self.nx * self.ny
        start = cells(actions.x, actions.y, self.nx, self.ny)
        count = np.bincount(start, minlength=n).astype(float)
        success = actions.type.isin(["Pass", "Carry"]) & actions.complete
        shots = actions.type.eq("Shot")
        goals = shots & actions.goal
        reward = np.bincount(start[goals], minlength=n) / np.maximum(count, 1)
        transition = np.zeros((n, n))
        ends = cells(actions.loc[success, "end_x"], actions.loc[success, "end_y"], self.nx, self.ny)
        np.add.at(transition, (start[success], ends), 1)
        transition /= np.maximum(count[:, None], 1)
        value = np.zeros(n)
        for iteration in range(1, max_iter + 1):
            updated = reward + transition @ value
            if np.max(np.abs(updated - value)) < tolerance:
                value = updated
                break
            value = updated
        else:
            raise RuntimeError("xT fixed point did not converge")
        self.value, self.transition, self.reward, self.count = value, transition, reward, count
        self.shot_probability = np.bincount(start[shots], minlength=n) / np.maximum(count, 1)
        self.train_matches = sorted(map(int, actions.match_id.unique()))
        self.iterations = iteration
        self.residual = float(np.max(np.abs(value - reward - transition @ value)))
        if (value < -1e-10).any() or (value > 1 + 1e-10).any():
            raise ValueError("Invalid xT probabilities")
        return self

    def rate(self, actions: pd.DataFrame) -> pd.DataFrame:
        result = actions.copy()
        start = cells(result.x, result.y, self.nx, self.ny)
        result["start_xt"] = self.value[start]
        result["xt_delta"] = 0.0
        success = result.type.isin(["Pass", "Carry"]) & result.complete
        end = cells(result.loc[success, "end_x"], result.loc[success, "end_y"], self.nx, self.ny)
        result.loc[success, "xt_delta"] = self.value[end] - result.loc[success, "start_xt"]
        result["positive_xt"] = result.xt_delta.clip(lower=0)
        # Turnovers are an optional diagnostic, separate from standard successful-move xT.
        failed = result.type.isin(["Pass", "Carry"]) & ~result.complete | result.type.isin(["Miscontrol", "Dispossessed", "Dribble"])
        result["turnover_xt"] = np.where(failed, -result.start_xt, 0.0)
        return result

    def evaluate(self, heldout: pd.DataFrame) -> dict:
        if set(heldout.match_id) & set(self.train_matches):
            raise ValueError("Train/test match leakage")
        start = cells(heldout.x, heldout.y, self.nx, self.ny)
        actual = heldout.type.eq("Shot").to_numpy(float)
        pred = self.shot_probability[start]
        train_rate = float(np.sum(self.shot_probability * self.count) / self.count.sum())
        return {"heldout_actions": len(heldout), "unseen_cell_fraction": float(np.mean(self.count[start] == 0)),
                "shot_choice_brier": float(np.mean((pred - actual) ** 2)),
                "constant_shot_choice_brier": float(np.mean((train_rate - actual) ** 2)),
                "meaning": "One-step shot-choice diagnostic; not a validation of possession-goal probability or causal action value."}

    def to_dict(self) -> dict:
        return {"nx": self.nx, "ny": self.ny, "value": self.value.reshape(self.ny, self.nx).tolist(),
                "counts": self.count.reshape(self.ny, self.nx).tolist(),
                "reward": self.reward.tolist(), "transition": self.transition.tolist(),
                "train_matches": self.train_matches, "iterations": self.iterations, "residual": self.residual,
                "target": "Empirical goals from non-penalty shots; failed moves and explicit losses absorb at zero"}

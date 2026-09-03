"""Realistic demo-data generator.

The generated data is NOT random noise — it encodes plausible human rhythms
via a hidden "day-type" archetype: focused workdays, recovery weekends, social
weekends, and low-energy days that follow a run of late nights. An exam week
overlays extra stress and study. This structure lets the clustering module
discover meaningful life patterns (rather than being told about them).
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np

WEATHERS = ["晴", "多云", "阴", "小雨", "晴", "多云"]


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _round1(value: float) -> float:
    return round(float(value), 1)


def generate_demo_data(days: int = 60, end_date: date | None = None, seed: int = 42) -> list[dict]:
    """Generate ``days`` days of realistic records ending at ``end_date``."""
    rng = np.random.RandomState(seed)
    end = end_date or date.today()
    dates = [end - timedelta(days=days - 1 - i) for i in range(days)]

    exam_start = max(0, days // 2 - 2)  # 6-day exam week
    late_streak = 0  # consecutive late nights so far

    records: list[dict] = []

    for i, d in enumerate(dates):
        is_weekend = d.weekday() >= 5
        in_exam = exam_start <= i < exam_start + 6

        # --- Determine the hidden day-type archetype -----------------------
        if in_exam:
            mode = "focus"
        elif is_weekend:
            mode = "social" if rng.rand() < 0.4 else "recover"
        else:
            mode = "low" if (late_streak >= 2 or rng.rand() < 0.12) else "focus"

        # --- Draw each variable per mode -----------------------------------
        if mode == "focus":
            sleep = rng.normal(6.9, 0.4)
            study = rng.normal(8.2, 1.0)
            exercise = _clip(rng.exponential(0.45), 0, 3) if rng.rand() < 0.5 else 0.0
            ent = rng.normal(1.3, 0.5)
            social = int(_clip(rng.poisson(0.9), 0, 5))
            spending = rng.gamma(2.0, 22)
            stress = rng.normal(5.2, 1.2)
            p_stay = 0.12
        elif mode == "recover":
            sleep = rng.normal(8.9, 0.5)
            study = rng.normal(2.0, 0.8)
            exercise = rng.normal(1.0, 0.5)
            ent = rng.normal(4.1, 1.0)
            social = int(_clip(rng.poisson(1.6), 0, 5))
            spending = rng.gamma(2.4, 30)
            stress = rng.normal(3.6, 1.0)
            p_stay = 0.15
        elif mode == "social":
            sleep = rng.normal(8.1, 0.5)
            study = rng.normal(3.0, 1.0)
            exercise = rng.normal(0.6, 0.5)
            ent = rng.normal(3.2, 1.0)
            social = int(_clip(rng.poisson(4.5), 1, 8))
            spending = rng.gamma(2.8, 55)
            stress = rng.normal(4.2, 1.0)
            p_stay = 0.35
        else:  # "low"
            sleep = rng.normal(5.2, 0.4)
            study = rng.normal(3.5, 1.0)
            exercise = 0.0
            ent = rng.normal(4.6, 1.0)
            social = int(_clip(rng.poisson(0.5), 0, 3))
            spending = rng.gamma(2.0, 25)
            stress = rng.normal(7.6, 1.0)
            p_stay = 0.7

        if in_exam:
            study += 2.5
            stress += 2.0
            p_stay += 0.15

        sleep = _round1(_clip(sleep, 4.5, 10.5))
        study = _round1(_clip(study, 0, 12))
        exercise = _round1(_clip(exercise, 0, 3))
        ent = _round1(_clip(ent, 0, 8))
        spending = round(_clip(spending, 0, 2500) * (4.0 if rng.rand() < 0.04 else 1.0), 2)
        stress = int(_clip(round(stress), 1, 10))

        stay_up = bool(rng.rand() < p_stay)
        late_streak = late_streak + 1 if stay_up else 0

        mood = int(
            _clip(
                round(
                    6.0
                    + (sleep - 7.0) * 0.6
                    - (stress - 5.0) * 0.35
                    - (0.9 if stay_up else 0.0)
                    + rng.normal(0, 0.6)
                ),
                1,
                10,
            )
        )

        p_plan = 0.75 - (0.25 if stay_up else 0.0) - (0.1 if in_exam else 0.0)
        plan = bool(rng.rand() < p_plan)

        records.append(
            {
                "date": d,
                "sleep_hours": sleep,
                "study_hours": study,
                "exercise_hours": exercise,
                "entertainment_hours": ent,
                "social_count": social,
                "spending": spending,
                "mood": mood,
                "stress": stress,
                "stay_up_late": stay_up,
                "plan_completed": plan,
                "note": "",
                "weather": WEATHERS[int(rng.randint(0, len(WEATHERS)))],
            }
        )

    return records

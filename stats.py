"""Load, save, and display score history using pickle (binary storage)."""

from __future__ import annotations

import os
import pickle
from typing import Any

HISTORY_FILE = "history.dat"


def _empty_user_record() -> dict[str, Any]:
    return {
        "quizzes_taken": 0,
        "questions_answered": 0,
        "correct_total": 0,
        "best_streak_ever": 0,
        "total_streak_bonuses": 0,
        "feedback": {},  # question_index (int) -> dislike count (int)
    }


def load_history() -> dict[str, Any]:
    """
    Load full history blob from disk.

    If unpickling fails, prints the spec message and returns an empty dict.
    """
    if not os.path.isfile(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "rb") as f:
            data = pickle.load(f)
        if not isinstance(data, dict):
            raise ValueError("root must be dict")
        return data
    except Exception:
        print("⚠️ Score history file is corrupted. Starting fresh.")
        return {}


def save_history(data: dict[str, Any]) -> None:
    """Write history atomically via temp file rename pattern."""
    tmp = HISTORY_FILE + ".tmp"
    with open(tmp, "wb") as f:
        pickle.dump(data, f)
    os.replace(tmp, HISTORY_FILE)


def get_user_record(history: dict[str, Any], username: str) -> dict[str, Any]:
    """Return a mutable user stats record, creating defaults if needed."""
    if username not in history:
        history[username] = _empty_user_record()
    rec = history[username]
    for key, default in _empty_user_record().items():
        if key not in rec:
            rec[key] = default.copy() if key == "feedback" else default
    if not isinstance(rec.get("feedback"), dict):
        rec["feedback"] = {}
    return rec


def record_session(
    history: dict[str, Any],
    username: str,
    total_questions: int,
    correct: int,
    best_streak: int,
    streak_bonuses_earned: int,
) -> None:
    """Merge a completed quiz into aggregate stats."""
    rec = get_user_record(history, username)
    rec["quizzes_taken"] += 1
    rec["questions_answered"] += total_questions
    rec["correct_total"] += correct
    if best_streak > rec["best_streak_ever"]:
        rec["best_streak_ever"] = best_streak
    rec["total_streak_bonuses"] += streak_bonuses_earned


def record_feedback(
    history: dict[str, Any],
    username: str,
    question_index: int,
    disliked: bool,
) -> None:
    """Increment dislike count for a question when the user asks to see it less often."""
    if not disliked:
        return
    rec = get_user_record(history, username)
    fb = rec["feedback"]
    fb[question_index] = int(fb.get(question_index, 0)) + 1


def get_dislike_weights(history: dict[str, Any], username: str, num_questions: int) -> list[float]:
    """
    Return per-question weights for selection (lower weight = less likely).

    Indices match the validated question list order.
    """
    rec = get_user_record(history, username)
    fb = rec["feedback"]
    weights: list[float] = []
    for i in range(num_questions):
        dislikes = int(fb.get(i, 0))
        # Each dislike halves the relative weight (bounded so we never hit zero).
        weights.append(1.0 / (1.0 + dislikes))
    return weights


def format_stats_display(history: dict[str, Any], username: str) -> None:
    """Print the stats block or the no-history message."""
    if username not in history:
        print("No quiz history yet. Take a quiz first! 🚀")
        return
    rec = get_user_record(history, username)
    if rec["quizzes_taken"] == 0 and rec["questions_answered"] == 0:
        print("No quiz history yet. Take a quiz first! 🚀")
        return

    answered = rec["questions_answered"]
    correct = rec["correct_total"]
    pct = (100.0 * correct / answered) if answered else 0.0

    print("📊 Your Stats")
    print(f"Total quizzes taken: {rec['quizzes_taken']}")
    print(f"Total questions answered: {answered}")
    print(f"Overall accuracy: {pct:.1f}%")
    print(f"Best streak ever: {rec['best_streak_ever']}")
    print(f"Total streak bonuses earned: {rec['total_streak_bonuses']}")

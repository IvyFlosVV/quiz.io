"""
Question bank loading, validation, quiz flow, scoring, and streak bonuses.

Supports multiple choice, true/false, and short answer; weighted random selection
based on per-question dislike feedback from ``stats``.
"""

from __future__ import annotations

import json
import os
import random
import sys
from typing import Any

QUESTIONS_PATH = "questions.json"


def _validate_question(obj: Any, index: int) -> tuple[bool, str | None]:
    """Return (ok, error_detail)."""
    if not isinstance(obj, dict):
        return False, None
    required = ("question", "type", "answer", "category")
    for k in required:
        if k not in obj or not isinstance(obj[k], str):
            return False, None
    qtype = obj["type"]
    if qtype not in ("multiple_choice", "true_false", "short_answer"):
        return False, None
    if qtype == "multiple_choice":
        opts = obj.get("options")
        if not isinstance(opts, list) or len(opts) < 2:
            return False, None
        if not all(isinstance(o, str) for o in opts):
            return False, None
        if obj["answer"] not in opts:
            return False, None
    elif qtype == "true_false":
        if obj["answer"].lower() not in ("true", "false"):
            return False, None
    return True, None


def load_and_validate_questions() -> list[dict[str, Any]]:
    """
    Load questions.json, validate structure, exit process on fatal errors.

    Returns:
        List of valid question dicts (original order preserved).
    """
    if not os.path.isfile(QUESTIONS_PATH):
        print(
            "❌ Error: Question bank file 'questions.json' not found. "
            "Please add it and try again."
        )
        sys.exit(1)

    raw_text: str
    try:
        with open(QUESTIONS_PATH, encoding="utf-8") as f:
            raw_text = f.read()
    except OSError:
        print(
            "❌ Error: Question bank file 'questions.json' not found. "
            "Please add it and try again."
        )
        sys.exit(1)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        print("❌ Error: Question bank file is not valid JSON. Please check the format.")
        sys.exit(1)

    if not isinstance(data, dict) or "questions" not in data:
        print("❌ Error: No valid questions found in the question bank.")
        sys.exit(1)

    qs = data["questions"]
    if not isinstance(qs, list):
        print("❌ Error: No valid questions found in the question bank.")
        sys.exit(1)

    valid: list[dict[str, Any]] = []
    for i, item in enumerate(qs):
        ok, _ = _validate_question(item, i)
        if ok:
            valid.append(item)

    if not valid:
        print("❌ Error: No valid questions found in the question bank.")
        sys.exit(1)

    return valid


def max_quiz_score(num_questions: int) -> int:
    """Maximum points for a quiz of n questions (all correct, full streak bonuses)."""
    if num_questions <= 0:
        return 0
    base = 10 * num_questions
    bonuses = (num_questions // 3) * 5
    return base + bonuses


def select_question_indices(
    n: int,
    pool_size: int,
    weights: list[float],
) -> list[int]:
    """
    Pick n distinct indices from 0..pool_size-1 using weights (higher = more likely).
    """
    if n > pool_size or n < 1:
        raise ValueError("invalid n")
    available = list(range(pool_size))
    chosen: list[int] = []
    for _ in range(n):
        w = [weights[i] for i in available]
        s = sum(w)
        if s <= 0:
            pick = random.choice(available)
        else:
            r = random.uniform(0, s)
            acc = 0.0
            pick = available[-1]
            for idx, wt in zip(available, w):
                acc += wt
                if r <= acc:
                    pick = idx
                    break
        chosen.append(pick)
        available.remove(pick)
    return chosen


def format_correct_answer(q: dict[str, Any]) -> str:
    """Human-readable correct answer for display after a wrong guess."""
    if q["type"] == "multiple_choice":
        return str(q["answer"])
    if q["type"] == "true_false":
        return q["answer"].lower()
    return str(q["answer"])


def check_answer(q: dict[str, Any], raw_input: str) -> bool:
    """Return True if the user's answer matches (per type rules)."""
    qtype = q["type"]
    if qtype == "multiple_choice":
        opts = q["options"]
        try:
            n = int(raw_input.strip())
        except ValueError:
            return False
        if n < 1 or n > len(opts):
            return False
        return opts[n - 1] == q["answer"]
    if qtype == "true_false":
        a = raw_input.strip().lower()
        return a == q["answer"].lower()
    if qtype == "short_answer":
        return raw_input.strip().lower() == q["answer"].strip().lower()
    return False


def is_valid_mc_input(q: dict[str, Any], raw_input: str) -> bool:
    """Whether multiple_choice input is in range (1..len(options))."""
    opts = q["options"]
    try:
        n = int(raw_input.strip())
    except ValueError:
        return False
    return 1 <= n <= len(opts)


def encouragement_message(percentage: float) -> str:
    """Closing line based on correct/total percentage."""
    if percentage >= 90:
        return "🌟 Amazing! You're a quiz master!"
    if percentage >= 70:
        return "🌟 Great job! Keep it up!"
    if percentage >= 50:
        return "👍 Not bad! A little more practice and you'll ace it!"
    return "💪 Keep going! Every attempt makes you better!"


def prompt_num_questions(max_available: int) -> int:
    """Re-prompt until user enters a valid integer in 1..max_available."""
    while True:
        raw = input(f"How many questions would you like? (1-{max_available}): ").strip()
        try:
            n = int(raw)
        except ValueError:
            print(
                f"Please enter a whole number between 1 and {max_available}."
            )
            continue
        if n < 1 or n > max_available:
            print(
                f"Please enter a whole number between 1 and {max_available} "
                f"(you asked for {n})."
            )
            continue
        return n


def run_quiz_session(
    username: str,
    questions: list[dict[str, Any]],
    weights: list[float],
    record_feedback_fn,
) -> dict[str, Any]:
    """
    Run one quiz; returns session summary dict for stats.update.

    record_feedback_fn(username, question_index, disliked: bool)
    """
    n = prompt_num_questions(len(questions))
    indices = select_question_indices(n, len(questions), weights)

    streak = 0
    best_streak = 0
    score = 0
    correct_count = 0
    streak_bonuses_earned = 0

    for round_i, qidx in enumerate(indices, start=1):
        q = questions[qidx]
        print(f"Question {round_i}/{n} | 🔥 Streak: {streak}")
        print(q["question"])

        if q["type"] == "multiple_choice":
            for i, opt in enumerate(q["options"], start=1):
                print(f"  {i}. {opt}")
            while True:
                ans = input("Your choice (number): ").strip()
                if not is_valid_mc_input(q, ans):
                    print("⚠️ Invalid choice. Please try again.")
                    continue
                break
        elif q["type"] == "true_false":
            print("True / False")
            while True:
                ans = input("Your answer (true or false): ").strip()
                al = ans.lower()
                if al not in ("true", "false"):
                    print("⚠️ Invalid choice. Please try again.")
                    continue
                break
        else:
            ans = input("Your answer: ").strip()

        ok = check_answer(q, ans)
        if ok:
            print("✅ Correct! Nice work!")
            streak += 1
            if streak > best_streak:
                best_streak = streak
            score += 10
            if streak > 0 and streak % 3 == 0:
                score += 5
                streak_bonuses_earned += 1
                print("🔥🔥🔥 Streak Bonus! +5 extra points!")
            correct_count += 1
        else:
            print(f"❌ Not quite. The answer was: {format_correct_answer(q)}")
            streak = 0

        # Feedback for weighted future selection (acceptance: disliked → less frequent)
        fb = input(
            "How was this question? (1) Fine  (2) Show less often in future quizzes: "
        ).strip()
        if fb == "2":
            record_feedback_fn(username, qidx, True)

    total = n
    pct = (100.0 * correct_count / total) if total else 0.0
    denom = max_quiz_score(total)

    print()
    print("🏆 Quiz Complete!")
    print(f"Score: {score}/{denom}")
    print(f"Correct: {correct_count}/{total}")
    print(f"Streak Bonuses Earned: {streak_bonuses_earned}")
    print(f"Best Streak: {best_streak}")
    print(encouragement_message(pct))

    return {
        "total_questions": total,
        "correct": correct_count,
        "best_streak": best_streak,
        "streak_bonuses_earned": streak_bonuses_earned,
    }

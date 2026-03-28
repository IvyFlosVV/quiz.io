#!/usr/bin/env python3
"""
QuizWhiz — main entry: login, menu, quiz, and stats.

Loads and validates ``questions.json`` before the welcome banner, then runs the
interactive menu loop until the user quits.
"""

from __future__ import annotations

import sys
from getpass import getpass

import auth
import quiz
import stats


def main() -> None:
    questions = quiz.load_and_validate_questions()
    history = stats.load_history()

    print("🎓 Welcome to QuizWhiz!")

    while True:
        yn = input("Do you have an account? (yes/no): ").strip().lower()
        if yn in ("yes", "y"):
            user = auth.login_interactive(getpass)
            if user is None:
                sys.exit(1)
            break
        if yn in ("no", "n"):
            user = auth.register_interactive(getpass)
            break
        print("Please answer yes or no.")

    while True:
        print()
        print("📌 Main Menu")
        print("1. Start Quiz")
        print("2. View My Stats")
        print("3. Quit")
        choice = input("Enter your choice (1-3): ").strip()

        if choice == "1":
            weights = stats.get_dislike_weights(history, user, len(questions))

            def record_feedback(u: str, qidx: int, disliked: bool) -> None:
                stats.record_feedback(history, u, qidx, disliked)

            summary = quiz.run_quiz_session(
                user, questions, weights, record_feedback
            )
            stats.record_session(
                history,
                user,
                summary["total_questions"],
                summary["correct"],
                summary["best_streak"],
                summary["streak_bonuses_earned"],
            )
            stats.save_history(history)
        elif choice == "2":
            stats.format_stats_display(history, user)
        elif choice == "3":
            print("👋 Goodbye")
            sys.exit(0)
        else:
            print("That is not a valid menu option. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()

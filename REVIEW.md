# Code review: QuizWhiz vs SPEC.md

Review of `quiz_app.py`, `auth.py`, `quiz.py`, and `stats.py` against `SPEC.md` (acceptance criteria, error handling, security, UX, and edge cases).

---

## Acceptance criteria

1. **[PASS] Fresh start (`users.json` / `history.dat` deleted)** — `auth.register_interactive()` creates a new user via `load_users()` → empty dict when the file is absent (`auth.py` 41–44), writes hashed credentials (`auth.py` 89–92), and `stats.load_history()` returns `{}` when `history.dat` is missing (`stats.py` 29–30). The menu can run a full quiz and `stats.record_session` + `stats.save_history` persist results (`quiz_app.py` 54–62, `stats.py` 63–78, 42–47).

2. **[PASS] Missing `questions.json`** — `quiz.load_and_validate_questions()` checks `os.path.isfile(QUESTIONS_PATH)` and prints the required message, then `sys.exit(1)` (`quiz.py` 51–56).

3. **[PASS] Empty question bank `{"questions": []}`** — After parsing JSON, `valid` stays empty and the code prints `❌ Error: No valid questions found in the question bank.` and exits with code 1 (`quiz.py` 84–92).

4. **[PASS] Login rejects wrong password (3 attempts, exit 1)** — `auth.login_interactive()` increments attempts on unknown user or bad password (`auth.py` 105–116), returns `None` after three failures (`auth.py` 117), and `quiz_app.py` calls `sys.exit(1)` (`quiz_app.py` 28–30). Message matches: `Invalid username or password.` (`auth.py` 109, 115).

5. **[PASS] Streak bonus and reset** — On each correct answer, `streak` increments before the bonus check; when `streak % 3 == 0`, score gains +5 and `streak_bonuses_earned` increments (`quiz.py` 254–264). Wrong answers set `streak = 0` (`quiz.py` 266–267).

6. **[PASS] Feedback affects selection** — Dislikes are stored per question index (`stats.py` 81–92). Weights are `1.0 / (1.0 + dislikes)` (`stats.py` 104–107), so more dislikes → lower weight → less frequent selection. `select_question_indices()` uses weighted sampling without replacement (`quiz.py` 106–134). If every question has many dislikes, weights stay positive and proportional; the `s <= 0` branch (`quiz.py` 121–122) is a safe fallback and does not break selection.

7. **[PASS] Stats persist across runs** — History is loaded at startup (`quiz_app.py` 21) and written after each completed quiz (`quiz_app.py` 62). `format_stats_display()` reads aggregated fields from the user record (`stats.py` 111–130).

8. **[FAIL] Invalid input handled without crashing** — Interactive prompts (menu, yes/no, counts, MC/TF) re-prompt safely (`quiz_app.py` 26–69, `quiz.py` 187–248). **However:** `auth.load_users()` calls `json.load()` with no `try`/`except` (`auth.py` 45–46). Malformed `users.json` raises `JSONDecodeError` on registration or login, so the process exits with a traceback. That violates acceptance criterion 8 (“Typing nonsense at any prompt never crashes the app”) for file-backed state, not just typed input. Unhandled I/O on `save_users()` / `save_history()` can also crash in edge environments.

---

## Additional findings (spec alignment, bugs, quality, security, UX)

9. **[PASS] Streak bonus math at streak 3, 6, 9** — Bonus triggers when `streak` is 3, 6, 9, … after incrementing (`quiz.py` 256–262). Maximum score for `n` questions matches `10*n + (n // 3) * 5` via `max_quiz_score()` (`quiz.py` 97–103, 277–278). Example: `n=3` → 35; `n=6` → 70; `n=9` → 105.

10. **[PASS] Edge: empty string at interactive prompts** — Yes/no: not in `yes`/`y`/`no`/`n` → re-prompt (`quiz_app.py` 26–35). Menu: invalid → re-prompt (`quiz_app.py` 68–69). Question count: `int("")` raises `ValueError` → caught → helpful message (`quiz.py` 191–197). MC: `is_valid_mc_input` false for `""` (`quiz.py` 169–173). TF: must be `true` or `false` (`quiz.py` 243–248). Short answer: `""` is graded as incorrect, no crash (`quiz.py` 251–252, `check_answer` 161–162).

11. **[PASS] Edge: one question in bank, user requests 1** — `prompt_num_questions` allows `1..max_available` (`quiz.py` 198–204). `select_question_indices(1, 1, weights)` runs one iteration (`quiz.py` 114–118).

12. **[WARN] Corrupted `history.dat` scope vs spec** — On unpickle failure, the code prints the required message (`stats.py` 37–38) but returns `{}`, **wiping all users’ history**, not only the current user. `SPEC.md` Error Handling §5 says “reset history **for that user**” (`SPEC.md` 181). **Mismatch:** global reset (`stats.py` 37–39).

13. **[WARN] Question bank read errors** — `OSError` when opening `questions.json` uses the same “file not found” text (`quiz.py` 62–67). Permission or other I/O errors are mislabeled (minor UX/debuggability).

14. **[WARN] Pickle security** — `history.dat` is loaded with `pickle.load()` (`stats.py` 32–33). For a local single-user tool this matches the spec; replacing or merging untrusted files could execute arbitrary code. Acceptable per spec; worth noting for threat model.

15. **[PASS] Password storage** — SHA-256 with random salt, `secrets.compare_digest` for verification (`auth.py` 15–37). `getpass` used for passwords (`quiz_app.py` 12, 27–28, 33; `auth.py` 79–83, 107).

16. **[PASS] Quiz summary and encouragement tiers** — Summary lines match the intended shape (`quiz.py` 280–286). `encouragement_message()` implements 90%+, 70–89%, 50–69%, below 50% (`quiz.py` 176–184).

17. **[PASS] Stats screen copy** — “No quiz history yet…” when unknown user or zero activity (`stats.py` 113–118). Aggregates match the spec layout (`stats.py` 125–130).

18. **[WARN] UX: startup order** — If `history.dat` is corrupted, the warning prints **before** `🎓 Welcome to QuizWhiz!` because `load_history()` runs first (`quiz_app.py` 20–23, `stats.py` 37–38). The step-by-step UX in `SPEC.md` lists the banner before other flows (`SPEC.md` 12–17).

19. **[WARN] UX: feedback prompt** — After each question, users see a numeric feedback prompt (`quiz.py` 269–274). This supports acceptance criterion 6 but is not spelled out in the main “Start Quiz” UX in `SPEC.md`; only “1” and “2” are meaningful, other input silently counts as “fine.” Could confuse users who expect validation on that prompt.

20. **[PASS] Invalid MC choice copy** — Uses `⚠️ Invalid choice. Please try again.` as required (`quiz.py` 237–238, 246–247; `SPEC.md` 179).

21. **[PASS] Code quality** — Clear module split (`quiz_app.py`, `auth.py`, `quiz.py`, `stats.py`). Minor nits: `_validate_question(..., index)` ignores `index` (`quiz.py` 19–21); duplicate “not found” strings in `quiz.py` 52–55 and 63–65.

---

## Summary

| Tag   | Count |
|-------|-------|
| PASS  | 15    |
| FAIL  | 1     |
| WARN  | 5     |

### Top 3 fixes (by impact)

1. **Harden `users.json` I/O** — Catch `json.JSONDecodeError` (and optionally `OSError`) in `load_users()` / callers so a damaged credential file shows a friendly message and re-prompts instead of crashing (closes the main gap vs acceptance criterion 8).

2. **Align `history.dat` corruption handling with the spec** — On unpickle failure, avoid discarding other users’ records: e.g. treat as fresh history only for the current session user, or backup/rename the bad file and start a new store, instead of returning `{}` for everyone (`stats.py` 23–39).

3. **Clarify I/O error messages for `questions.json`** — Distinguish missing file from permission/other `OSError` when printing errors (`quiz.py` 58–67).

---

*Review generated against repository state; line numbers refer to files as of this review.*

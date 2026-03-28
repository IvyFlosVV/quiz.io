# Quiz App — SPEC.md

Overview

A command-line Python quiz app with local login, question bank loading from JSON, score tracking, and a streak bonus system. Everything runs locally with no backend, no HTML/CSS, no APIs.


User Experience (Step by Step)

1. Launch & Login

1. User runs `python quiz_app.py`.
2. App prints a welcome banner:
   ```
   🎓 Welcome to QuizWhiz!
   ```
3. App asks: `Do you have an account? (yes/no)`
   - **yes** → Prompt for username and password. Validate against stored credentials. On failure, print `Invalid username or password.` and re-prompt (max 3 attempts, then exit with code 1).
   - **no** → Prompt for a new username (must be unique, non-empty, alphanumeric). Prompt for a new password (min 6 characters). Confirm password. Save hashed credentials. Print `Account created! Let's get started.`

2. Main Menu

After login, show:
```
📌 Main Menu
1. Start Quiz
2. View My Stats
3. Quit
```
User enters 1, 2, or 3. Invalid input → friendly error message and re-prompt.

### 3. Start Quiz

1. Ask: `How many questions would you like? (1-<max available>):`
2. Randomly select that many questions from the question bank.
3. For each question:
   - Display the question number, total, and current streak: `Question 3/10 | 🔥 Streak: 4`
   - Display the question text.
   - Based on question type:
     - **multiple_choice**: Display numbered options. User enters the number of their choice.
     - **true_false**: Display `True / False`. User enters `true` or `false` (case-insensitive).
     - **short_answer**: User types their answer (case-insensitive, stripped of whitespace for comparison).
   - After answering:
     - **Correct**: Print `✅ Correct! Nice work!` — increment streak counter.
     - **Incorrect**: Print `❌ Not quite. The answer was: <answer>` — reset streak counter to 0.
   - **Streak Bonus** (extension feature): 
     - Every **3 consecutive correct answers**, award a bonus: `🔥🔥🔥 Streak Bonus! +5 extra points!`
     - Base score: +10 points per correct answer.
     - Streak bonus: +5 points awarded at every 3rd consecutive correct answer (i.e., at streak 3, 6, 9…).

4. Quiz Summary

After all questions are answered, display:
```
🏆 Quiz Complete!
Score: 85/100
Correct: 7/10
Streak Bonuses Earned: 2
Best Streak: 6
🌟 Great job! Keep it up!
```
Encouragement messages vary based on percentage:
- 90%+: `🌟 Amazing! You're a quiz master!`
- 70-89%: `🌟 Great job! Keep it up!`
- 50-69%: `👍 Not bad! A little more practice and you'll ace it!`
- Below 50%: `💪 Keep going! Every attempt makes you better!`

Save the session results to the score history file.

5. View My Stats

Display:
```
📊 Your Stats
Total quizzes taken: 5
Total questions answered: 47
Overall accuracy: 72.3%
Best streak ever: 9
Total streak bonuses earned: 6
```
If no history exists, print `No quiz history yet. Take a quiz first! 🚀`

6. Quit
Print `👋 Goodbye` and exit with code 0.


Data Format

Question Bank: `questions.json`

```json
{
  "questions": [
    {
      "question": "What keyword is used to define a function in Python?",
      "type": "multiple_choice",
      "options": ["func", "define", "def", "function"],
      "answer": "def",
      "category": "Python Basics"
    },
    {
      "question": "A list in Python is immutable.",
      "type": "true_false",
      "answer": "false",
      "category": "Data Structures"
    },
    {
      "question": "What built-in function returns the number of items in a list?",
      "type": "short_answer",
      "answer": "len",
      "category": "Python Basics"
    },
    {
      "question": "Which of the following is NOT a valid Python data type?",
      "type": "multiple_choice",
      "options": ["int", "float", "char", "str"],
      "answer": "char",
      "category": "Data Types"
    },
    {
      "question": "Python uses indentation to define code blocks.",
      "type": "true_false",
      "answer": "true",
      "category": "Python Basics"
    },
    {
      "question": "What symbol is used for single-line comments in Python?",
      "type": "short_answer",
      "answer": "#",
      "category": "Syntax"
    },
    {
      "question": "Which keyword is used to handle exceptions in Python?",
      "type": "multiple_choice",
      "options": ["catch", "except", "handle", "error"],
      "answer": "except",
      "category": "Error Handling"
    }
  ]
}
```

**Validation rules for `questions.json`:**
- Must be valid JSON with a top-level `"questions"` key containing a list.
- Each question must have: `question` (string), `type` (one of `"multiple_choice"`, `"true_false"`, `"short_answer"`), `answer` (string), `category` (string).
- `multiple_choice` questions must also have `options` (list of at least 2 strings), and `answer` must be one of the options.
- `true_false` questions must have `answer` as `"true"` or `"false"`.


## File Structure

| File | Purpose |
|---|---|
| `quiz_app.py` | Main entry point — handles login, menu, quiz loop, display |
| `auth.py` | User registration, login, password hashing/verification |
| `quiz.py` | Quiz logic — question selection, answer checking, scoring, streak tracking |
| `stats.py` | Load/save/display score history and feedback |
| `questions.json` | Human-readable question bank (editable by user) |
| `users.json` | Stores usernames + hashed passwords (created at runtime) |
| `history.dat` | Binary (pickled) score history + feedback per user (created at runtime) |

### Why these files?
- `questions.json` is human-readable so users can easily add/edit questions.
- `users.json` stores credentials with hashed passwords — usernames visible but passwords are not discoverable.
- `history.dat` uses Python's `pickle` module to store data in a non-human-readable binary format (as required by the spec). Contains scores **and** feedback, keyed by username.



## Error Handling

The app must handle at least these error cases:

1. **Missing `questions.json`**: Print `❌ Error: Question bank file 'questions.json' not found. Please add it and try again.` Exit with code 1.

2. **Malformed/invalid JSON in `questions.json`**: Print `❌ Error: Question bank file is not valid JSON. Please check the format.` Exit with code 1.

3. **Empty question bank** (file exists but `questions` list is empty or all questions are invalid): Print `❌ Error: No valid questions found in the question bank.` Exit with code 1.

4. **Invalid user input during quiz** (e.g., entering "5" when there are 4 options): Print `⚠️ Invalid choice. Please try again.` and re-prompt for the same question.

5. **Corrupted `history.dat`**: If unpickling fails, print `⚠️ Score history file is corrupted. Starting fresh.` and reset history for that user.

6. **Invalid number of questions requested** (0, negative, non-integer, or more than available): Print a helpful message with the valid range and re-prompt.


## Required Features Checklist

- [x] Local login system with hashed passwords (use `hashlib.sha256` with a salt)
- [x] Questions loaded from a human-readable `.json` file
- [x] Three question types: multiple choice, true/false, short answer
- [x] Random question selection
- [x] Score tracking saved in non-human-readable format (`pickle`)
- [x] Stats viewing

Extension Feature: Streak Bonus System

- Track consecutive correct answers during a quiz session.
- Every 3 consecutive correct answers → +5 bonus points on top of the base +10.
- Display current streak alongside each question.
- Show streak stats in quiz summary and overall stats.
- A wrong answer resets the streak to 0.

---
Acceptance Criteria

1. **Fresh start works**: Deleting `users.json` and `history.dat`, then running the app, allows account creation and a full quiz without errors.
2. **Missing question bank**: Running the app with no `questions.json` prints a friendly error and exits with code 1.
3. **Empty question bank**: A `questions.json` with `{"questions": []}` prints a friendly error and exits with code 1.
4. **Login rejects wrong password**: Entering a wrong password 3 times prints an error and exits.
5. **Streak bonus triggers correctly**: Getting 3 correct in a row awards +5 bonus; getting one wrong resets the streak.
6. **Feedback affects selection**: After marking several questions as disliked, those questions appear less frequently in subsequent quizzes (verifiable by running multiple quizzes).
7. **Stats persist**: Completing a quiz, quitting, re-launching, and viewing stats shows the previous session's data.
8. **Invalid input is handled gracefully**: Typing nonsense at any prompt never crashes the app — it always re-prompts or shows a helpful message.

---

## Dependencies

- **Python 3.10+** (standard library only)
- Modules used: `json`, `hashlib`, `os`, `random`, `pickle`, `getpass`, `sys`
- **No external packages required.**

---

## Notes

- Keep the code clean and well-documented with docstrings.
- Use `getpass.getpass()` for password input so it's not echoed to the terminal.
- Salt passwords with a random salt stored alongside the hash in `users.json`.
- Keep all print statements friendly and use emoji consistently.
- Do not over-engineer: no classes unless they genuinely help. Simple functions and dictionaries are fine.

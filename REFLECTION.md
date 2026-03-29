# Reflection

## 1. How far did the agent get?

The agent fully implemented my spec. Cursor's agent mode handled all the core features — login system with hashed passwords, three question types, random selection, score persistence with pickle, feedback collection, and the streak bonus system. I'd estimate around 90% of my acceptance criteria passed on the first try. The main logic, file structure, and UX flow all matched what I described in the spec without needing corrections.

## 2. Where did I intervene?

I barely had to intervene during the build phase. This isn't my first time using this workflow — I've been using a plan-then-delegate approach with Cursor's agent mode in previous projects (breaking tasks into a to-do list, handing it off, then debugging), so writing a spec that an agent can follow cleanly is something I've practiced before. The familiarity helped me write a spec that left fewer ambiguities. The one area where the agent had to make its own judgment calls was the feedback-based question weighting system, where I hadn't specified exact weights. It made reasonable choices there. A more precise spec *could* have pinned that down, but honestly the agent's interpretation was fine.

## 3. How useful was the AI review?

The review agent found 3 real issues, mostly edge cases — the kind of things you don't think about when writing the spec but matter in practice. These were genuine catches and worth fixing. I didn't notice it flagging things that were non-issues, so the signal-to-noise ratio was good. That said, the review was better at catching mechanical bugs than evaluating the overall user experience. If I wanted UX feedback specifically, I'd probably need to prompt for that more explicitly or just test it myself.

## 4. What would I change about the spec?

In hindsight, my spec was already fairly detailed — the step-by-step user flow, the exact error messages, and the acceptance criteria all helped the agent stay on track. If I were to improve it, I'd be more specific about edge case behavior (e.g., what happens when all questions are disliked, or when the user requests exactly the number of available questions). I'd also explicitly define the weighted sampling numbers instead of leaving that to interpretation. The lesson is: anywhere you write "something like" or leave a decision implicit, the agent will fill in the blank — sometimes well, sometimes not.

## 5. When would I use this workflow?

Plan-delegate-review works best when the project has a clear, well-defined scope and produces testable output — exactly like this quiz app. You can describe what "done" looks like, hand it off, and verify the result. It's faster than conversational back-and-forth because you skip the iterative copy-paste cycle. I'd use it for any self-contained feature or tool where I can write a complete spec upfront. It's worse for exploratory work — when I don't yet know what I want, or when I'm learning a new concept and need the AI to explain things along the way. In those cases, the conversational approach is more natural because the goal evolves as you go.

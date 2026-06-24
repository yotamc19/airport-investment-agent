---
description: Run the evaluation suite against the agent and report results
---

# Run Agent Evaluation

Run the full evaluation suite from `evals/questions.json` against the agent.

## Steps

1. Read `evals/questions.json` to load all test questions
2. For each question:
   a. Send the question to the agent endpoint (POST to the agent's chat API)
   b. Capture the agent's full response
   c. Grade the response against the expected answer:
      - Check each `must_include` assertion — does the response cover this point?
      - Check each `must_not_include` assertion — does the response avoid this?
      - Score: percentage of `must_include` items satisfied, with any `must_not_include` violation as an automatic flag
3. Print a results table:
   ```
   ID   | Question (truncated)        | Score | Flags
   q1   | Which airports in New En... | 4/5   | PASS
   q2   | Compare LA and Santa An... | 3/4   | FAIL: mentioned wrong airport
   ```
4. Print overall pass rate and list any regressions (questions that previously passed but now fail)
5. If any question scores below 50%, suggest adding it to a "needs attention" list

## Important
- If the agent server is not running, start it first
- Each question should be sent as a fresh conversation (no follow-up context)
- Save results to `evals/results/` with a timestamp so we can track improvement over time
- If a question fails badly, suggest whether it's an agent logic issue or a test expectation issue

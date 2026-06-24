---
description: Add a new test question to the evaluation database
argument-hint: The question the agent struggled with
---

# Add Evaluation Question

Add a new question to `evals/questions.json` based on an edge case or failure discovered during development.

## Input
$ARGUMENTS

If no arguments provided, ask the user:
1. What question did the agent struggle with?
2. What should the correct answer include?
3. What should it avoid?

## Steps

1. Read the current `evals/questions.json`
2. Determine the next question ID (e.g., if last is `q7`, use `q8`)
3. Construct a new question entry with:
   - `id`: next sequential ID
   - `question`: the exact question text
   - `source`: "discovered" (to distinguish from the original assignment questions)
   - `expected.summary`: a plain-English description of what a good answer looks like
   - `expected.must_include`: 3-5 specific assertions the response must satisfy
   - `expected.must_not_include`: 1-3 red flags that indicate a bad answer
4. Add the entry to the questions array in `evals/questions.json`
5. Confirm the addition and suggest running `/eval` to test

## Guidelines
- Be specific in assertions — "mentions BOS" is better than "mentions a major airport"
- `must_include` should test both factual accuracy AND reasoning quality
- `must_not_include` should catch common failure modes (wrong airport, hallucinated data, missing caveats)
- Always note whether this was a data issue, reasoning issue, or tool-use issue in the summary

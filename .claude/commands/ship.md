---
description: Stage, commit, and push changes with interview-quality commit messages
---

# Commit and Push

This repo is a take-home assignment. The interviewer WILL read the git history. Every commit message matters — it tells the story of how the project was built.

## Rules

1. **Small, logical commits.** Never bundle unrelated changes. If you worked on scoring logic AND the chat UI, that's two commits. Each commit should represent one coherent thought.

2. **Commit messages tell a story.** The interviewer reads `git log --oneline` and should see a clear progression:
   ```
   good:
   scaffold project structure with Next.js frontend and FastAPI backend
   add deterministic scoring model for airport congestion and capacity
   implement tool-calling agent with airport search and comparison tools
   add eval framework with 4 baseline test questions

   bad:
   update files
   WIP
   fix stuff
   add features
   ```

3. **Message format:** Start with a lowercase verb. One line, under 72 characters. If more context is needed, add a blank line then a short body paragraph — but most commits shouldn't need one.

4. **Logical ordering matters.** If you have multiple changes to commit, think about what order tells the best story. Foundation first, then features, then refinements.

## Steps

1. Run `git status` and `git diff` to see all changes
2. Group changes into logical commits — ask yourself "would the interviewer understand why these files changed together?"
3. For each logical group:
   a. Stage only the relevant files (never `git add -A` blindly)
   b. Write a clear commit message that explains the WHY, not just the WHAT
   c. Commit
4. Push to remote

## Important
- If unsure how to split changes, ask the user
- Never amend published commits
- Never force push

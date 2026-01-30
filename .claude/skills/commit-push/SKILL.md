---
name: commit-push
description: Stage all changes, create a meaningful commit message, and push to the remote branch.
---

Commit and push all current changes.

Steps:

1. Run `git status` (without `-uall`) and `git diff` to understand all staged and unstaged changes.
2. Run `git log --oneline -5` to see recent commit message style.
3. Stage all relevant changes with `git add` (prefer naming specific files over `git add .`; never stage files containing secrets like `.env` or credentials).
4. Write a concise commit message that summarizes the "why" of the changes. Follow the style of recent commits in this repo. End the message with:
   ```
   Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
   ```
5. Create the commit using a HEREDOC for the message.
6. Push to the current remote-tracking branch with `git push`. If no upstream is set, push with `git push -u origin HEAD`.
7. Confirm success by showing the final `git status` and the pushed commit hash.

If $ARGUMENTS is provided, incorporate it into the commit message.
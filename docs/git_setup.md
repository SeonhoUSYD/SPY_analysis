# GitHub connection

The local repository uses branch `main` and remote `origin`:

```text
https://github.com/SeonhoUSYD/SPY_analysis.git
```

The remote and upstream branch are configured. Uploads require this Mac to authenticate with GitHub. The connected Codex GitHub account and the local Git client use separate authentication sessions.

## Authenticate and upload from VS Code

1. Open this project folder in VS Code.
2. Open Source Control and choose Push or Sync Changes.
3. Complete the GitHub sign-in prompt in the browser and return to VS Code.
4. Verify that Source Control shows no outgoing commits.

Use GitHub's normal sign-in flow. Do not place access tokens or passwords in source files, terminal command history, or chat.

## Check the connection

```bash
git remote -v
git status --short --branch
git log -1 --oneline
git push -u origin main
```

Once authentication succeeds, future updates can be committed and pushed from VS Code. Downloaded datasets and the local Python environment are excluded from Git; the source manifest and reproduction scripts are tracked.

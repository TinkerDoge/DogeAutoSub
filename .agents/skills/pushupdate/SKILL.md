---
name: pushupdate
description: "Use when preparing and publishing DogeAutoSub updates: gather changed update files, bump version, generate releases/version.json + releases/files via serve_updates.py, validate artifacts, and optionally push to git or start update server. Keywords: release, updater, version.json, delta patch, publish update, push update files."
---

Prepare and publish a DogeAutoSub update package in a repeatable, low-risk workflow.

## Outcome

Produce a valid update payload for clients:
- releases/version.json contains the target version, notes, and file hashes
- releases/files contains patchable files copied from current workspace state
- optional full zip is generated: releases/DogeAutoSub_v<version>.zip
- optional local update server is started for LAN testing

## Use This Skill When

- User asks to "push update", "publish update", "prepare release", or "update version.json"
- Code has changed and updater artifacts must be regenerated
- Need to verify delta patch contents before distributing to team

## Inputs

- target_version: semantic version string, for example 2.2.3
- release_notes: one-line or short paragraph notes
- mode: dry-run | generate | generate-and-serve
- push_git: true | false

Default behavior:
- If target_version is missing, auto bump patch from releases/version.json (x.y.z -> x.y.(z+1)) and report it.
- If push_git is missing, default to false (manual commit/push).
- If release_notes are missing, derive from recent user request and changed files, then confirm.

## Workflow

1. Preflight checks
- Ensure workspace root is DogeAutoSub and virtual env exists.
- Run git status and capture changed files.
- If there are unrelated risky changes, warn and continue only with user confirmation.

2. Determine release metadata
- Read current releases/version.json.
- If target_version not provided, compute next patch version from current manifest version.
- Validate target_version is newer than current version.
- Build concise release_notes focused on user-visible behavior changes.

3. Generate updater artifacts
- Run: python serve_updates.py --generate <target_version> --notes "<release_notes>"
- This regenerates releases/version.json, releases/files, and full zip.

4. Validate artifacts (must pass)
- releases/version.json exists and version equals target_version.
- filename matches DogeAutoSub_v<target_version>.zip.
- files map is non-empty.
- For each changed patchable source file, verify corresponding path exists under releases/files.
- Spot-check at least one critical changed file hash entry in version.json.

5. Optional local serve test
- If mode is generate-and-serve, run: python serve_updates.py --serve
- Report URL and how to stop server.

6. Optional git push
- If push_git is true:
- Stage release artifacts and related source changes.
- Commit with message: "release: v<target_version>"
- Push current branch to remote.

7. Final report
- Summarize version, notes, generated files count, and any skipped checks.
- Include explicit pass/fail for validation checklist.

## Decision Rules

- If generate command fails: stop, show root cause, propose fix, do not push.
- If target_version is not newer: stop and ask for corrected version.
- If validation fails: regenerate once; if still failing, stop and request user decision.
- If git push fails: keep local commit and show exact next command.

## Quality Checklist

- version in releases/version.json is correct
- zip filename matches version
- releases/files reflects current source changes
- release notes are clear and user-facing
- no silent failures; all blocked steps reported

## Example Prompts

- "Use pushupdate: generate 2.2.3 with notes 'MLAAS long transcript chunking fix', no git push."
- "Use pushupdate in dry-run mode and tell me what will change."
- "Use pushupdate: generate-and-serve 2.2.3, then give me the LAN update URL."
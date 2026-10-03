#!/bin/bash
# ASSERT THE TRACKED SET IS EXACTLY WHAT WE MEANT TO PUBLISH.
#
# WHY AN ALLOWLIST AND NOT A PATTERN LIST. This repo is public, and its content is
# a SUBSET of a working tree that also holds material which must never leave the
# origin machine. A deny-by-default `.gitignore` is safe, but it is not
# self-checking: `git add -f` walks past it, and so does a careless un-ignore rule
# added later.
#
# The lab's own gate is a BLACKLIST of forbidden patterns, and it fails on the
# case nobody thought of. This version asserts the positive instead: every tracked
# path must sit under one of the paths we MEANT to publish. Anything else is
# refused by construction — there is no pattern to miss.
#
# ITS SCOPE, STATED SO IT IS NOT MISTAKEN FOR MORE: this guards the BOUNDARY —
# nothing from outside the published paths can be tracked. It does NOT police the
# CONTENTS of those paths: a file placed inside `paper2/` or `ops/` or `runs/` is
# published by intent, and this gate will admit it. It is deliberately NOT a copy
# of the lab's version, which names the private source files it must exclude and
# would therefore leak the very thing it guards.
#
# `.git/hooks/pre-commit` runs it. Do not bypass with --no-verify.
#
# Usage:  bash ops/check_tracked_set.sh
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

# THE ALLOWLIST — the only paths that may be tracked. Keep in step with
# .gitignore's un-ignore rules; if they drift, this is the one that should win.
# `design/` (the product's design record) is deliberately NOT published.
# `dpdr/` carries the frozen model package (the revision the agent build imports) and
# `dlb/` the engine binding (paper 1's deposit predates the model's opt-in variants,
# and the CEN's real-engine path needs dlb).
# `agent/` and `design/` carry the worker's code (paper 2's Appendix B cites; paper 3
# adds the worker's full task suite and batteries). `runs/` carries the run data
# (campaign.json, state/, evaluation.json, per-cell runs/*.json and rows/*.jsonl,
# logs/*.rc). `held-out-task-suite.json` is the sealed held-out definition.
# `SNAPSHOT` is the revision pin. `paper-3.md` and `paper-3.pdf` are the unified paper.
ALLOWED_DIRS=(paper2 ops agent runs dpdr dlb)
ALLOWED_FILES=(README.md LICENSE LICENSE-paper .gitignore SNAPSHOT paper-3.md paper-3.pdf .zenodo.json held-out-task-suite.json)

fail=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  ok=0
  for f_ok in "${ALLOWED_FILES[@]}"; do [ "$f" = "$f_ok" ] && ok=1 && break; done
  if [ "$ok" -eq 0 ]; then
    for d in "${ALLOWED_DIRS[@]}"; do
      case "$f" in "$d"/*) ok=1; break;; esac
    done
  fi
  if [ "$ok" -eq 0 ]; then
    echo "REFUSING: '$f' is outside the publish allowlist." >&2
    echo "  allowed: ${ALLOWED_DIRS[*]} / ${ALLOWED_FILES[*]}" >&2
    fail=1
  fi
done < <(git ls-files)

[ "$fail" -eq 0 ] || { echo >&2; echo "Fix: unstage it, or add the path here deliberately." >&2; exit 1; }

# Independent check by CONTENT SHAPE: no session/transcript data anywhere, and no
# .jsonl outside runs/ (the per-turn rows under runs/ are the paper's evidence and
# are tracked by intent).
if git ls-files | grep -qE '(^|/)session-|transcript'; then
  echo "REFUSING: session/transcript data is tracked." >&2
  exit 1
fi
while IFS= read -r f; do
  case "$f" in runs/*) continue;; esac
  echo "REFUSING: .jsonl/.ndjson outside runs/ is tracked: '$f'" >&2
  exit 1
done < <(git ls-files | grep -E '\.(jsonl|ndjson)$')

echo "tracked set clean: $(git ls-files | wc -l) files, all inside the allowlist."

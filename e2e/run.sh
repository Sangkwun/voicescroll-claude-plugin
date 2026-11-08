#!/bin/bash
# run.sh <name> <model> <prompt file> [file to put in the run folder]
#
# One headless Claude Code run with only this plugin: user settings, other plugins, MCP servers, and CLAUDE.md are
# left out (--setting-sources project in an empty folder). The prompt goes on stdin. The run folder is outside
# this repository, because Claude Code reads CLAUDE.md from the folders above the one it runs in.
#
#   E2E_RUNS  where runs go (default $TMPDIR/voicescroll-e2e) — <name>/{prompt.txt,out.jsonl,err.txt,cwd/}
#   CLAUDE    the command (default claude)
set -u
E=$(cd "$(dirname "$0")" && pwd)
name=$1 model=$2 prompt=$3
case $name in ''|.*|*/*) echo "run.sh: the name must be a plain folder name: '$name'" >&2; exit 2;; esac
d=${E2E_RUNS:-${TMPDIR:-/tmp}/voicescroll-e2e}/$name
rm -rf "$d"; mkdir -p "$d/cwd"; cp "$prompt" "$d/prompt.txt"
if [ -n "${4:-}" ]; then cp "$4" "$d/cwd/"; fi
cd "$d/cwd" && ${CLAUDE:-claude} -p --setting-sources project --strict-mcp-config --model "$model" \
  --plugin-dir "$E/../voicescroll" --allowedTools "Bash,Skill,Read" --output-format stream-json --verbose \
  < "$d/prompt.txt" > "$d/out.jsonl" 2> "$d/err.txt"
echo "$name exit=$? $d"

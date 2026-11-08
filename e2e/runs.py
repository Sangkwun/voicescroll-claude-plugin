"""Read the Bash commands of an e2e run: the heredocs a command holds, and whether code Claude wrote out is the
skill's code from SKILL.md, character for character.

The skills tell Claude to run their code in one command:

    f=$(mktemp) && cat > "$f" <<'VOICESCROLL_CODE_END' && python3 "$f" - <<'VOICESCROLL_SCRIPT_END'; rm -f "$f"
    (code)
    VOICESCROLL_CODE_END
    (script)
    VOICESCROLL_SCRIPT_END
"""
import difflib
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))
from skill_code import code  # noqa: E402

SKILLS = ("script-link", "script-format", "reading-time")
MARKER = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?")


def heredocs(command):
    """[(marker, body)] for the heredocs of a command whose first line holds the << operators, in order."""
    lines = command.split("\n")
    out, i = [], 1
    for marker in MARKER.findall(lines[0]):
        body = []
        while i < len(lines) and lines[i].strip() != marker:
            body.append(lines[i])
            i += 1
        out.append((marker, "\n".join(body)))
        i += 1
    return out


def code_copies(command):
    """[(skill, None if same, else a short description of the first differences)] for each heredoc that holds a
    skill's code. A body counts as code if it is closer to a skill's code than half."""
    found = []
    for _, body in heredocs(command):
        if "import sys" not in body:
            continue
        ratios = {s: difflib.SequenceMatcher(None, code(s), body + "\n", autojunk=False).ratio() for s in SKILLS}
        skill = max(ratios, key=ratios.get)
        if ratios[skill] < 0.5:
            continue
        want, got = code(skill).splitlines(), body.splitlines()
        if want == got:
            found.append((skill, None))
            continue
        diff = [d for d in difflib.unified_diff(want, got, lineterm="", n=0) if d[:1] in "+-" and d[:3] not in ("+++", "---")]
        found.append((skill, f"{len(diff)} lines differ: " + " | ".join(d[:70] for d in diff[:4])))
    return found


def bash_commands(run_dir):
    """[(tool_use id, command)] of the run's Bash calls, in order."""
    out = []
    for line in open(os.path.join(run_dir, "out.jsonl"), encoding="utf-8"):
        e = json.loads(line)
        if e.get("type") == "assistant":
            for c in e["message"]["content"]:
                if c["type"] == "tool_use" and c["name"] == "Bash":
                    out.append((c["id"], c["input"]["command"]))
    return out


def report_code(run_dir):
    """Print one line per code copy in the run."""
    for _, command in bash_commands(run_dir):
        for skill, diff in code_copies(command):
            print(f"   code {skill}: " + ("same as SKILL.md" if diff is None else "DIFFERENT · " + diff))

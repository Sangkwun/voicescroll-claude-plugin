"""Read the Bash commands of an e2e run: the heredocs a command holds, and whether code Claude wrote out is the
skill's code from SKILL.md, character for character.

The skills tell Claude to run their code in one command:

    f=$(mktemp) && cat >| "$f" <<'VOICESCROLL_CODE_END' && python3 "$f" - <<'VOICESCROLL_SCRIPT_END'; s=$?; rm -f "$f"; (exit $s)
    (code)
    VOICESCROLL_CODE_END
    (script)
    VOICESCROLL_SCRIPT_END
"""
import difflib
import functools
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))
import skill_code  # noqa: E402

SKILLS = tuple(skill_code.skills())
# A heredoc operator, << or <<-, and its marker; not a here-string (<<<).
MARKER = re.compile(r"(?<!<)<<(-?)(?!<)\s*['\"]?(\w+)['\"]?")


@functools.lru_cache(maxsize=None)
def code(skill):
    return skill_code.code(skill)


def heredocs(command):
    """[(marker, body)] for the heredocs of a command, in order. A heredoc's body starts on the line after the line that
    opens it and ends at a line that is exactly its marker (for <<-, after leading tabs)."""
    out, pending, body = [], [], None
    for line in command.split("\n"):
        if pending:
            dash, marker = pending[0]
            if (line.lstrip("\t") if dash else line) == marker:
                out.append((marker, "\n".join(body)))
                pending.pop(0)
                body = []
            else:
                body.append(line)
            continue
        pending = MARKER.findall(line)
        body = []
    return out


def which_code(body):
    """The skill whose code a heredoc body is, or None. Equal code is found first; otherwise the closest code, if it is
    closer than half."""
    for skill in SKILLS:
        if body + "\n" == code(skill):
            return skill
    if "import " not in body:
        return None
    ratios = {s: difflib.SequenceMatcher(None, code(s), body + "\n", autojunk=False).ratio() for s in SKILLS}
    skill = max(ratios, key=ratios.get)
    return skill if ratios[skill] >= 0.5 else None


def code_copies(command):
    """[(skill, None if the same as SKILL.md, else a short description of the first differences)] for each heredoc of
    the command that holds a skill's code."""
    found = []
    for _, body in heredocs(command):
        skill = which_code(body)
        if skill is None:
            continue
        want, got = code(skill).splitlines(), body.splitlines()
        if want == got:
            found.append((skill, None))
            continue
        diff = [d for d in difflib.unified_diff(want, got, lineterm="", n=0) if d[:1] in "+-" and d[:3] not in ("+++", "---")]
        found.append((skill, f"{len(diff)} lines differ: " + " | ".join(d[:70] for d in diff[:4])))
    return found


def text_bodies(command):
    """The bodies of the command's heredocs that are not a skill's code: the script Claude passed."""
    return [body for _, body in heredocs(command) if which_code(body) is None]


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

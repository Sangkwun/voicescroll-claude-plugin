"""The code a skill's SKILL.md holds, written to a file so tests and e2e tools can import and run it.

Each skill keeps its code in one ```python block under "## The code", the last section of its SKILL.md.
Claude writes that block to a temporary file and runs it; this does the same for the tests. The plugin
ships no code files, because the Claude plugin directory accepts only Markdown, text, JSON, YAML, and
images from organizations that are not Verified (refused 2026-11-09).

    from skill_code import code, path
    path("script-link", "script_link")   # a .py file holding the block, importable as script_link
"""

import atexit
import os
import re
import shutil
import tempfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SKILLS = os.path.join(ROOT, "voicescroll", "skills")
SECTION = "\n## The code\n"
BLOCK = re.compile(r"^```python\n(.*?)^```$", re.S | re.M)

_dir = tempfile.mkdtemp(prefix="voicescroll-skill-code-")
atexit.register(shutil.rmtree, _dir, True)


def skills():
    """The skill folders, not stray files such as .DS_Store."""
    return sorted(d for d in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, d)))


def skill_md(skill):
    with open(os.path.join(SKILLS, skill, "SKILL.md"), encoding="utf-8") as f:
        return f.read()


def code(skill):
    """The one python block of a skill, from its last section "## The code"."""
    text = skill_md(skill)
    if text.count(SECTION) != 1 or "\n## " in text.split(SECTION, 1)[1]:
        raise ValueError(f"{skill}/SKILL.md must end with one '## The code' section")
    blocks = BLOCK.findall(text)
    if len(blocks) != 1 or blocks[0] not in text.split(SECTION, 1)[1]:
        raise ValueError(f"{skill}/SKILL.md must have one python block, in '## The code'")
    return blocks[0]


def path(skill, module):
    """A file holding the skill's code, named module.py, in a folder that is removed when Python exits."""
    p = os.path.join(_dir, module + ".py")
    if not os.path.exists(p):
        with open(p, "w", encoding="utf-8") as f:
            f.write(code(skill))
    return p

"""The command each SKILL.md gives Claude works as written, and each skill's code stops when a key value is miscopied.

Claude copies the command from the skill's steps, puts the code from "The code" in the first heredoc and the script in
the second, and runs it in the user's shell. This does the same in bash and zsh, also with noclobber set, and checks the
output, the exit status, and that the temporary file is gone.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from skill_code import code, path, skill_md, skills  # noqa: E402

CODE_LINE = '(the code from "The code", every line exactly as written)'
SCRIPT_LINE = "(the script text)"
COMMAND = re.compile(r"^   ```\n((?:   .*\n)+?)   ```$", re.M)

SHELLS = [s for s in ("bash", "zsh") if shutil.which(s)]


def commands(skill):
    """The commands in a skill's steps, without the list indent."""
    found = []
    for block in COMMAND.findall(skill_md(skill)):
        text = "".join(line[3:] for line in block.splitlines(keepends=True))
        if text.startswith("f=$(mktemp)"):
            found.append(text)
    return found


def fill(command, skill, script):
    return command.replace(CODE_LINE + "\n", code(skill)).replace(SCRIPT_LINE + "\n", script)


def run(shell, command, tmp, noclobber=False):
    pre = "set -o noclobber\n" if noclobber else ""
    env = dict(os.environ, TMPDIR=tmp)
    return subprocess.run([shell, "-c", pre + command], capture_output=True, env=env)


def direct(skill, module, args, script):
    return subprocess.run([sys.executable, "-I", path(skill, module), *args], input=script.encode(), capture_output=True)


class CommandTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def check(self, skill, module, command_index, args, script, status=0):
        command = fill(commands(skill)[command_index], skill, script)
        want = direct(skill, module, args, script)
        self.assertEqual(want.returncode, status, want.stderr)
        for shell in SHELLS:
            for noclobber in (False, True):
                with self.subTest(shell=shell, noclobber=noclobber):
                    out = run(shell, command, self.tmp, noclobber)
                    self.assertEqual(out.returncode, status, out.stderr)
                    self.assertEqual(out.stdout, want.stdout)
                    self.assertEqual(out.stderr, want.stderr)
                    self.assertEqual(os.listdir(self.tmp), [], "the temporary file is left behind")

    def test_each_skill_has_its_commands(self):
        self.assertEqual({s: len(commands(s)) for s in skills()},
                         {"reading-time": 2, "script-format": 1, "script-link": 1})

    def test_link(self):
        self.check("script-link", "script_link", 0, ["-"], "[박수]\n안녕하세요 \"따옴표\" $HOME `date` \\n\n")

    def test_link_error_keeps_the_exit_status(self):
        self.check("script-link", "script_link", 0, ["-"], " \n", status=1)

    def test_format(self):
        self.check("script-format", "check_script", 0, ["-"], "[Intro]\nHello [smile]\nBye [now\n")

    def test_reading_time(self):
        self.check("reading-time", "reading_time", 0, ["--lang", "ko", "-"], "[박수]\n안녕하세요, 여러분.\n")

    def test_reading_time_for_seconds(self):
        command = commands("reading-time")[1].replace(CODE_LINE + "\n", code("reading-time"))
        want = subprocess.run([sys.executable, "-I", path("reading-time", "reading_time"), "--lang", "en", "--seconds", "60"],
                              capture_output=True)
        for shell in SHELLS:
            with self.subTest(shell=shell):
                out = run(shell, command, self.tmp, noclobber=True)
                self.assertEqual(out.returncode, 0, out.stderr)
                self.assertEqual(out.stdout, want.stdout)
                self.assertEqual(os.listdir(self.tmp), [])


# A miscopy of a key value, per skill: (skill, old, new, args).
MISCOPIES = [
    ("script-link", 'PREFIX = "https://www.voice-scroll.com/s#v1."', 'PREFIX = "https://voice-scroll.com/s#v1."', ["-"]),
    ("script-link", "urlsafe_b64encode", "b64encode", ["-"]),
    ("script-link", '.decode("ascii").rstrip("=")', '.decode("ascii")', ["-"]),
    ("script-link", "zlib.compress(text", "zlib.compress(b'x' + text", ["-"]),
    ("reading-time", '"ko": ("characters", 276, 314, 368)', '"ko": ("characters", 368, 314, 276)', ["--lang", "ko", "-"]),
    ("reading-time", '"de": ("words", 155, "coupe")', '"de": ("words", 153, "coupe")', ["--lang", "de", "-"]),
    ("reading-time", '"vi": ("words", 256, "coupe")', '"vi": ("words", 265, "coupe")', ["--lang", "vi", "-"]),
    ("script-format", '"【": "[", "】": "]"', '"【": "[", "】": "["', ["-"]),
    ("script-format", '"（": "(", "）": ")"', '"（": "(", "）": "("', ["-"]),
    ("script-format", 'MARKS = {"[]": ("[", "]")', 'MARKS = {"[]": ("[", ")")', ["-"]),
]


class SelfTestTest(unittest.TestCase):
    def test_each_miscopy_stops_the_code(self):
        for skill, old, new, args in MISCOPIES:
            with self.subTest(skill=skill, new=new):
                source = code(skill)
                self.assertEqual(source.count(old), 1, old)
                with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
                    f.write(source.replace(old, new))
                self.addCleanup(os.unlink, f.name)
                out = subprocess.run([sys.executable, "-I", f.name, *args], input="[smile] Hello\n".encode(),
                                     capture_output=True)
                self.assertEqual(out.returncode, 1)
                self.assertEqual(out.stdout, b"")
                self.assertIn(b"the code was not copied exactly", out.stderr)


if __name__ == "__main__":
    unittest.main()

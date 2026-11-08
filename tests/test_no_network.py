"""The plugin makes no outside requests.

Three checks: the skills' code (the python block in each SKILL.md) imports only
standard-library modules that cannot reach a network; plugin files name no host but
voice-scroll.com; and on macOS each skill's code runs the same with the network
denied by sandbox-exec.
"""

import ast
import io
import os
import re
import shutil
import subprocess
import sys
import tokenize
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, "..", "voicescroll")

sys.path.insert(0, HERE)
from skill_code import BLOCK, code, path, skills  # noqa: E402

# Add a module here only if it cannot open a connection.
ALLOWED_IMPORTS = {"argparse", "base64", "re", "statistics", "sys", "unicodedata", "zlib"}

# Names that could load a module or run code the import check cannot see.
DYNAMIC_NAMES = {"__import__", "__builtins__", "eval", "exec", "compile", "getattr", "globals", "vars", "importlib"}

ALLOWED_HOSTS = {"www.voice-scroll.com", "voice-scroll.com"}

# Any scheme (or none) followed by //host, and bare host names with a dot and a letter-only last label.
URL_HOST = re.compile(r"(?i)(?:[a-z][a-z0-9+.-]*:)?//([^/\s)\"'>#:]+)")
BARE_HOST = re.compile(r"(?i)\b((?:[a-z0-9-]+\.)+[a-z]{2,})\b")
# File names and Python attribute chains the bare-host pattern also matches.
NOT_HOSTS = re.compile(r"(?i)\.(md|py|json|txt|png|zip|plugin|swift|ts)$|^(base64|zlib|sys|os|f|e|raw|script|self|node|out|claude-plugin)\.")

# A skill, the module name its code is written to, the code's arguments, and its stdin.
RUNS = [
    ("script-link", "script_link", ["-"], "[박수]\n안녕하세요\n"),
    ("reading-time", "reading_time", ["--lang", "ko", "-"], "[박수]\n안녕하세요\n"),
    ("script-format", "check_script", ["-"], "[박수]\n안녕하세요 [이름\n"),
]


# Script tokens that can hold a host name: string and bytes literals, f-string text, comments.
TEXT_TOKENS = {tokenize.STRING, tokenize.COMMENT} | {getattr(tokenize, "FSTRING_MIDDLE", tokenize.STRING)}


def code_text(source):
    """Where code could name a host: its literals and comments.

    The code itself is checked by the import test; its attribute chains (``text.split``)
    look like host names to the pattern, so code tokens are not scanned.
    """
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    return "\n".join(t.string for t in tokens if t.type in TEXT_TOKENS)


def readable_text(file):
    """Where a file could name a host: all of its text, but only the literals and comments of a python block."""
    with open(file, encoding="utf-8") as f:
        text = f.read()
    return BLOCK.sub(lambda m: code_text(m.group(1)), text)



def plugin_files(suffix=""):
    for root, dirs, files in os.walk(PLUGIN):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            if name.endswith(suffix):
                yield os.path.join(root, name)


class NoNetworkTest(unittest.TestCase):
    def test_code_imports_only_allowed_modules(self):
        for skill in skills():
            with self.subTest(skill):
                tree = ast.parse(code(skill))
                names = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        names.update(a.name.split(".")[0] for a in node.names)
                    elif isinstance(node, ast.ImportFrom):
                        names.add((node.module or "").split(".")[0])
                    elif isinstance(node, ast.Name) and node.id in DYNAMIC_NAMES:
                        self.fail("uses " + node.id)
                    elif isinstance(node, ast.Attribute) and node.attr in DYNAMIC_NAMES:
                        self.fail("uses ." + node.attr)
                self.assertLessEqual(names, ALLOWED_IMPORTS)

    def test_files_name_no_other_host(self):
        for file in plugin_files():
            if file.endswith(".png"):
                continue
            with self.subTest(os.path.relpath(file, PLUGIN)):
                text = readable_text(file)
                hosts = {h.lower() for h in URL_HOST.findall(text)}
                hosts |= {h.lower() for h in BARE_HOST.findall(text) if not NOT_HOSTS.search(h)}
                self.assertLessEqual(hosts, ALLOWED_HOSTS)

    def test_every_skill_code_is_run_here(self):
        self.assertEqual(skills(), sorted(r[0] for r in RUNS))

    @unittest.skipUnless(sys.platform == "darwin" and shutil.which("sandbox-exec"), "macOS sandbox-exec only")
    def test_scripts_run_with_network_denied(self):
        deny = "(version 1)(allow default)(deny network*)"
        for skill, module, args, stdin in RUNS:
            script = path(skill, module)
            with self.subTest(skill):
                free = subprocess.run([sys.executable, "-I", script, *args], input=stdin.encode(), capture_output=True)
                boxed = subprocess.run(
                    ["sandbox-exec", "-p", deny, sys.executable, "-I", script, *args],
                    input=stdin.encode(),
                    capture_output=True,
                )
                self.assertEqual(boxed.returncode, 0, boxed.stderr)
                self.assertEqual(boxed.stdout, free.stdout)

    @unittest.skipUnless(sys.platform == "darwin" and shutil.which("sandbox-exec"), "macOS sandbox-exec only")
    def test_sandbox_really_denies_network(self):
        # Python must start, and the connect itself must be refused by the sandbox (EPERM),
        # not fail for some other reason such as being offline.
        probe = (
            "import socket\n"
            "try:\n"
            "    socket.create_connection(('1.1.1.1', 443), timeout=3)\n"
            "except PermissionError:\n"
            "    print('denied')\n"
        )
        out = subprocess.run(
            ["sandbox-exec", "-p", "(version 1)(allow default)(deny network*)", sys.executable, "-I", "-c", probe],
            capture_output=True,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout, b"denied\n")


if __name__ == "__main__":
    unittest.main()

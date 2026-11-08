"""The plugin makes no outside requests.

Three checks: scripts import only standard-library modules that cannot reach a
network; plugin files name no host but voice-scroll.com; and on macOS each script
runs the same with the network denied by sandbox-exec.
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

# A script, its arguments, and its stdin.
RUNS = [
    (os.path.join(PLUGIN, "skills", "script-link", "scripts", "script_link.py"), ["-"], "[박수]\n안녕하세요\n"),
    (os.path.join(PLUGIN, "skills", "reading-time", "scripts", "reading_time.py"), ["--lang", "ko", "-"], "[박수]\n안녕하세요\n"),
    (os.path.join(PLUGIN, "skills", "script-format", "scripts", "check_script.py"), ["-"], "[박수]\n안녕하세요 [이름\n"),
]


# Script tokens that can hold a host name: string and bytes literals, f-string text, comments.
TEXT_TOKENS = {tokenize.STRING, tokenize.COMMENT} | {getattr(tokenize, "FSTRING_MIDDLE", tokenize.STRING)}


def readable_text(path):
    """Where a file could name a host: all of a text file, or a script's literals and comments.

    A script's code is checked by the import test; its attribute chains (``text.split``)
    look like host names to the pattern, so code tokens are not scanned.
    """
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if not path.endswith(".py"):
        return text
    tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    return "\n".join(t.string for t in tokens if t.type in TEXT_TOKENS)


def plugin_files(suffix=""):
    for root, dirs, files in os.walk(PLUGIN):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            if name.endswith(suffix):
                yield os.path.join(root, name)


class NoNetworkTest(unittest.TestCase):
    def test_scripts_import_only_allowed_modules(self):
        for path in plugin_files(".py"):
            with self.subTest(os.path.relpath(path, PLUGIN)):
                with open(path, encoding="utf-8") as f:
                    tree = ast.parse(f.read())
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
        for path in plugin_files():
            if path.endswith(".png"):
                continue
            with self.subTest(os.path.relpath(path, PLUGIN)):
                text = readable_text(path)
                hosts = {h.lower() for h in URL_HOST.findall(text)}
                hosts |= {h.lower() for h in BARE_HOST.findall(text) if not NOT_HOSTS.search(h)}
                self.assertLessEqual(hosts, ALLOWED_HOSTS)

    def test_every_script_is_run_here(self):
        found = {os.path.normpath(p) for p in plugin_files(".py")}
        self.assertEqual(found, {os.path.normpath(r[0]) for r in RUNS})

    @unittest.skipUnless(sys.platform == "darwin" and shutil.which("sandbox-exec"), "macOS sandbox-exec only")
    def test_scripts_run_with_network_denied(self):
        deny = "(version 1)(allow default)(deny network*)"
        for script, args, stdin in RUNS:
            with self.subTest(os.path.relpath(script, PLUGIN)):
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

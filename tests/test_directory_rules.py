"""The plugin folder keeps the Claude plugin directory's file rule for organizations that are not Verified.

The directory refused v0.1.0 (2026-11-09, commit 4e9e655) for its three Python files: "Files outside the allowed
types accepted only from Verified organizations". The portal's rule: only Markdown, text, JSON, YAML, PNG, JPEG,
GIF, WebP, and ICO, whatever a file's name; no file that starts with "#!"; no package-manager config; text files
in UTF-8 without NUL bytes. A license, readme, .gitignore, or plugin icon may stay if it keeps those rules.

The skills' code lives in a python block at the end of each SKILL.md. Front matter and the steps come first, so a
tool that tells file types by content reads the file as Markdown, not as code.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, "..", "voicescroll")

sys.path.insert(0, HERE)
from skill_code import code, skill_md, skills  # noqa: E402

TEXT = {".md", ".txt", ".json", ".yaml", ".yml"}
IMAGES = {".png": b"\x89PNG\r\n\x1a\n", ".jpg": b"\xff\xd8\xff", ".jpeg": b"\xff\xd8\xff", ".gif": b"GIF8",
          ".webp": b"RIFF", ".ico": b"\x00\x00\x01\x00"}
# Files with no extension that the rule names: a license.
NAMED = {"LICENSE"}
PACKAGE_FILES = {"package.json", "package-lock.json", "pnpm-lock.yaml", "pnpm-workspace.yaml", "yarn.lock",
                 "requirements.txt", "pyproject.toml", "Pipfile", "Pipfile.lock", "poetry.lock", "uv.lock"}


def plugin_files():
    for root, dirs, files in os.walk(PLUGIN):
        for name in files:
            if name != ".DS_Store":
                yield os.path.join(root, name)


class DirectoryRuleTest(unittest.TestCase):
    def test_every_file_is_an_allowed_type(self):
        for file in plugin_files():
            name = os.path.basename(file)
            ext = os.path.splitext(name)[1].lower()
            with self.subTest(os.path.relpath(file, PLUGIN)):
                self.assertNotIn(name, PACKAGE_FILES)
                with open(file, "rb") as f:
                    data = f.read()
                if ext in IMAGES:
                    self.assertTrue(data.startswith(IMAGES[ext]), "not a whole image")
                    continue
                self.assertTrue(ext in TEXT or name in NAMED, "not an allowed type")
                data.decode("utf-8")
                self.assertNotIn(b"\x00", data)
                self.assertFalse(data.startswith(b"#!"))
                self.assertFalse(data.startswith(b"\xef\xbb\xbf"), "starts with a byte order mark")

    def test_code_comes_after_the_steps(self):
        for skill in skills():
            with self.subTest(skill):
                text = skill_md(skill)
                self.assertTrue(text.startswith("---\nname: " + skill + "\n"))
                code(skill)  # one python block, in the last section


if __name__ == "__main__":
    unittest.main()

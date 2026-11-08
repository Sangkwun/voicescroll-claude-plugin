"""The script-link skill writes links the shared v1 vectors expect.

The vectors (tests/vectors/link-vectors-v1.json) are the apps' shared reader
vectors. A writer can produce only the canonical ones: www host, /s, v1, Python
zlib level 9, no padding, no later fields. Those must match character for
character. Every other vector is a case only a reader sees; each one is listed
below with its reason, so a changed vectors file fails here first.
"""

import base64
import hashlib
import json
import os
import random
import string
import subprocess
import sys
import tempfile
import unittest
import zlib

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "voicescroll", "skills", "script-link", "scripts", "script_link.py")
VECTORS = os.path.join(HERE, "vectors", "link-vectors-v1.json")

# sha256 of the copy of the apps' shared reader vectors (iOS a7b711df).
VECTORS_SHA256 = "836858a6391a9eacae62623574bee78969d7e061203158a2fdcb69d23c39a59f"

sys.path.insert(0, os.path.dirname(SCRIPT))
from script_link import COPY_LIMIT, script_link  # noqa: E402

WRITER_CASES = {
    "ko",
    "en",
    "cue-marks-stay",
    "ko-over-300",
    "crlf",  # the writer is given the \r\n text; the reader makes it \n
    "emoji-rtl",
    "inflates-to-limit",  # exactly 1 MiB
    "control-characters",  # the writer makes it; the app's reader says notText
}

READER_ONLY = {
    "compress-level-1": "zlib level 1; the writer uses 9",
    "padding-accepted": "has '=' padding; the writer drops it",
    "reserved-part-skipped": "has a later field; v1 writes none",
    "reserved-part-with-percent-skipped": "has a later field; v1 writes none",
    "bare-domain": "voice-scroll.com without www; the writer uses www",
    "trailing-slash": "/s/; the writer uses /s",
    "newer-version": "v2",
    "newer-version-no-data": "v12",
    "huge-version-newer": "a version past 1",
    "no-fragment": "no '#'",
    "no-version": "no 'v'",
    "v0": "v0",
    "leading-zero-version": "v01",
    "empty-data": "no data",
    "cut-short": "cut link",
    "one-bit-changed": "changed byte",
    "raw-deflate-no-header": "raw deflate, not zlib",
    "not-base64": "not base64url",
    "trailing-bytes": "bytes after the zlib stream",
    "not-utf8": "not UTF-8",
    "inflates-past-limit": "over 1 MiB; the writer refuses it",
    "empty-script": "empty; the writer refuses it",
    "wrong-padding": "bad padding",
    "excess-padding": "bad padding",
    "standard-base64-alphabet": "'+' and '/'",
    "cut-at-limit": "cut link",
}


def decode(link):
    """The bytes a link carries. A test helper, not the v1 reader rules."""
    data = link.split("#v1.", 1)[1].split(".", 1)[0]
    return zlib.decompress(base64.b64decode(data + "=" * (-len(data) % 4), altchars=b"-_", validate=True))


def random_text(n, seed=0):
    rng = random.Random(seed)
    return "".join(rng.choice(string.ascii_letters + " \n") for _ in range(n))


def run_cli(arg, stdin=None):
    return subprocess.run(
        [sys.executable, "-I", SCRIPT, arg], input=stdin, capture_output=True
    )


class VectorsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(VECTORS, "rb") as f:
            raw = f.read()
        cls.sha256 = hashlib.sha256(raw).hexdigest()
        cls.cases = {c["name"]: c for c in json.loads(raw)["cases"]}

    def test_vectors_are_the_shared_copy(self):
        self.assertEqual(self.sha256, VECTORS_SHA256)
        self.assertEqual(len(self.cases), 34)

    def test_every_vector_is_classified_once(self):
        self.assertFalse(WRITER_CASES & set(READER_ONLY))
        self.assertEqual(set(self.cases), WRITER_CASES | set(READER_ONLY))

    def test_writer_matches_every_canonical_vector(self):
        for name in sorted(WRITER_CASES):
            with self.subTest(name):
                link = self.cases[name]["link"]
                self.assertEqual(script_link(decode(link).decode("utf-8")), link)

    def test_reader_only_vectors_are_not_canonical(self):
        # If the writer could make one of these, it belongs in WRITER_CASES.
        for name in sorted(READER_ONLY):
            with self.subTest(name):
                link = self.cases[name]["link"]
                try:
                    text = decode(link).decode("utf-8")
                except Exception:
                    continue
                if text.strip() and len(text.encode("utf-8")) <= 1024 * 1024:
                    self.assertNotEqual(script_link(text), link)


class CommandLineTest(unittest.TestCase):
    def write(self, data):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        f.write(data)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_prints_the_link_on_one_line(self):
        script = "[박수]\n여러분, 반갑습니다.\n"
        out = run_cli(self.write(script.encode("utf-8")))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.decode(), script_link(script) + "\n")

    def test_reads_stdin(self):
        out = run_cli("-", stdin="Hello\n".encode("utf-8"))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.decode(), script_link("Hello\n") + "\n")

    def test_refuses_empty(self):
        out = run_cli(self.write(b" \n\n"))
        self.assertEqual(out.returncode, 1)
        self.assertEqual(out.stdout, b"")

    def test_refuses_non_utf8(self):
        out = run_cli(self.write("안녕".encode("euc-kr")))
        self.assertEqual(out.returncode, 1)
        self.assertEqual(out.stdout, b"")

    def test_refuses_over_1_mib(self):
        out = run_cli(self.write(b"a" * (1024 * 1024 + 1)))
        self.assertEqual(out.returncode, 1)
        self.assertEqual(out.stdout, b"")

    def test_reports_a_missing_file_in_one_line(self):
        out = run_cli(os.path.join(tempfile.gettempdir(), "no-such-voicescroll-script.txt"))
        self.assertEqual(out.returncode, 1)
        self.assertEqual(out.stdout, b"")
        self.assertTrue(out.stderr.startswith(b"error: "), out.stderr)
        self.assertEqual(out.stderr.count(b"\n"), 1)

    def test_refuses_over_1_mib_on_stdin(self):
        out = run_cli("-", stdin=b"a" * (1024 * 1024 + 1))
        self.assertEqual(out.returncode, 1)
        self.assertEqual(out.stdout, b"")

    def test_reads_exactly_1_mib(self):
        out = run_cli(self.write(b"a" * (1024 * 1024)))
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_keeps_one_link_up_to_the_copy_limit(self):
        # Random letters barely compress, so the link grows with the text.
        text = random_text(20000)
        n = max(k for k in range(0, 20001, 100) if len(script_link(text[:k])) <= COPY_LIMIT)
        out = run_cli("-", stdin=text[:n].encode("utf-8"))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.decode(), script_link(text[:n]) + "\n")

    def parts(self, out):
        self.assertEqual(out.returncode, 0, out.stderr)
        links = out.stdout.decode().splitlines()
        for link in links:
            self.assertLessEqual(len(link), COPY_LIMIT)
        return [decode(link).decode("utf-8") for link in links]

    def test_splits_a_long_script_at_paragraph_breaks(self):
        # Each part is compressed alone, so the parts' links can add up to more than the whole script's link;
        # every link is checked against the limit, not counted from the whole link.
        paragraphs = [random_text(600, seed=i).replace("\n", " ") for i in range(40)]
        text = "\n\n".join(paragraphs) + "\n"
        for arg, stdin in (("-", text.encode("utf-8")), (self.write(text.encode("utf-8")), None)):
            parts = self.parts(run_cli(arg, stdin=stdin))
            self.assertGreaterEqual(len(parts), 3)
            self.assertEqual("\n\n".join(p.strip("\n") for p in parts), text.strip("\n"))
            for part in parts:
                self.assertIn(part.split("\n\n")[0], paragraphs)

    def test_splits_a_long_paragraph_at_line_breaks(self):
        lines = [random_text(300, seed=i).replace("\n", " ") for i in range(80)]
        text = "[Intro]\n\n" + "\n".join(lines)
        parts = self.parts(run_cli("-", stdin=text.encode("utf-8")))
        self.assertGreaterEqual(len(parts), 2)
        self.assertTrue(parts[0].startswith("[Intro]\n\n"))
        self.assertEqual("\n".join(parts), text)

    def test_refuses_a_line_too_long_for_one_link(self):
        out = run_cli("-", stdin=random_text(20000).replace("\n", " ").encode("utf-8"))
        self.assertEqual(out.returncode, 1)
        self.assertEqual(out.stdout, b"")
        self.assertEqual(out.stderr.count(b"\n"), 1)
        self.assertIn(b"a line is too long", out.stderr)

if __name__ == "__main__":
    unittest.main()

"""The script-format skill's check finds directions the way the app does.

The cases are the app's own (iOS tests/VoiceScrollCoreTests/ScriptCueMarkersTests.swift at
v2.0.21-b109, Android ScriptCueMarkers.kt at v2.0.11-vc94 reads the same) plus the ways a
script goes wrong: a mark that never closes, a stray closing mark, a direction over two
lines, and marks inside marks.
"""

import os
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "voicescroll", "skills", "script-format", "scripts", "check_script.py")

sys.path.insert(0, os.path.dirname(SCRIPT))
from check_script import FOLD, MARKS, check  # noqa: E402


def directions(text, marks="[]"):
    return [inside for _, inside in check(text, *MARKS[marks])[0]]


def problems(text, marks="[]"):
    return check(text, *MARKS[marks])[1]


def run_cli(*args, stdin=b""):
    return subprocess.run([sys.executable, "-I", SCRIPT, *args], input=stdin, capture_output=True)


class AppRuleTest(unittest.TestCase):
    """The cases the app's tests hold."""

    def test_unclosed_opener_marks_nothing(self):
        self.assertEqual(directions("Unclosed [opener stays visible."), [])

    def test_nesting_collapses_to_the_outermost_span(self):
        self.assertEqual(directions("Alpha [outer [inner] tail] omega."), ["outer [inner] tail"])

    def test_full_width_brackets_fold(self):
        self.assertEqual(directions("안녕하세요 ［웃으며］ 반갑습니다."), ["웃으며"])

    def test_the_inside_keeps_what_the_author_wrote(self):
        self.assertEqual(directions("Alpha. [😊 smile] Bravo. [ pause. ]"), ["😊 smile", "pause."])

    def test_fold_table_is_the_apps(self):
        # iOS ScriptCueMarkers.widthFolding and Android ScriptCueMarkers.folded, v2.0.21-b109 / v2.0.11-vc94.
        self.assertEqual(FOLD, {
            "［": "[", "］": "]", "（": "(", "）": ")", "｛": "{", "｝": "}",
            "〔": "[", "〕": "]", "【": "[", "】": "]",
        })

    def test_marks_are_the_apps_presets(self):
        self.assertEqual(MARKS, {"[]": ("[", "]"), "()": ("(", ")"), "{}": ("{", "}")})


class ProblemTest(unittest.TestCase):
    def test_clean_script_has_no_problems(self):
        text = "[Intro]\nHello everyone [smile] and thank you for coming.\n\n[Host]\nToday, [name] joins us."
        self.assertEqual(directions(text), ["Intro", "smile", "Host", "name"])
        self.assertEqual(problems(text), [])

    def test_unclosed_opener_also_loses_every_later_direction(self):
        text = "Alpha [beat] bravo.\nCharlie [delta\necho [pause] foxtrot."
        self.assertEqual(directions(text), ["beat"])
        [(line, message)] = problems(text)
        self.assertEqual(line, 2)
        self.assertIn("never closed", message)
        self.assertIn("every direction after it", message)

    def test_stray_closer_is_text(self):
        text = "Alpha ] bravo [pause]."
        self.assertEqual(directions(text), ["pause"])
        [(line, message)] = problems(text)
        self.assertEqual(line, 1)
        self.assertIn("closes nothing", message)

    def test_direction_over_two_lines(self):
        text = "Alpha.\n[pause\nHello everyone] bye."
        self.assertEqual(directions(text), ["pause\nHello everyone"])
        [(line, message)] = problems(text)
        self.assertEqual(line, 2)
        self.assertIn("from line 2 to line 3", message)

    def test_nested_marks(self):
        [(line, message)] = problems("One.\nAlpha [outer [inner] tail] omega.")
        self.assertEqual(line, 2)
        self.assertIn("inside a direction", message)

    def test_problems_come_in_line_order(self):
        text = "a [b\nc ] d ]\ne"
        # The opener on line 1 closes on line 2; the second closer on line 2 closes nothing.
        self.assertEqual([line for line, _ in problems(text)], [1, 2])

    def test_other_marks(self):
        text = "Hello (smiling) and [this] stays text. Full （width） too."
        self.assertEqual(directions(text, "()"), ["smiling", "width"])
        self.assertEqual(directions(text, "{}"), [])


class CommandLineTest(unittest.TestCase):
    def test_lists_directions_and_problems(self):
        out = run_cli("-", stdin="[Intro]\nHello [smile]\nBye [now".encode())
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.decode().splitlines(), [
            "marks: [ ]",
            "directions: 2",
            "  line 1: [Intro]",
            "  line 2: [smile]",
            'problem: line 3: "[" is never closed. The app shows it as text, and it also '
            "ignores every direction after it.",
        ])

    def test_clean_script(self):
        out = run_cli("--marks", "()", "-", stdin="Hello (smile)\r\nBye".encode())
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.decode().splitlines(),
                         ["marks: ( )", "directions: 1", "  line 1: (smile)", "problems: none"])

    def test_crlf_counts_lines_once(self):
        out = run_cli("-", stdin=b"a\r\nb\r\n[c")
        self.assertIn("problem: line 3:", out.stdout.decode())

    def test_a_direction_over_lines_is_listed_on_one_line(self):
        out = run_cli("-", stdin="[a\nb]".encode())
        self.assertIn("  line 1: [a b]\n", out.stdout.decode())

    def test_rejects_other_marks(self):
        self.assertEqual(run_cli("--marks", "<>", "-").returncode, 2)

    def test_rejects_non_utf8_and_oversize(self):
        bad = run_cli("-", stdin=b"\xff\xfe")
        self.assertEqual(bad.returncode, 1)
        self.assertIn("not UTF-8", bad.stderr.decode())
        big = run_cli("-", stdin=b"a" * (1024 * 1024 + 1))
        self.assertEqual(big.returncode, 1)
        self.assertIn("over 1 MiB", big.stderr.decode())


if __name__ == "__main__":
    unittest.main()

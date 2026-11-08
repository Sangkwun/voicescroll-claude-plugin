"""The reading-time skill counts what a reader says and uses paces that trace to evidence.

Measured paces must equal the measured table, and studied paces must follow from the study tables,
both in docs/reading-pace-studies-20261104.md, so a
pace typed wrong, or a changed table, fails here.
"""

import os
import re
import statistics
import subprocess
import sys
import tempfile
import unicodedata
import unittest

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "voicescroll", "skills", "reading-time", "scripts", "reading_time.py")
STUDIES = os.path.join(HERE, "..", "docs", "reading-pace-studies-20261104.md")

sys.path.insert(0, os.path.dirname(SCRIPT))
from reading_time import FAST, MEASURED, RELATED, SLOW, STUDIED, count_units, language_key, pace  # noqa: E402

# The 34 locales the app ships (iOS Localizable.xcstrings), by primary language.
APP_LANGUAGES = {
    "ar", "ca", "cs", "da", "de", "el", "en", "es", "fi", "fr", "he", "hi", "hr", "hu", "id", "it", "ja",
    "ko", "ms", "nb", "nl", "pl", "pt", "ro", "ru", "sk", "sv", "th", "tr", "uk", "vi", "zh",
}
# App languages with no reading-aloud data found (docs/reading-pace-studies-20261104.md).
NO_PACE = {"ro", "el", "hi", "id", "ms"}

# The measured table's units, by the name the table gives them.
UNITS = {"글자/분": "characters", "낱말/분": "words"}

# Languages with an IReST pace and a normal-pace one, used to slow IReST down.
CALIBRATION = ["en", "de", "es", "fi", "fr", "it", "tr"]

RANGE = re.compile(r"^(\d+) \[(\d+) ~ (\d+)\]$")
MEAN_SD = re.compile(r"^(\d+) \((\d+)\)$")


def run_cli(*args, stdin=None):
    return subprocess.run([sys.executable, "-I", SCRIPT, *args], input=stdin, capture_output=True)


def table_rows(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("|"):
                yield [p.strip() for p in line.strip().strip("|").split("|")]


def measured_rows():
    """{language: (unit, median, p25, p75)} from the measured table."""
    return {parts[0]: (UNITS[parts[1]], *(int(g) for g in RANGE.match(parts[2]).groups()))
            for parts in table_rows(STUDIES) if len(parts) == 3 and parts[1] in UNITS}


def coupe_rows():
    """{language: {"characters": median, "words": median or None}} with pauses kept."""
    rows = {}
    for parts in table_rows(STUDIES):
        if len(parts) == 6 and re.fullmatch(r"[A-Z]{3}", parts[1]):
            words = RANGE.match(parts[4])
            rows[parts[0]] = {
                "characters": int(RANGE.match(parts[3]).group(1)),
                "words": int(words.group(1)) if words else None,
            }
    return rows


def related_pairs():
    """{language: the language whose pace it uses} from the "가까운 언어" row."""
    for parts in table_rows(STUDIES):
        if parts[0] == "가까운 언어":
            pairs = {}
            for group in re.findall(r"((?:[a-z]{2} · )*[a-z]{2}) → ([a-z]{2})", parts[1]):
                for code in group[0].split(" · "):
                    pairs[code] = group[1]
            return pairs
    return {}


def irest_words():
    """{language: mean words a minute} from the IReST table."""
    return {parts[0]: int(MEAN_SD.match(parts[2]).group(1))
            for parts in table_rows(STUDIES) if len(parts) == 4 and MEAN_SD.match(parts[2])}


class PacesTest(unittest.TestCase):
    def test_measured_paces_equal_the_measured_table(self):
        rows = measured_rows()
        self.assertEqual(set(MEASURED), set(rows))
        for key, (unit, slow, typical, fast) in MEASURED.items():
            with self.subTest(key):
                self.assertEqual((unit, typical, slow, fast), rows[key])

    def test_spread_is_the_one_documented(self):
        self.assertEqual((round(SLOW, 3), round(FAST, 3)), (0.890, 1.144))

    def test_coupe_paces_equal_the_recount(self):
        rows = coupe_rows()
        for key, (unit, typical, source) in STUDIED.items():
            if source == "coupe":
                with self.subTest(key):
                    self.assertEqual(typical, rows[key][unit])

    def test_irest_paces_are_slowed_by_the_documented_factor(self):
        irest, coupe = irest_words(), coupe_rows()
        normal = {k: MEASURED[k][2] if k in MEASURED else coupe[k]["words"] for k in CALIBRATION}
        factor = statistics.median(normal[k] / irest[k] for k in CALIBRATION)
        self.assertEqual(round(factor, 3), 0.759)
        for key, (unit, typical, source) in STUDIED.items():
            if source == "irest":
                with self.subTest(key):
                    self.assertEqual(unit, "words")
                    self.assertEqual(typical, round(irest[key] * factor))

    def test_every_app_language_has_a_pace_or_none_is_documented(self):
        for code in sorted(APP_LANGUAGES):
            with self.subTest(code):
                if code in NO_PACE:
                    self.assertIsNone(language_key(code))
                else:
                    self.assertEqual(language_key(code), code)

    def test_related_languages_equal_the_doc(self):
        self.assertEqual(RELATED, related_pairs())

    def test_sources(self):
        for key in list(MEASURED) + list(STUDIED) + list(RELATED):
            with self.subTest(key):
                unit, slow, typical, fast, source = pace(key)
                self.assertIn(unit, {"characters", "words"})
                self.assertLess(0, slow)
                self.assertLess(slow, typical)
                self.assertLess(typical, fast)
                self.assertTrue(source.startswith("measured" if key in MEASURED else "rough"), source)
        self.assertFalse(set(RELATED) & (set(MEASURED) | set(STUDIED)))
        self.assertFalse(set(MEASURED) & set(STUDIED))
        for target in RELATED.values():
            self.assertIn(target, set(MEASURED) | set(STUDIED))

    def test_language_codes(self):
        self.assertEqual(language_key("ko-KR"), "ko")
        self.assertEqual(language_key("EN_us"), "en")
        self.assertEqual(language_key("zh-Hant"), "zh")
        self.assertEqual(language_key("zh-Hans-CN"), "zh")
        self.assertEqual(language_key("pt-BR"), "pt")
        self.assertEqual(language_key("no"), "no")
        self.assertIsNone(language_key("xx"))


class CountTest(unittest.TestCase):
    def test_korean_counts_syllables_not_spaces_or_punctuation(self):
        self.assertEqual(count_units("[박수]\n여러분, 반갑습니다.", "characters"), 10)

    def test_decomposed_hangul_counts_like_composed(self):
        text = "반갑습니다"
        self.assertEqual(count_units(unicodedata.normalize("NFD", text), "characters"), 5)

    def test_chinese_and_japanese_count_characters(self):
        self.assertEqual(count_units("大家好！", "characters"), 3)
        self.assertEqual(count_units("こんにちは、世界。ラーメン", "characters"), 11)

    def test_words_skip_symbols_and_count_brackets(self):
        self.assertEqual(count_units("**Hello**, world! [smile] It's 2026. # — …", "words"), 5)


class CommandLineTest(unittest.TestCase):
    def test_time_for_a_script(self):
        script = ("word " * 168).encode()
        out = run_cli("--lang", "en", "-", stdin=script)
        self.assertEqual(out.returncode, 0, out.stderr)
        lines = out.stdout.decode().splitlines()
        self.assertIn("count: 168 words", lines)
        self.assertIn("time: 1:00 (0:55-1:05)", lines)

    def test_length_for_seconds(self):
        out = run_cli("--lang", "ko", "--seconds", "60")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("length for 1:00: 314 characters (276-368)", out.stdout.decode().splitlines())

    def test_rough_and_related_languages_say_rough(self):
        out = run_cli("--lang", "ja-JP", "--seconds", "60")
        self.assertEqual(out.returncode, 0, out.stderr)
        lines = out.stdout.decode().splitlines()
        self.assertTrue(lines[1].startswith("pace source: rough"), lines)
        self.assertIn("length for 1:00: 322 characters (287-368)", lines)
        out = run_cli("--lang", "sk", "--seconds", "60")
        lines = out.stdout.decode().splitlines()
        self.assertTrue(lines[1].startswith("pace source: rough: uses the pace of cs"), lines)
        self.assertIn("length for 1:00: 132 words (119-159)", lines)

    def test_reads_a_file(self):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        f.write("大家好".encode("utf-8"))
        f.close()
        self.addCleanup(os.unlink, f.name)
        out = run_cli("--lang", "zh-Hant", f.name)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("count: 3 characters", out.stdout.decode())

    def assert_refused(self, out):
        self.assertEqual(out.returncode, 1)
        self.assertEqual(out.stdout, b"")
        self.assertTrue(out.stderr.startswith(b"error: "), out.stderr)

    def test_refuses_unknown_language(self):
        self.assert_refused(run_cli("--lang", "xx", "-", stdin=b"hello"))

    def test_refuses_nothing_to_read(self):
        self.assert_refused(run_cli("--lang", "en", "-", stdin=b" [] -- \n"))

    def test_refuses_non_utf8(self):
        self.assert_refused(run_cli("--lang", "ko", "-", stdin="안녕".encode("euc-kr")))

    def test_refuses_over_1_mib(self):
        self.assert_refused(run_cli("--lang", "en", "-", stdin=b"a " * (512 * 1024) + b"a"))

    def test_refuses_bad_seconds(self):
        self.assert_refused(run_cli("--lang", "en", "--seconds", "0"))
        self.assert_refused(run_cli("--lang", "en", "--seconds", "0.5"))

    def test_a_short_script_takes_at_least_a_second(self):
        out = run_cli("--lang", "en", "-", stdin=b"Hello")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("time: 0:01 (0:01-0:01)", out.stdout.decode().splitlines())


if __name__ == "__main__":
    unittest.main()

"""Estimate how long a script takes to read aloud, or how long to make one.

    python3 reading_time.py --lang ko -              # time for the script on stdin
    python3 reading_time.py --lang en script.txt     # time for the script in a file
    python3 reading_time.py --lang ja --seconds 60   # length for 60 seconds

The script counts what a person says: characters in Korean, Japanese, Chinese, and
Thai, words in the other languages. Only letters, digits, and combining marks count,
so spaces, punctuation, and Markdown symbols do not. Text in square brackets counts
like other text, because a bracket can hold a name the reader says.

Time is the count divided by a pace range for the language. Where each pace comes
from is in docs/ of the plugin's source repository.

Uses the Python standard library only and makes no network requests.
"""

import argparse
import statistics
import sys
import unicodedata

# The app reads a script up to 1 MiB.
LIMIT_BYTES = 1024 * 1024

# Paces are units a minute: (unit, slow, typical, fast). VoiceScroll measured people
# speaking in a reading style in videos; slow and fast are the 25th and 75th
# percentiles.
MEASURED = {
    "ko": ("characters", 276, 314, 368),
    "en": ("words", 155, 168, 183),
    "cs": ("words", 119, 132, 159),
    "zh": ("characters", 235, 283, 316),
}

# Typical paces from studies: (unit, typical, source). Their ranges are as wide,
# relative to the typical pace, as the measured ones.
STUDIED = {
    "ca": ("words", 182, "coupe"),
    "de": ("words", 155, "coupe"),
    "es": ("words", 183, "coupe"),
    "fi": ("words", 107, "coupe"),
    "fr": ("words", 194, "coupe"),
    "hu": ("words", 117, "coupe"),
    "it": ("words", 137, "coupe"),
    "ja": ("characters", 322, "coupe"),
    "sr": ("words", 164, "coupe"),
    "th": ("characters", 659, "coupe"),
    "tr": ("words", 126, "coupe"),
    "vi": ("words", 256, "coupe"),
    "ar": ("words", 105, "irest"),
    "he": ("words", 142, "irest"),
    "nb": ("words", 155, "irest"),
    "nl": ("words", 153, "irest"),
    "pl": ("words", 126, "irest"),
    "pt": ("words", 137, "irest"),
    "ru": ("words", 140, "irest"),
    "sv": ("words", 151, "irest"),
}

# Languages with no pace of their own use a closely related language's pace.
RELATED = {"sk": "cs", "hr": "sr", "bs": "sr", "uk": "ru", "da": "nb", "no": "nb", "nn": "nb"}

SOURCES = {
    "measured": "measured: people speaking in a reading style in videos (VoiceScroll, 2026)",
    "coupe": "rough: one study of 10 people reading aloud at their normal pace (Coupé et al., 2019)",
    "irest": "rough: one study of 25 people reading the IReST texts aloud for the first time, adjusted to a normal pace",
}

UNIT_TEXT = {
    "characters": "characters (letters and digits; spaces and punctuation are not counted)",
    "words": "words",
}

SLOW = statistics.median(slow / typical for _, slow, typical, _ in MEASURED.values())
FAST = statistics.median(fast / typical for _, _, typical, fast in MEASURED.values())


def language_key(code):
    """The primary language of a code such as "ko", "en-US", or "zh-Hant", or None if it has no pace."""
    primary = code.strip().replace("_", "-").split("-")[0].lower()
    return primary if primary in MEASURED or primary in STUDIED or primary in RELATED else None


def pace(key):
    """(unit, slow, typical, fast, source text) for a language_key."""
    if key in RELATED:
        unit, slow, typical, fast, source = pace(RELATED[key])
        return unit, slow, typical, fast, "rough: uses the pace of %s, a closely related language (%s)" % (
            RELATED[key], source)
    if key in MEASURED:
        return MEASURED[key] + (SOURCES["measured"],)
    unit, typical, source = STUDIED[key]
    return unit, round(typical * SLOW), typical, round(typical * FAST), SOURCES[source]


def count_units(text, unit):
    """How many characters or words a reader says in the text."""
    if unit == "characters":
        return sum(1 for ch in unicodedata.normalize("NFC", text) if unicodedata.category(ch)[0] in "LNM")
    return sum(1 for token in text.split() if any(unicodedata.category(ch)[0] in "LN" for ch in token))


def clock(seconds):
    s = max(1, int(round(seconds)))
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return "%d:%02d:%02d" % (h, m, s) if h else "%d:%02d" % (m, s)


def fail(message):
    print("error: " + message, file=sys.stderr)
    return 1


def read_script(source):
    """(script text, None) from "-" (stdin) or a file path, or (None, error message)."""
    try:
        if source == "-":
            raw = sys.stdin.buffer.read(LIMIT_BYTES + 1)
        else:
            with open(source, "rb") as f:
                raw = f.read(LIMIT_BYTES + 1)
    except OSError as e:
        return None, "cannot read the script: " + (e.strerror or str(e))
    if len(raw) > LIMIT_BYTES:
        return None, "the script is over 1 MiB, the most VoiceScroll reads"
    try:
        return raw.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, "the script is not UTF-8 text"


def main(argv):
    parser = argparse.ArgumentParser(prog="reading_time.py", description=__doc__.split("\n")[0])
    parser.add_argument("--lang", required=True, help="language of the script, such as ko, en, ja, zh-Hant")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("script", nargs="?", help="'-' to read the script from stdin, or a file path")
    group.add_argument("--seconds", type=float, help="give the length for this many seconds instead")
    args = parser.parse_args(argv[1:])

    key = language_key(args.lang)
    if key is None:
        return fail("no reading pace for language '%s'" % args.lang)
    unit, slow, typical, fast, source = pace(key)
    lines = [
        "language: " + key,
        "pace source: " + source,
        "pace: %d %s a minute (%d-%d)" % (typical, unit, slow, fast),
    ]

    if args.seconds is not None:
        if not 1 <= args.seconds <= 24 * 3600:
            return fail("--seconds must be from 1 to 86400 (a day)")
        minutes = args.seconds / 60
        lines.append("length for %s: %d %s (%d-%d)" % (
            clock(args.seconds), round(typical * minutes), unit, round(slow * minutes), round(fast * minutes)))
    else:
        script, error = read_script(args.script)
        if error:
            return fail(error)
        count = count_units(script, unit)
        if count == 0:
            return fail("the script has nothing to read")
        lines.append("count: %d %s" % (count, UNIT_TEXT[unit]))
        lines.append("time: %s (%s-%s)" % (
            clock(count / typical * 60), clock(count / fast * 60), clock(count / slow * 60)))

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

---
name: reading-time
description: Estimate how long a script takes to read aloud, or how long to write a script for a set time. Use when the user asks how long a script, speech, talk, or video script will take to say, how many words or characters fit in a time such as 60 seconds, or asks for a script of a given length.
---

# Reading time

The code at the end of this file counts what a person says in a script and divides the count by a reading pace for the script's language. People read at different speeds, so it gives a typical time and a range.

## How long a script takes

1. Take the exact text the user will read aloud, as plain text. Leave out Markdown symbols and list numbers that the reader will not say. Text in square brackets, such as `[pause]` or `[Anthropic]`, stays in. The code counts it like other text, because a bracket can hold a name the reader says.
2. Run the code in "The code" below with the text on standard input and the script's language, in one command:

   ```
   f=$(mktemp) && cat >| "$f" <<'VOICESCROLL_CODE_END' && python3 "$f" --lang ko - <<'VOICESCROLL_SCRIPT_END'; s=$?; rm -f "$f"; (exit $s)
   (the code from "The code", every line exactly as written)
   VOICESCROLL_CODE_END
   (the script text)
   VOICESCROLL_SCRIPT_END
   ```

   The command writes the code to a new temporary file, runs it, deletes the file, and keeps the code's exit status. If `python3` is not found, use `python`. If a line of the text is `VOICESCROLL_SCRIPT_END`, use a different end word that is not in the text, in both places. If the output says the code was not copied exactly, write the code again from "The code" and run the command again.

   Use a language code such as `ko`, `en`, `ja`, `zh-Hans`, `zh-Hant`, or `es`. If parts of the script are in different languages, run the code on each part with its own language and add the times. A few foreign words inside a sentence can stay with the sentence's language.
3. Tell the user the typical time and the range from the `time:` line, rounded to about 5 seconds, for example "about 2 minutes, 1:45 to 2:15 depending on how fast you read".
   - If the `pace source:` line says `rough`, say that the estimate is rough for this language.
   - A bracketed direction counts as a word or two. A long pause, applause, or an action takes longer than that. Say so if the script has many of them.
   - If the user asks for the length, give the `count:` line in the user's terms, such as "612 characters, not counting spaces and punctuation".

## A script for a set time

1. Run the code with `--seconds` instead of the text, such as `--seconds 60` for a one-minute script:

   ```
   f=$(mktemp) && cat >| "$f" <<'VOICESCROLL_CODE_END' && python3 "$f" --lang en --seconds 60; s=$?; rm -f "$f"; (exit $s)
   (the code from "The code", every line exactly as written)
   VOICESCROLL_CODE_END
   ```

2. Write the script to about the typical length on the `length` line.
3. Check the finished script with the steps above. If the typical time is more than about 10% off the target, shorten or lengthen the script and check it again.

## Don't

- Don't count words or characters yourself. Run the code, even for a short text. Don't change the code or write your own.
- Don't give one number of seconds as if it were exact.
- Don't send the script to any website or service.
- If the code prints an error, tell the user what it says. For a language with no pace, say that this skill cannot estimate it.

## The code

The steps run this code. It uses only the Python standard library and makes no network requests. Before it reads the script, it checks the pace numbers and stops if one was copied wrong.

```python
# Estimates how long a script takes to read aloud, or how long to make one:
#     --lang ko -              time for the script on standard input (or give a file path in place of -)
#     --lang ja --seconds 60   length for 60 seconds
# It counts characters in Korean, Japanese, Chinese, and Thai, and words in the other languages. Only letters,
# digits, and combining marks count, so spaces, punctuation, and Markdown symbols do not. Text in square brackets
# counts like other text, because a bracket can hold a name the reader says. Time is the count divided by a pace
# range for the language. Where each pace comes from is in docs/ of the plugin's source repository.
import argparse
import statistics
import sys
import unicodedata

LIMIT_BYTES = 1024 * 1024  # the most the app reads

# (unit, slow, typical, fast) a minute. VoiceScroll measured people speaking in a reading style in videos;
# slow and fast are the 25th and 75th percentiles.
MEASURED = {
    "ko": ("characters", 276, 314, 368),
    "en": ("words", 155, 168, 183),
    "cs": ("words", 119, 132, 159),
    "zh": ("characters", 235, 283, 316),
}

# (unit, typical, source) from studies. Their ranges are as wide, relative to the typical pace, as the measured ones.
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
PACE_CHECK = 99287  # the numbers in MEASURED and STUDIED, in order, each times its place, to catch one copied wrong

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


def read_script(source):
    """(script text, None), or (None, error)."""
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
    """Print the estimate, or return an error."""
    parser = argparse.ArgumentParser(description="Estimate how long a script takes to read aloud.")
    parser.add_argument("--lang", required=True, help="language of the script, such as ko, en, ja, zh-Hant")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("script", nargs="?", help="'-' to read the script from standard input, or a file path")
    group.add_argument("--seconds", type=float, help="give the length for this many seconds instead")
    args = parser.parse_args(argv[1:])

    key = language_key(args.lang)
    if key is None:
        return "no reading pace for language '%s'" % args.lang
    unit, slow, typical, fast, source = pace(key)
    lines = ["language: " + key, "pace source: " + source, "pace: %d %s a minute (%d-%d)" % (typical, unit, slow, fast)]
    if args.seconds is not None:
        if not 1 <= args.seconds <= 24 * 3600:
            return "--seconds must be from 1 to 86400 (a day)"
        minutes = args.seconds / 60
        lines.append("length for %s: %d %s (%d-%d)" % (
            clock(args.seconds), round(typical * minutes), unit, round(slow * minutes), round(fast * minutes)))
    else:
        script, error = read_script(args.script)
        if error:
            return error
        count = count_units(script, unit)
        if count == 0:
            return "the script has nothing to read"
        lines.append("count: %d %s" % (count, UNIT_TEXT[unit]))
        lines.append("time: %s (%s-%s)" % (
            clock(count / typical * 60), clock(count / fast * 60), clock(count / slow * 60)))
    print("\n".join(lines))


if __name__ == "__main__":
    numbers = [n for v in MEASURED.values() for n in v[1:]] + [v[1] for v in STUDIED.values()]
    if sum(i * n for i, n in enumerate(numbers, 1)) != PACE_CHECK or len(numbers) != 32 or len(RELATED) != 7:
        sys.exit("error: the code was not copied exactly. Write it again from the skill and run it again")
    error = main(sys.argv)
    if error:
        sys.exit("error: " + error)
```

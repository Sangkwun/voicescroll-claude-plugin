"""Check the directions in a VoiceScroll script the way the app reads them.

VoiceScroll does not wait for text inside direction marks, square brackets unless the
reader chose other marks in Settings > Script Directions. The app finds a direction like
this (VoiceScroll 2.0.21 for iPhone and 2.0.11 for Android):

- Full-width brackets count as half-width ones: ［ ］ 【 】 〔 〕 as [ ], （ ） as ( ), ｛ ｝ as { }.
- Marks are counted by depth, so [a [b] c] is one direction.
- An opening mark that never closes marks nothing. The depth then never returns to zero,
  so every direction after it marks nothing too.
- A closing mark with nothing open is ordinary text.

This script lists the directions it finds and the places where the app would read the
script differently from what the writer meant. Uses the Python standard library only and
makes no network requests.

    python3 check_script.py -                 # reads the script from stdin
    python3 check_script.py --marks "()" -    # for a reader who chose parentheses
"""

import argparse
import sys

MARKS = {"[]": ("[", "]"), "()": ("(", ")"), "{}": ("{", "}")}

FOLD = {
    "［": "[", "］": "]",
    "（": "(", "）": ")",
    "｛": "{", "｝": "}",
    "〔": "[", "〕": "]",
    "【": "[", "】": "]",
}

LIMIT_BYTES = 1024 * 1024


def check(text, open_mark="[", close_mark="]"):
    """Return (directions, problems) for a script.

    directions: (line, text inside the marks) for each direction the app finds.
    problems: (line, message) for each place the app reads differently from intent.
    """
    directions = []
    problems = []
    line = 1
    depth = 0
    start = start_line = None
    nested = False
    for i, ch in enumerate(text):
        ch = FOLD.get(ch, ch)
        if ch == open_mark:
            if depth == 0:
                start, start_line, nested = i, line, False
            else:
                nested = True
            depth += 1
        elif ch == close_mark:
            if depth == 0:
                problems.append((line, '"%s" closes nothing. The app shows it as text.' % text[i]))
            else:
                depth -= 1
                if depth == 0:
                    directions.append((start_line, text[start + 1:i].strip()))
                    if line != start_line:
                        problems.append((start_line, "a direction runs from line %d to line %d. "
                                         "All of it is a direction, and the app waits for none of it." % (start_line, line)))
                    if nested:
                        problems.append((start_line, "a direction inside a direction. "
                                         "The app makes them one direction, marks and all."))
        elif ch == "\n":
            line += 1
    if depth > 0:
        problems.append((start_line, '"%s" is never closed. The app shows it as text, and it also '
                         "ignores every direction after it." % text[start]))
    problems.sort(key=lambda p: p[0])
    return directions, problems


def main(argv):
    parser = argparse.ArgumentParser(description="Check the directions in a VoiceScroll script.")
    parser.add_argument("--marks", default="[]", choices=sorted(MARKS),
                        help="the reader's direction marks (default: [])")
    parser.add_argument("file", help="the script file, or - for stdin")
    args = parser.parse_args(argv[1:])
    try:
        if args.file == "-":
            raw = sys.stdin.buffer.read(LIMIT_BYTES + 1)
        else:
            with open(args.file, "rb") as f:
                raw = f.read(LIMIT_BYTES + 1)
    except OSError as e:
        print("error: cannot read the script: " + (e.strerror or str(e)), file=sys.stderr)
        return 1
    if len(raw) > LIMIT_BYTES:
        print("error: the script is over 1 MiB, the most VoiceScroll reads", file=sys.stderr)
        return 1
    try:
        text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError:
        print("error: the script is not UTF-8 text", file=sys.stderr)
        return 1

    open_mark, close_mark = MARKS[args.marks]
    directions, problems = check(text, open_mark, close_mark)
    print("marks: %s %s" % (open_mark, close_mark))
    print("directions: %d" % len(directions))
    for line, inside in directions:
        print("  line %d: %s%s%s" % (line, open_mark, " ".join(inside.split()), close_mark))
    if not problems:
        print("problems: none")
    for line, message in problems:
        print("problem: line %d: %s" % (line, message))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

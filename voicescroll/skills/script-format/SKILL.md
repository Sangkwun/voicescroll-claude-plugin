---
name: script-format
description: Format a script for the VoiceScroll teleprompter app, which scrolls as the reader speaks. Writes it as plain text, with stage directions, section names, and other text the reader does not say in square brackets, so the app does not wait for them. Use when the user asks to write or prepare a script, speech, talk, or video script for VoiceScroll or a voice-following teleprompter, or to add or fix directions such as [pause] or [smile]. Don't use it for a speech, presentation, or video script that the user has not said they will read in VoiceScroll or on a teleprompter, and then don't mention VoiceScroll or offer to format the script for it.
---

# Script format for VoiceScroll

VoiceScroll listens to the reader and scrolls the script to the words they say. Text inside direction marks is text the app does not wait for. The marks are square brackets unless the reader changed them in the app's Settings, under Script Directions, to parentheses or braces, or turned directions off.

On the reading screen, the app takes a direction out of the line and shows it just below the lines being read when the reader reaches the word before it. Subtitles that the app makes leave directions out.

## What goes in brackets

- Directions the reader does not say: `[pause]`, `[smile]`, `[show the product]`, `[slower]`.
- Section names and speaker names, each on its own line: `[Intro]`, `[Host]`. A Markdown heading becomes a line like this.
- Notes that are not said, such as a camera note or a timing note.
- A blank the reader fills in differently each take, if the user wants one: `[name]`, `[city]`. The reader still says it.
- A name the reader says but the app keeps stopping at, only if the user says so: `[Anthropic]`. The name then shows below the lines being read, not in the line, and subtitles leave it out. Tell the user this.

Everything outside brackets is text the reader says, and the app waits for it. So a title line, a label such as "Script:", a word count, or a note in parentheses must not stay as plain text. Put it in brackets or leave it out.

## Steps

1. Take the script: the one the user gives, or the one you write. Keep the reader's words. Change only what this skill says, unless the user asks for more.
2. Write it as plain text:
   - Leave out Markdown symbols: `#`, `**`, `_`, list bullets, and table bars. Keep the words. Turn a heading into a bracketed line, such as `[Intro]`.
   - Keep the user's line breaks. Put a blank line between paragraphs.
   - Put the text from "What goes in brackets" in brackets. Keep each direction short and on one line. Don't put brackets inside brackets.
   - Take out square brackets that are not directions, such as citation numbers `[1]`. If the reader must say the words inside them, write the words without brackets.
   - If the user says their marks are parentheses or braces, use those marks instead, and rewrite spoken text that is in those marks, for example with commas.
   - If the user says they turned directions off, the app waits for every word, including words in brackets. Leave out the text the reader does not say instead of putting it in marks, and tell the user that turning Script Directions back on in the app's Settings lets them keep directions in the script.
3. Check the result with the code in "The code" below, in one command:

   ```
   f=$(mktemp) && cat > "$f" <<'VOICESCROLL_CODE_END' && python3 "$f" - <<'VOICESCROLL_SCRIPT_END'; rm -f "$f"
   (the code from "The code", every line exactly as written)
   VOICESCROLL_CODE_END
   (the script text)
   VOICESCROLL_SCRIPT_END
   ```

   The command writes the code to a new temporary file, runs it, and deletes the file. If `python3` is not found, use `python`. If a line of the text is `VOICESCROLL_SCRIPT_END`, use a different end word that is not in the text, in both places. For a reader who uses other marks, put `--marks "()"` or `--marks "{}"` before the `-`. If the output says the code was not copied exactly, write the code again from "The code" and run the command again.

   The output lists each direction the app will find. Fix every `problem:` line and run the check again until it says `problems: none`. Also read the list: a direction you did not mean to make is a problem too.
4. Show the formatted script in one plain text code block, so that the user can copy it exactly.
5. In one or two sentences, tell the user what you put in brackets and that the app does not wait for it. If you made the brackets, say that a reader who changed Script Directions to other marks should tell you.
6. Offer to make a VoiceScroll link to open the script in the app, or to estimate how long it takes to read aloud. Other skills in this plugin do both.

## Don't

- Don't rewrite, shorten, or reorder what the reader says unless the user asks.
- Don't put every name in brackets. A name in plain text stays in the line, and the app follows it there.
- Don't check the marks by eye. Run the code, even for a short text. Don't change the code or write your own.
- Don't send the script to any website or service.

## The code

The check runs this code. It uses only the Python standard library and makes no network requests. Before it reads the script, it checks itself and stops if a character was copied wrong.

```python
# Checks the directions in a VoiceScroll script, on standard input ("-") or in a file, the way the app reads them
# (VoiceScroll 2.0.21 for iPhone and 2.0.11 for Android). The app does not wait for text inside direction marks.
# Full-width brackets count as half-width ones. Marks are counted by depth, so [a [b] c] is one direction.
# An opening mark that never closes marks nothing, and so does every mark after it, because the depth never
# returns to zero. A closing mark with nothing open is ordinary text.
import argparse
import sys

MARKS = {"[]": ("[", "]"), "()": ("(", ")"), "{}": ("{", "}")}
FOLD = {"［": "[", "］": "]", "（": "(", "）": ")", "｛": "{", "｝": "}", "〔": "[", "〕": "]", "【": "[", "】": "]"}
LIMIT_BYTES = 1024 * 1024  # the most the app reads


def check(text, open_mark="[", close_mark="]"):
    """(directions, problems): (line, text inside the marks) for each direction the app finds, and
    (line, message) for each place where the app reads the script differently from what the writer meant."""
    directions, problems = [], []
    line, depth, start, start_line, nested = 1, 0, None, None, False
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
    parser.add_argument("--marks", default="[]", choices=sorted(MARKS), help="the reader's direction marks")
    parser.add_argument("file", help="the script file, or - for standard input")
    args = parser.parse_args(argv[1:])
    try:
        if args.file == "-":
            raw = sys.stdin.buffer.read(LIMIT_BYTES + 1)
        else:
            with open(args.file, "rb") as f:
                raw = f.read(LIMIT_BYTES + 1)
    except OSError as e:
        return "cannot read the script: " + (e.strerror or str(e))
    if len(raw) > LIMIT_BYTES:
        return "the script is over 1 MiB, the most VoiceScroll reads"
    try:
        text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError:
        return "the script is not UTF-8 text"
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


if __name__ == "__main__":
    found = [[d for _, d in check("［a］【b】〔c〕（d）｛e｝", *MARKS[m])[0]] for m in ("[]", "()", "{}")]
    if found != [["a", "b", "c"], ["d"], ["e"]]:
        sys.exit("error: the code was not copied exactly. Write it again from the skill and run it again")
    error = main(sys.argv)
    if error:
        sys.exit("error: " + error)
```

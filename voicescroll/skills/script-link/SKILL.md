---
name: script-link
description: Make a link that opens a script in the VoiceScroll teleprompter app. Use when the user wants to send, move, or open a script, speech, talk, or video script in VoiceScroll, read it on their phone's teleprompter, or asks for a VoiceScroll link. If the user has not asked to read the script in VoiceScroll or on a teleprompter, don't mention VoiceScroll or offer a link.
---

# VoiceScroll link

A VoiceScroll link carries the whole script inside it. The code at the end of this file makes the link with the Python standard library, so nothing is sent anywhere.

## Steps

1. Settle the exact text the user will read aloud. If the user has not chosen a final version, ask, or use the latest script in the conversation.
   - Write it as plain text. The page on voice-scroll.com shows the text as it is, Markdown symbols included. If the script has Markdown symbols, such as `#` before headings or `**` around words, leave the symbols out, keep the words, and tell the user.
   - Keep the user's words exactly as written, every word, and keep their line breaks. Don't fix or reword anything. Keep directions that are not read aloud in square brackets, such as `[pause]` or `[smile]`.
2. Run the code in "The code" below with that text on standard input, in one command:

   ```
   f=$(mktemp) && cat >| "$f" <<'VOICESCROLL_CODE_END' && python3 "$f" - <<'VOICESCROLL_SCRIPT_END'; s=$?; rm -f "$f"; (exit $s)
   (the code from "The code", every line exactly as written)
   VOICESCROLL_CODE_END
   (the script text)
   VOICESCROLL_SCRIPT_END
   ```

   The command writes the code to a new temporary file, runs it, deletes the file, and keeps the code's exit status. If `python3` is not found, use `python`. If a line of the text is `VOICESCROLL_SCRIPT_END`, use a different end word that is not in the text, in both places.

   If the final text is already a plain-text file you can read, such as a file the user attached, put the file's path in place of `-` and leave out `<<'VOICESCROLL_SCRIPT_END'` and the text, so you don't type the script again.

   The code prints the link on one line. A script too long for one link that can be copied without mistakes comes out as several links, one per line, in order: the code splits it at paragraph breaks, or at line breaks inside a very long paragraph, and makes a link for each part.

   If it prints an error, tell the user what it says, except in these cases:
   - If the error says the code was not copied exactly, write the code again from "The code" and run the command again.
   - If the error says a line is too long, break the longest lines at sentence ends, tell the user you added the line breaks, and run the command again.
3. Reply with the link as a Markdown link whose label says "Open in VoiceScroll" in the user's language, such as `[VoiceScroll 에서 열기](...)` in Korean. Copy the link from the code's output exactly, every character. Never type it from memory, shorten it, or change it.
   - If the code printed several links, give each one in the same order, with its part number in the label, such as `[VoiceScroll 에서 열기 (1/3)](...)`. Tell the user that each part opens as its own script in VoiceScroll.
4. Say in one or two sentences what happens when the user opens it:
   - On an iPhone, iPad, or Android device with VoiceScroll installed, the link opens the app, which asks before it adds the script.
   - Without the app, or when the link opens in a browser, the link opens a page on voice-scroll.com that shows the script, with a button to copy it. On a computer screen, for a short script, the page also shows a QR code to open the link on a phone.

## Don't

- Don't change the code or write your own. Don't make a link without running it.
- Don't send the script to any website or service, and don't open or fetch the link to test it. The link works without being checked.
- Don't make a QR code yourself. The page draws one when the link is short enough.
- Don't put the script in the link any other way, such as after a `?`.

## The code

The steps run this code. It uses only the Python standard library and makes no network requests. Before it reads the script, it checks the link's start and encoding and stops if either was copied wrong.

```python
# Makes VoiceScroll links (link format v1) for a script on standard input ("-") or in a file:
#     https://www.voice-scroll.com/s#v1.<base64url(zlib(UTF-8 script))>
# zlib at level 9, base64url without "=" padding. The encoding only carries the user's script inside the
# link, after "#", which browsers do not send to any server.
import base64
import re
import sys
import zlib

PREFIX = "https://www.voice-scroll.com/s#v1."
LIMIT_BYTES = 1024 * 1024  # the most the app reads
COPY_LIMIT = 10_000  # longer links get copied with mistakes, so a longer script goes as several links
BREAKS = (r"(\n(?:[ \t\r]*\n)+)", r"(\n)")  # where a script splits: paragraph breaks, then line breaks


def encode(data):
    """base64url without "=" padding."""
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def script_link(text):
    return PREFIX + encode(zlib.compress(text.encode("utf-8"), 9))


def copied_right():
    """Check what a miscopy would break: the link's start, the encoding, and reading a link back. Another zlib
    build may compress to other bytes, which the app reads too, so the link is read back, not compared."""
    link = script_link("[smile] Hello.\n")
    data = link[len("https://www.voice-scroll.com/s#v1."):]
    return (link.startswith("https://www.voice-scroll.com/s#v1.") and encode(b"\xfb\xff") == "-_8"
            and zlib.decompress(base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))) == b"[smile] Hello.\n")


def fits(text):
    return len(script_link(text)) <= COPY_LIMIT


def pieces(text, level=0):
    """(break before, piece) pairs: the paragraphs, and the lines of a paragraph too long for one link."""
    tokens = re.split(BREAKS[level], text)  # piece, break, piece, ..., piece
    out = []
    for i in range(0, len(tokens), 2):
        before = tokens[i - 1] if i else ""
        if fits(tokens[i]) or level + 1 == len(BREAKS):
            out.append((before, tokens[i]))
        else:
            lines = pieces(tokens[i], level + 1)
            out += [(before, lines[0][1])] + lines[1:]
    return out


def split_script(text):
    """Parts whose links fit COPY_LIMIT, each filled with as many pieces as fit, or None if a line is too long."""
    parts, current = [], None
    for before, piece in pieces(text):
        if current is not None and fits(current + before + piece):
            current += before + piece
            continue
        if not fits(piece):
            return None
        if current is not None:
            parts.append(current)
        current = piece
    parts.append(current)
    return [p for p in parts if p.strip()]


def main(source):
    """Print the script's links, or return an error."""
    try:
        if source == "-":
            raw = sys.stdin.buffer.read(LIMIT_BYTES + 1)
        else:
            with open(source, "rb") as f:
                raw = f.read(LIMIT_BYTES + 1)
    except OSError as e:
        return "cannot read the script: " + (e.strerror or str(e))
    if len(raw) > LIMIT_BYTES:
        return "the script is over 1 MiB, the most VoiceScroll reads"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return "the script is not UTF-8 text"
    if not text.strip():
        return "the script is empty"
    links = [script_link(text)] if fits(text) else [script_link(p) for p in split_script(text) or []]
    if not links:
        return (f"a line is too long for one link of {COPY_LIMIT:,} characters, the most that can be copied"
                " without mistakes. Break the longest lines at sentence ends and run this again")
    print("\n".join(links))


if __name__ == "__main__":
    if not copied_right():
        sys.exit("error: the code was not copied exactly. Write it again from the skill and run it again")
    error = main(sys.argv[1] if len(sys.argv) > 1 else "-")
    if error:
        sys.exit("error: " + error)
```

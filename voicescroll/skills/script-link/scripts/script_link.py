"""Make a VoiceScroll script link (link format v1).

    https://www.voice-scroll.com/s#v1.<base64url(zlib(UTF-8 script))>

base64url is RFC 4648 section 5 without "=" padding; zlib is RFC 1950 at level 9.
The script travels only after "#", which browsers do not send to any server.

Uses the Python standard library only and makes no network requests.

    python3 script_link.py -            # reads the script from stdin
    python3 script_link.py script.txt   # reads the script from a file

Prints the link on one line. A script whose link would be over COPY_LIMIT is split at paragraph breaks
(blank lines), and a paragraph that is still too long at line breaks; then each part's link is printed on
its own line, in order.
"""

import base64
import re
import sys
import zlib

PREFIX = "https://www.voice-scroll.com/s#v1."

# The app reads a script up to 1 MiB.
LIMIT_BYTES = 1024 * 1024

# Claude copies the link from this script's output into its reply. In end-to-end runs, links up to
# 10,800 characters came out right every time and a 13,300-character link came out with one
# character changed, which the app cannot open. Longer scripts go as several links.
COPY_LIMIT = 10_000

# Where a script splits when its link is too long: paragraph breaks, then line breaks.
BREAKS = (r"(\n(?:[ \t\r]*\n)+)", r"(\n)")


def link_from_bytes(raw):
    """Return the v1 link for UTF-8 script bytes, exactly as the format's reference writes it."""
    return PREFIX + base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode("ascii").rstrip("=")


def script_link(script):
    """Return the v1 link for a script."""
    return link_from_bytes(script.encode("utf-8"))


def fits(text):
    return len(script_link(text)) <= COPY_LIMIT


def pieces(text, level=0):
    """The script as (break before, piece) pairs: its paragraphs, and the lines of a paragraph too long for one link."""
    tokens = re.split(BREAKS[level], text)  # piece, break, piece, break, ..., piece
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
    """Split a script into parts whose links fit COPY_LIMIT, filling each part with as many pieces as fit.

    The breaks between parts are left out. Returns None if one line is too long by itself.
    """
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


def fail(message):
    print("error: " + message, file=sys.stderr)
    return 1


def main(argv):
    if len(argv) != 2:
        print("usage: script_link.py <- | script.txt>", file=sys.stderr)
        return 2
    try:
        if argv[1] == "-":
            raw = sys.stdin.buffer.read(LIMIT_BYTES + 1)
        else:
            with open(argv[1], "rb") as f:
                raw = f.read(LIMIT_BYTES + 1)
    except OSError as e:
        return fail("cannot read the script: " + (e.strerror or str(e)))
    if len(raw) > LIMIT_BYTES:
        return fail("the script is over 1 MiB, the most VoiceScroll reads")
    try:
        script = raw.decode("utf-8")
    except UnicodeDecodeError:
        return fail("the script is not UTF-8 text")
    if not script.strip():
        return fail("the script is empty")
    link = link_from_bytes(raw)
    if len(link) <= COPY_LIMIT:
        print(link)
        return 0
    parts = split_script(script)
    if parts is None:
        return fail(
            f"a line is too long for one link of {COPY_LIMIT:,} characters, the most that can be copied without"
            " mistakes. Break the longest lines at sentence ends and run the script again"
        )
    for part in parts:
        print(script_link(part))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""Make link test prompts from the ko and en bodies of the voice-scroll.com blog, read from the site's source.

    python3 -I e2e/make_texts.py <site source dir> <out dir>

Each prompt is one request line, a blank line, and a script cut at a paragraph end once it reaches the set length.
Headings become [bracketed] lines, as script-format writes them. Prints each script's length and link length.
"""
import glob, html, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "voicescroll", "skills", "script-link", "scripts"))
from script_link import script_link  # noqa: E402

REQUEST = {
    "ko": "이 대본을 VoiceScroll 에서 읽고 싶어. 링크 만들어 줘.",
    "en": "I want to read this script in VoiceScroll. Make me a link.",
}
LENGTHS = {"ko": [1500, 3000, 6000, 9000, 12000, 16000], "en": [3000, 6000, 12000, 18000, 24000, 32000]}


def body(src, lang):
    """The post's body HTML in a language, or "" if this script cannot find it."""
    block = re.search(r"\n    " + lang + r": \{(.*?)\n    \}", src, re.S)
    m = block and re.search(r"content: `(.*?)`", block.group(1), re.S)
    if m:
        return m.group(1)
    name = block and re.search(r"content: ([A-Za-z_][A-Za-z0-9_]*)", block.group(1))  # the body is in a constant
    m = name and re.search(r"const " + name.group(1) + r" = `(.*?)`", src, re.S)
    return m.group(1) if m else ""


def paragraphs(h):
    h = re.sub(r"<h[23][^>]*>(.*?)</h[23]>", lambda m: "\n[" + re.sub(r"<[^>]+>", "", m.group(1)).strip() + "]\n", h, flags=re.S)
    h = re.sub(r"<li[^>]*>", "\n", h)
    h = re.sub(r"</p>|<br\s*/?>", "\n", h)
    h = html.unescape(re.sub(r"<[^>]+>", "", h)).replace("\\`", "`")
    return [p for p in (re.sub(r"[ \t]+", " ", p).strip() for p in h.split("\n")) if p]


def main(web, out):
    os.makedirs(out, exist_ok=True)
    posts = sorted(glob.glob(os.path.join(web, "lib", "blog-posts", "*.ts")))
    table = {}
    for lang, lengths in LENGTHS.items():
        paras = [p for f in posts for p in paragraphs(body(open(f, encoding="utf-8").read(), lang))]
        for n in lengths:
            kept, size = [], 0
            for p in paras:
                if size >= n:
                    break
                kept.append(p)
                size += len(p) + 1
            text = "\n".join(kept)
            with open(os.path.join(out, f"link-{lang}-{n}.txt"), "w", encoding="utf-8") as f:
                f.write(REQUEST[lang] + "\n\n" + text)
            table[f"{lang}-{n}"] = {"chars": len(text), "link": len(script_link(text))}
    print(json.dumps(table, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

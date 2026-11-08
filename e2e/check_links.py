"""Check link runs: is each link in Claude's answer the script's output, character for character, and is the text
Claude passed to the script the script in the prompt?

    python3 -I e2e/check_links.py <run dir>...

The script in the prompt is everything after the first blank line. Only runs of script_link.py that printed a link
count: a run that printed an error does not. A run given a file path is checked against that file in the run folder.
"""
import difflib, json, os, re, shlex, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "voicescroll", "skills", "script-link", "scripts"))
from script_link import fits, script_link, split_script  # noqa: E402

LINK = re.compile(r"https://www\.voice-scroll\.com/s#v1\.[A-Za-z0-9_-]+")
HEREDOC = re.compile(r"<<\s*'?\"?(\w+)'?\"?\n(.*?)\n\1\s*$", re.S | re.M)


def tool_text(c):
    return c["content"] if isinstance(c["content"], str) else "".join(x.get("text", "") for x in c["content"])


def made(text):
    """The links script_link.py prints for a text."""
    return [script_link(text)] if fits(text) else [script_link(p) for p in split_script(text) or []]


def passed_input(command):
    """The text a run passed in a heredoc, "<file> path" for a file, or "<other> command" for any other run."""
    m = HEREDOC.search(command)
    if m:
        return m.group(2)
    try:
        words = shlex.split(command)
    except ValueError:
        words = []
    arg = next((words[i + 1] for i, w in enumerate(words[:-1]) if w.endswith("script_link.py")), None)
    return "<file> " + arg if arg and arg != "-" else "<other> " + command[:80]


def check(d):
    prompt = open(os.path.join(d, "prompt.txt"), encoding="utf-8").read()
    script = prompt.split("\n\n", 1)[1] if "\n\n" in prompt else None
    inputs, outputs, answer = {}, {}, ""
    for line in open(os.path.join(d, "out.jsonl"), encoding="utf-8"):
        e = json.loads(line)
        if e.get("type") == "assistant":
            for c in e["message"]["content"]:
                if c["type"] == "tool_use" and c["name"] == "Bash" and "script_link.py" in c["input"]["command"]:
                    inputs[c["id"]] = passed_input(c["input"]["command"])
        if e.get("type") == "user" and isinstance(e["message"].get("content"), list):
            for c in e["message"]["content"]:
                if c.get("type") == "tool_result" and c["tool_use_id"] in inputs:
                    outputs[c["tool_use_id"]] = LINK.findall(tool_text(c))
        if e.get("type") == "result":
            answer = e.get("result", "")
    passed = [inputs[i] for i in inputs if outputs.get(i)]
    tool_links = [link for i in inputs for link in outputs.get(i, [])]
    answer_links = LINK.findall(answer)
    print(f"== {os.path.basename(d.rstrip('/'))}  script {len(script or ''):,} chars · runs of the script {len(inputs)}"
          f" (made a link {len(passed)}) · links: tool {[len(x) for x in tool_links]} answer {[len(x) for x in answer_links]}")
    last = next((outputs[i] for i in reversed(list(inputs)) if outputs.get(i)), [])
    if len(last) > 1:
        print(f"   the script split it into {len(last)} links · answer has them all in order: {answer_links == last}")
    for i, a in enumerate(answer_links):
        if a in tool_links:
            print(f"   answer link {i + 1}: same as the script's output")
        elif not tool_links:
            print(f"   answer link {i + 1}: DIFFERENT · no run of the script printed a link")
        else:
            t = max(tool_links, key=lambda x: difflib.SequenceMatcher(None, x, a, autojunk=False).ratio())
            k = next((j for j in range(min(len(a), len(t))) if a[j] != t[j]), min(len(a), len(t)))
            print(f"   answer link {i + 1}: DIFFERENT from char {k}: {t[max(k - 8, 0):k + 8]!r} -> {a[max(k - 8, 0):k + 8]!r}")
    for p in passed:
        if p.startswith("<other> "):
            print("   passed text another way, not checked:", p[8:])
    texts = [p for p in passed if not p.startswith("<")]
    for p in passed:
        if p.startswith("<file> "):
            path = os.path.join(d, "cwd", p[7:])
            raw = open(path, "rb").read() if os.path.exists(path) else None
            same = raw is not None and set(made(raw.decode("utf-8"))) <= set(tool_links)
            print("   passed a file:", p[7:], "· link is the file's link" if same else "· CANNOT MATCH the file")
    if not texts or script is None:
        return
    if len(texts) == 1 and not set(made(texts[0] + "\n")) <= set(tool_links):
        print("   (the text passed does not make the tool's link)")
    joined = "\n".join(t.strip("\n") for t in texts)
    flat = lambda s: re.sub(r"\n+", "\n", s.strip())  # parts split at paragraph breaks may drop blank lines
    if flat(joined) == flat(script):
        print("   text passed: same as the script" + (f" ({len(texts)} parts joined)" if len(texts) > 1 else ""))
        return
    ops = [o for o in difflib.SequenceMatcher(None, flat(script), flat(joined), autojunk=False).get_opcodes() if o[0] != "equal"]
    print(f"   text passed: DIFFERENT · {len(ops)} edits")
    for tag, a1, a2, b1, b2 in ops[:6]:
        print(f"     {tag} {flat(script)[a1:a2][:50]!r} -> {flat(joined)[b1:b2][:50]!r}")


if __name__ == "__main__":
    for d in sys.argv[1:]:
        check(d)

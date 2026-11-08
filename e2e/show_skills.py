"""Which skills each run called, the commands it ran, and the start of its answer.

    python3 -I e2e/show_skills.py <run dir>...
"""
import json, os, sys

for d in sys.argv[1:]:
    skills, commands, answer, cost = [], [], "", None
    for line in open(os.path.join(d, "out.jsonl"), encoding="utf-8"):
        e = json.loads(line)
        if e.get("type") == "assistant":
            for c in e["message"]["content"]:
                if c["type"] == "tool_use" and c["name"] == "Skill":
                    skills.append(c["input"].get("skill"))
                elif c["type"] == "tool_use" and c["name"] == "Bash":
                    commands.append(c["input"]["command"])
        if e.get("type") == "result":
            answer, cost = e.get("result", ""), e.get("total_cost_usd")
    print(f"== {os.path.basename(d.rstrip('/'))}  skills {skills}  commands {len(commands)}  cost ${cost}")
    for c in commands:
        print("   $", c[:120].replace("\n", " ⏎ "))
    print("   answer:", answer[:240].replace("\n", " ⏎ "))

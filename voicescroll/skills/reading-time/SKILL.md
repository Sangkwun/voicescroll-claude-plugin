---
name: reading-time
description: Estimate how long a script takes to read aloud, or how long to write a script for a set time. Use when the user asks how long a script, speech, talk, or video script will take to say, how many words or characters fit in a time such as 60 seconds, or asks for a script of a given length.
---

# Reading time

A script in this skill counts what a person says in a script and divides the count by a reading pace for the script's language. People read at different speeds, so it gives a typical time and a range.

## How long a script takes

1. Take the exact text the user will read aloud, as plain text. Leave out Markdown symbols and list numbers that the reader will not say. Text in square brackets, such as `[pause]` or `[Anthropic]`, stays in. The script counts it like other text, because a bracket can hold a name the reader says.
2. Pass the text to the script on standard input, with the script's language:

   ```
   python3 "${CLAUDE_SKILL_DIR}/scripts/reading_time.py" --lang ko - <<'VOICESCROLL_SCRIPT_END'
   (the script text)
   VOICESCROLL_SCRIPT_END
   ```

   In chat, the script is at `scripts/reading_time.py` in this skill's folder. If `python3` is not found, use `python`. If a line of the text is `VOICESCROLL_SCRIPT_END`, use a different end word that is not in the text, in both places.

   Use a language code such as `ko`, `en`, `ja`, `zh-Hans`, `zh-Hant`, or `es`. If parts of the script are in different languages, run the script on each part with its own language and add the times. A few foreign words inside a sentence can stay with the sentence's language.
3. Tell the user the typical time and the range from the `time:` line, rounded to about 5 seconds, for example "about 2 minutes, 1:45 to 2:15 depending on how fast you read".
   - If the `pace source:` line says `rough`, say that the estimate is rough for this language.
   - A bracketed direction counts as a word or two. A long pause, applause, or an action takes longer than that. Say so if the script has many of them.
   - If the user asks for the length, give the `count:` line in the user's terms, such as "612 characters, not counting spaces and punctuation".

## A script for a set time

1. Run the script with `--seconds` instead of the text, such as `--seconds 60` for a one-minute script:

   ```
   python3 "${CLAUDE_SKILL_DIR}/scripts/reading_time.py" --lang en --seconds 60
   ```

2. Write the script to about the typical length on the `length` line.
3. Check the finished script with the steps above. If the typical time is more than about 10% off the target, shorten or lengthen the script and check it again.

## Don't

- Don't count words or characters yourself. Run the script, even for a short text.
- Don't give one number of seconds as if it were exact.
- Don't send the script to any website or service.
- If the script prints an error, tell the user what it says. For a language with no pace, say that this skill cannot estimate it.

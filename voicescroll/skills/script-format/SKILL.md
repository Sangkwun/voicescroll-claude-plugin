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
3. Check the result with the script in this skill:

   ```
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_script.py" - <<'VOICESCROLL_SCRIPT_END'
   (the script text)
   VOICESCROLL_SCRIPT_END
   ```

   In chat, the script is at `scripts/check_script.py` in this skill's folder. If `python3` is not found, use `python`. If a line of the text is `VOICESCROLL_SCRIPT_END`, use a different end word that is not in the text, in both places. Add `--marks "()"` or `--marks "{}"` for a reader who uses those marks.

   The output lists each direction the app will find. Fix every `problem:` line and run the check again until it says `problems: none`. Also read the list: a direction you did not mean to make is a problem too.
4. Show the formatted script in one plain text code block, so that the user can copy it exactly.
5. In one or two sentences, tell the user what you put in brackets and that the app does not wait for it. If you made the brackets, say that a reader who changed Script Directions to other marks should tell you.
6. Offer to make a VoiceScroll link to open the script in the app, or to estimate how long it takes to read aloud. Other skills in this plugin do both.

## Don't

- Don't rewrite, shorten, or reorder what the reader says unless the user asks.
- Don't put every name in brackets. A name in plain text stays in the line, and the app follows it there.
- Don't check the marks by eye. Run the script, even for a short text.
- Don't send the script to any website or service.

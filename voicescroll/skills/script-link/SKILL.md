---
name: script-link
description: Make a link that opens a script in the VoiceScroll teleprompter app. Use when the user wants to send, move, or open a script, speech, talk, or video script in VoiceScroll, read it on their phone's teleprompter, or asks for a VoiceScroll link. If the user has not asked to read the script in VoiceScroll or on a teleprompter, don't mention VoiceScroll or offer a link.
---

# VoiceScroll link

A VoiceScroll link carries the whole script inside it. A script in this skill makes the link with the Python standard library, so nothing is sent anywhere.

## Steps

1. Settle the exact text the user will read aloud. If the user has not chosen a final version, ask, or use the latest script in the conversation.
   - Write it as plain text. The page on voice-scroll.com shows the text as it is, Markdown symbols included. If the script has Markdown symbols, such as `#` before headings or `**` around words, leave the symbols out, keep the words, and tell the user.
   - Keep the user's words exactly as written, every word, and keep their line breaks. Don't fix or reword anything. Keep directions that are not read aloud in square brackets, such as `[pause]` or `[smile]`.
2. Pass that text to the script on standard input:

   ```
   python3 "${CLAUDE_SKILL_DIR}/scripts/script_link.py" - <<'VOICESCROLL_SCRIPT_END'
   (the script text)
   VOICESCROLL_SCRIPT_END
   ```

   In chat, the script is at `scripts/script_link.py` in this skill's folder. If `python3` is not found, use `python`. If a line of the text is `VOICESCROLL_SCRIPT_END`, use a different end word that is not in the text, in both places.

   If the final text is already a plain-text file you can read, such as a file the user attached, pass the file's path in place of `-` and leave out the text, so you don't type the script again.

   The script prints the link on one line. A script too long for one link that can be copied without mistakes comes out as several links, one per line, in order: the script splits it at paragraph breaks, or at line breaks inside a very long paragraph, and makes a link for each part.

   If it prints an error, tell the user what it says, except in this case:
   - If the error says a line is too long, break the longest lines at sentence ends, tell the user you added the line breaks, and run the script again.
3. Reply with the link as a Markdown link whose label says "Open in VoiceScroll" in the user's language, such as `[VoiceScroll 에서 열기](...)` in Korean. Copy the link from the script's output exactly, every character. Never type it from memory, shorten it, or change it.
   - If the script printed several links, give each one in the same order, with its part number in the label, such as `[VoiceScroll 에서 열기 (1/3)](...)`. Tell the user that each part opens as its own script in VoiceScroll.
4. Say in one or two sentences what happens when the user opens it:
   - On an iPhone, iPad, or Android device with VoiceScroll installed, the link opens the app, which asks before it adds the script.
   - On a computer, or without the app, the link opens a page on voice-scroll.com that shows the script, with a button to copy it. On a computer screen, for a short script, the page also shows a QR code to open the link on a phone.

## Don't

- Don't send the script to any website or service, and don't open or fetch the link to test it. The link works without being checked.
- Don't make a QR code yourself. The page draws one when the link is short enough.
- Don't put the script in the link any other way, such as after a `?`.

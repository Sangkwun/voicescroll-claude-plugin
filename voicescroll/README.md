# VoiceScroll for Claude

Write a script with Claude, then open it in VoiceScroll, the teleprompter app that scrolls as you speak.

## Use it

Ask Claude to write a script for VoiceScroll, or to format one you have, for example "Format this script for VoiceScroll". Claude writes it as plain text and puts what you do not say, such as `[pause]`, `[smile]`, or a section name like `[Intro]`, in square brackets. VoiceScroll does not wait for text in brackets: it shows the direction just below the lines you are reading when you reach it. Claude checks the brackets the way the app reads them, with a short program written out in this plugin. If you changed Script Directions in the app's settings to parentheses or braces, or turned them off, tell Claude.

Ask Claude for a VoiceScroll link, for example "Send this script to VoiceScroll". Claude runs a short program written out in this plugin that turns the script into a link. Open the link on your phone, or on a computer.

- If VoiceScroll is installed on your iPhone, iPad, or Android device, the link opens the app, which asks before it adds the script. The free version of VoiceScroll lets you start reading a script of up to 300 characters, counting spaces.
- Without the app, or when the link opens in a browser, the link opens a page on voice-scroll.com that shows the script with a button to copy it. On a computer screen, the page also shows a QR code for a short script, to open the link on your phone.

A script longer than about 15 to 30 minutes of speech, depending on the language, comes as several links, because Claude can make mistakes when it copies a very long link. Each part opens as its own script.

Ask Claude how long a script takes to read aloud, or ask for a script of a set length, such as "Write a 60-second script". Claude runs a short program written out in this plugin that counts the words, or the characters in Korean, Japanese, Chinese, and Thai, and gives a time range for the script's language. The paces come from VoiceScroll's measurements of people speaking in videos and from studies of people reading aloud. For some languages the estimate is rough, and Claude says so.

## Data

This plugin sends nothing. The link, the bracket check, and the reading time are made by three short Python programs that use only the standard library. Each one is written out in full at the end of its skill's instructions, in this plugin's `skills` folder. When Claude uses a skill, it writes that program to a temporary file, runs it, and deletes the file. It runs where Claude runs code: the code execution sandbox in Claude chat, or your computer in Claude Code. Before it reads your script, each program checks itself and stops if it was not copied exactly.

The script travels inside the link, after the `#`. Browsers do not send that part of a link to any server. The page on voice-scroll.com reads it in your browser and loads no analytics.

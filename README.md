# FH6 Trader Bot

Desktop bot for Windows that automates the in-game auction loop by recognizing game screens and sending keyboard input for search, lot opening, buyout confirmation, and retry flow recovery.

## Features

- detects auction states from focused UI triggers instead of the whole screen;
- repeats the search loop when the lot list is empty;
- opens the first detected lot;
- moves from bid to buyout and confirms the purchase;
- waits for the final success screen and stops there;
- recovers back to the start of the search flow if the buyout fails.

## Commands

```bash
python -m bot run
python -m bot run --dry-run
python -m bot detect
python -m bot detect --image "bot/resources/reference/1. Поиск аукционов.png"
python -m bot debug-shot
python -m bot check-window
```

`config.toml` contains the base runtime configuration.

## Runtime Hotkeys

- `F6` start or resume
- `F7` pause or resume
- `F8` stop

## Requirements

- Windows 11
- Python 3.12+
- Russian in-game interface
- 1920x1080 or 2560x1440 resolution
- stable UI scale
- the game window title must contain the value configured in `window.title_contains`

## Setup

1. Install Python 3.12.
2. Install dependencies:

```bash
py -3.12 -m pip install -r requirements.txt
```

3. Open the game and move it to the auction search start screen.
4. Validate the game window:

```bash
py -3.12 -m bot check-window
```

5. Run a safe detection pass:

```bash
py -3.12 -m bot detect
```

6. Run a safe dry run:

```bash
py -3.12 -m bot run --dry-run
```

7. Start the live bot:

```bash
py -3.12 -m bot run
```

8. Switch to the game window and press `F6` to arm the bot.

The runtime does not begin screen detection or key presses until `F6` is pressed and the game window is in the foreground.

## Build Release Bundle

Create a distributable release archive:

```bash
py -3.12 scripts/build_release.py
```

Or on Windows:

```bat
build_release.bat
```

The build step creates:

- `dist/fh6-trader-bot/`
- `dist/fh6-trader-bot-release.zip`

## Build Standalone Windows Package

If `PyInstaller` is available locally, build a standalone package with:

```bat
build_standalone.bat
```

The standalone build is written to:

- `dist/standalone/fh6-trader-bot.exe`

## Logging

- runtime log: `logs/session.log`
- debug screenshots: `debug_frames/`

## Repository Scope

This repository contains the source code, runtime reference assets required for screen detection, and release build files required to package and run the bot.

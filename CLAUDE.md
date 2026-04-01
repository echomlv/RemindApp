# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

- **Python**: 3.12.12 via pyenv (`.python-version` pins this). The system Python (3.9.6 from Xcode CLT) must not be used for builds — py2app fails with CLT Python due to framework permission errors.
- **Runtime**: macOS 13.7.4, no Xcode installed (only Xcode Command Line Tools).
- **Dependencies**: `pip3 install rumps pyobjc-framework-Cocoa` for development; `pip3 install py2app` additionally for packaging.

## Common Commands

```bash
# Run in development (no packaging)
python3 main.py

# Build .app bundle
make app          # generates icon → cleans → py2app

# Build .dmg installer (includes .app step)
make dmg

# Regenerate icon only
python3 create_icon.py

# Clean build artifacts
make clean
```

There are no tests or linter configurations in this project.

## Architecture

This is a macOS menu-bar-only app (no Dock icon). The entry point is `main.py`; `RemindApp` extends `rumps.App`. The Dock icon is hidden by calling `NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)` inside the overridden `run()` method — it cannot be done in `__init__` because `NSApplication.sharedApplication()` is not yet initialized there.

**Module responsibilities:**

| File | Role |
|------|------|
| `main.py` | `RemindApp(rumps.App)` — entire menu tree, all callbacks, wires everything together |
| `config.py` | Singleton `Config` reading/writing `~/Library/Application Support/RemindApp/settings.json` |
| `reminder.py` | `ReminderManager` — `threading.Timer` based countdown; fires on a background thread |
| `overlay.py` | Full-screen `NSWindow` overlay via pyobjc; always shown in dark mode (`NSAppearanceNameDarkAqua`) |
| `notifier.py` | `send_banner` (osascript), `play_sound` (afplay), `speak_text` (say command) |
| `templates.py` | Static list of 7 built-in reminder message templates |
| `create_icon.py` | Generates `RemindApp.icns` using AppKit drawing — run before packaging |
| `setup.py` | py2app config referencing `RemindApp.icns` |

**Threading model:** `ReminderManager` fires its callback on a background thread. Any UI update from that callback (e.g. updating menu item state) must be dispatched to the main thread via `AppKitDispatch.run_on_main()` or `NSOperationQueue.mainQueue().addOperationWithBlock_()`. `show_overlay_from_thread()` in `overlay.py` handles this for overlay display.

**PyObjC notes:**
- Subclasses of Objective-C classes must call parent methods using `ClassName.method_(self, args)` rather than `super().method_(args)` to avoid `ObjCSuperWarning`.
- `objc.super(ClassName, self).init()` is the correct pattern for `__init__`-equivalent Obj-C initialisers.
- Module-level variables (`_current_window`, `_current_handler` in `overlay.py`) are required to prevent garbage collection of live AppKit objects.

## Key Config Keys

All persisted via `Config.get()`/`Config.set()`:
`interval_minutes`, `recurring`, `enabled`, `notification_type` (`"banner"` | `"overlay"`), `sound_enabled`, `sound_name`, `use_random_template`, `selected_template_key`, `custom_message`, `tts_enabled`, `tts_voice`.

## Packaging Notes

- py2app must be run with pyenv Python 3.12.12, not system Python.
- `setup.py` sets `"strip": False` to avoid permission errors on read-only `.so` files copied from pyenv.
- The `RemindApp.icns` file must exist before running `python3 setup.py py2app`; `make app` handles this automatically via the `icon` target.
- `LSUIElement: True` in the py2app plist (in `setup.py`) also suppresses the Dock icon in the packaged `.app`, complementing the runtime `setActivationPolicy_` call.

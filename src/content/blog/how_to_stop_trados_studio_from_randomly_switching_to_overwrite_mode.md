---
title: How to stop Trados Studio from randomly switching to overwrite mode
description: The Insert/Overwrite mode toggle has been annoying Trados Studio users
  for over a decade. Here's how to disable the Insert key and stop it from happening.
pubDate: '2026-04-09'
---

If you've used Trados Studio for any length of time, you've almost certainly experienced this: you're happily typing away in the editor, and suddenly your new text starts overwriting existing characters instead of being inserted. You look down at the status bar and see "OVR" staring back at you.

This is the Insert/Overwrite mode toggle – and it has been driving translators mad for well over a decade. Forum threads about it go back to Studio 2009, and it's still catching people out in 2026. The usual advice is "just press the Insert key to toggle it back", but that's cold comfort when you don't know how it got triggered in the first place, and doubly unhelpful if you're on a laptop that doesn't have a dedicated Insert key.

## Why does it happen?

The Insert key on a standard keyboard is a toggle: press it once and you switch to overwrite mode, press it again and you're back to insert mode. The problem is that the Insert key sits right next to the Delete, Home and End keys – all keys that translators use constantly when editing segments. It's very easy to clip the Insert key by accident without realising it.

On laptops, the situation is even more confusing. Many laptop keyboards combine Insert with another key (often Delete or F12) via the Fn key, and it's easy to trigger it unintentionally. On my Dell Precision 7740, for instance, Insert is hidden under Fn+F12 – not exactly intuitive.

Trados Studio itself has no setting to disable overwrite mode. The toggle is handled at the OS level, and Studio simply respects whatever mode is currently active. So the fix has to happen outside Studio.

## Immediate fix: restart Trados Studio

If you're stuck in overwrite mode right now and just want it to stop, the quickest fix is simply to restart Trados Studio. The overwrite mode state doesn't persist across restarts, so a fresh launch will put you back in insert mode. It's not elegant, but it works.

## If your Insert key doesn't work

Some translators (myself included) have previously disabled the Insert key using registry hacks or remapping tools, only to find themselves trapped in overwrite mode with no way to toggle it back. If that's you, there are two options.

### Use the on-screen keyboard

Press Win+R, type `osk` and press Enter. The Windows On-Screen Keyboard has an Insert key in the top-right area. Click it with Trados Studio focused. The on-screen keyboard generates virtual keypresses that bypass most key remaps, so it should work even if your physical Insert key is disabled.

### Send a virtual keypress via AutoHotkey

If you have [AutoHotkey](https://www.autohotkey.com/) installed, you can create a tiny script to send a virtual Insert keypress:

```ahk
SendInput "{Insert}"
ExitApp
```

Save this as a `.ahk` file and run it with Trados Studio in the foreground. This sends a software-level Insert keypress that bypasses registry-level scancode remaps.

## The permanent fix: disable the Insert key

Once you're out of overwrite mode, the real question is how to stop it from ever happening again. The answer is to disable the Insert key at the operating system level. Here are three ways to do it.

### Option 1: AutoHotkey (recommended for power users)

If you already use [AutoHotkey](https://www.autohotkey.com/), this is the easiest approach. Add one line to your existing script:

**AutoHotkey v2:**

```ahk
Insert::Return
```

**AutoHotkey v1:**

```ahk
Insert::return
```

This swallows the Insert key press so it never reaches any application. Save and reload your script, and overwrite mode will never bother you again. This is my preferred method – it's transparent, instantly reversible, and you can still send a virtual Insert keypress from a script if you ever need to (since AHK intercepts at a different level than `SendInput`).

### Option 2: Microsoft PowerToys (recommended for most users)

[PowerToys](https://learn.microsoft.com/en-us/windows/powertoys/) is a free set of utilities from Microsoft. Its Keyboard Manager module lets you remap or disable any key through a simple GUI – no scripting needed.

1. Install PowerToys from the Microsoft Store or from GitHub.
2. Open PowerToys and go to **Keyboard Manager** in the sidebar.
3. Make sure **Enable Keyboard Manager** is toggled on.
4. Click **Remap a key**.
5. Click the **+** button to add a new mapping.
6. In the **Select** column, choose **Insert**.
7. In the **To send** column, choose **Disable** (or leave it empty/undefined).
8. Click **OK** to save.

The Insert key is now dead for as long as PowerToys is running. PowerToys starts with Windows by default, so this is effectively permanent.

### Option 3: SharpKeys (registry-level remap)

[SharpKeys](https://github.com/randyrants/sharpkeys) is a free tool that writes a scancode remap directly to the Windows registry. Unlike AutoHotkey and PowerToys, it doesn't need to be running in the background – the remap persists at the driver level after a reboot.

1. Download and install SharpKeys.
2. Click **Add**.
3. In the left column ("Map this key"), select **Special: Insert**.
4. In the right column ("To this key"), select **Turn Key Off**.
5. Click **OK**, then **Write to Registry**.
6. Restart your computer.

The Insert key is now permanently disabled until you remove the mapping in SharpKeys.

**A word of caution with SharpKeys:** because it operates at the registry level, it can be hard to troubleshoot later. I once disabled my Insert key this way, forgot about it, and then couldn't figure out why Fn+F12 on my laptop did nothing when I needed to toggle overwrite mode back. If you go this route, make a note somewhere that you've done it.

## Which method should I use?

For most translators, **PowerToys** is the best balance of simplicity and flexibility. It's an official Microsoft tool, it has a friendly interface, and you can undo the change in seconds.

If you already use **AutoHotkey**, the one-liner is the obvious choice – and it's the most transparent option since you can see exactly what it does in your script.

**SharpKeys** works well as a set-and-forget solution, but bear in mind that you might forget you've done it and confuse yourself later (speaking from experience).

Whichever method you choose, you can finally stop worrying about your text being eaten by overwrite mode mid-segment. One less thing to break your flow.

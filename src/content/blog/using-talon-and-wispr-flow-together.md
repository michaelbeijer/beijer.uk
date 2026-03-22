---
title: Using Talon Voice and Wispr Flow at the same time
description: How to use Talon voice commands alongside Wispr Flow dictation without
  them fighting over your microphone.
pubDate: '2026-03-22'
---

<p>If you use <a href="https://talonvoice.com/">Talon Voice</a> for hands-free computer control, you may have wondered whether you can dictate text with another tool at the same time. The answer is yes — with a small trick.</p>
<h2>The problem</h2>
<p>Talon listens to everything you say. Even in command mode (where it only responds to defined commands, not free dictation), it still has the microphone open and will occasionally misinterpret your speech as a command. If you're dictating a translation with <a href="https://www.wispr.com/">Wispr Flow</a> and you say something that happens to sound like a Talon command, things get messy fast.</p>
<p>What we need is a way to put Talon to sleep whenever Wispr Flow is active, and wake it up again when we're done dictating.</p>
<h2>The solution</h2>
<p>Wispr Flow uses a push-to-talk model: you hold down a key combination to dictate, and it stops listening when you let go. In my case, that's <code>Ctrl+Win</code>. The idea is simple — while that key combo is held down, Talon sleeps. When you release it, Talon wakes back up.</p>
<p>Talon's <code>.talon</code> key bindings don't reliably capture modifier-only key combos, so we use a small Python script that polls the key state directly via the Windows API.</p>
<p>Create a file called <code>wispr_flow_ptt.py</code> in your Talon user folder (e.g. <code>%APPDATA%\Talon\user\</code>) with the following content:</p>
<p><img alt="The script file in my Talon user folder" src="/blog-images/talon-user-folder.png"></p>
<pre><code class="language-python">"""Sleep Talon while Ctrl+Win is held (Wispr Flow PTT)."""

from talon import cron, actions
import ctypes

user32 = ctypes.windll.user32
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_CONTROL = 0x11

is_held = False

def poll():
    global is_held
    ctrl = user32.GetAsyncKeyState(VK_CONTROL) &amp; 0x8000
    win = (user32.GetAsyncKeyState(VK_LWIN) &amp; 0x8000) or (user32.GetAsyncKeyState(VK_RWIN) &amp; 0x8000)
    both_down = bool(ctrl and win)

    if both_down and not is_held:
        is_held = True
        actions.speech.disable()
    elif not both_down and is_held:
        is_held = False
        actions.speech.enable()

cron.interval("50ms", poll)
</code></pre>
<p>That's it. No other changes needed.</p>
<h2>How it works</h2>
<p>The script checks 20 times per second whether <code>Ctrl</code> and <code>Win</code> are being held down. When they are, it calls <code>speech.disable()</code> to put Talon to sleep. When you let go, it calls <code>speech.enable()</code> to wake Talon back up. The CPU overhead is negligible.</p>
<h2>A few notes</h2>
<ul>
<li><strong>Windows only.</strong> The script uses <code>ctypes.windll</code>, which is a Windows API. Mac and Linux users would need a different approach.</li>
<li><strong>Adjust the key combo if needed.</strong> If your Wispr Flow PTT is set to something other than <code>Ctrl+Win</code>, you'll need to change the <a href="https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes">virtual key codes</a> in the script.</li>
<li><strong>Talon commands still work</strong> the moment you release the key. There's no noticeable delay — 50ms is imperceptible.</li>
</ul>
<p><img alt="Wispr Flow hotkey settings showing Ctrl+Win as push-to-talk" src="/blog-images/wispr-flow-hotkeys.png"></p>
<h2>Update: single-key push-to-talk with AutoHotkey</h2>
<p>After using <code>Ctrl+Win</code> for a couple of hours, I noticed it was already causing RSI in my left hand — holding down two modifier keys repeatedly is not great ergonomically. I wanted to go back to using a single key: the media next key in the top right of my keyboard, which I can press comfortably with my right hand.</p>
<p>The problem is that Wispr Flow won't accept a single key as a push-to-talk shortcut. It insists: "Shortcut must include a modifier key or a valid mouse button."</p>
<p>The workaround is a tiny <a href="https://www.autohotkey.com/">AutoHotkey</a> v2 script that remaps the media next key to send <code>Ctrl+Win</code>:</p>
<pre><code class="language-ahk">#Requires AutoHotkey v2.0
*Media_Next::Send "{LWin down}{LCtrl down}"
*Media_Next up::Send "{LWin up}{LCtrl up}"
</code></pre>
<p>A bit convoluted, but now pressing (and holding) a single key with my right hand triggers Wispr Flow dictation while simultaneously putting Talon to sleep – and when I let go, Talon wakes up again, and Wispr Flow stops listening.</p>
<h2>Why not just use Talon's built-in dictation?</h2>
<p>Talon does have a dictation mode, but dedicated dictation tools like Wispr Flow tend to be better at producing natural prose. Wispr Flow uses a large language model to clean up your speech in real time, which makes it particularly good for longer stretches of text. For translation work — where you're dictating in one language while your interface is in another — having a specialised dictation tool is a real advantage.</p>
<p>Using both tools together gives you the best of both worlds: Talon for precise, hands-free computer control, and Wispr Flow for fluid dictation.</p>
<h2>References</h2>
<ul>
<li><a href="https://talonvoice.com/">Talon Voice</a> — hands-free computer control via voice commands</li>
<li><a href="https://www.wispr.com/">Wispr Flow</a> — AI-powered dictation tool</li>
</ul>

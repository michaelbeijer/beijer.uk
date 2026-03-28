---
title: "Trados Studio 2024: how to fix the fuzzy match diff highlighting glitch in the Translation Results pane"
description: "If coloured diff highlighting in Trados Studio 2024's Translation Results pane has stopped working or is garbling text, here's the reliable fix – delete two settings folders and restore your user profile."
pubDate: 2026-03-28
---

If you use Trados Studio 2024 and have noticed that the coloured diff highlighting in the Translation Results pane has stopped working for fuzzy matches – or worse, that text from the TM source and your active segment is being garbled and concatenated together (think "ThisThe decision" instead of showing the two versions cleanly) – you're not alone. This is a recurring bug that has been reported by multiple users on the RWS Community forum, and it has a reliable fix.

Here's what the Translation Results pane looks like when it's working correctly – additions are shown in green, deletions in red with strikethrough:

![Trados Studio Translation Results pane with correct fuzzy match diff highlighting – additions in green, deletions in red strikethrough](/blog-images/trados-fuzzy-match-diff-highlighting-working.png)

## What the bug looks like

When the bug is active, all of that diff highlighting disappears. The Translation Results pane either:

- Shows no coloured highlighting at all – the differences between the TM match and your active segment are simply not marked, or
- Concatenates/overlays the TM source text with your current segment text, producing garbled output where the old and new text run together (think "ThisThe decision" instead of showing the two versions cleanly)

The underlying TM data is fine – if you double-click a match to open the Edit Translation Unit dialog, the correct text is shown. It's purely a rendering glitch in the preview pane.

This has been discussed on the RWS Community forum in a thread titled ["Differences in fuzzy matches not displayed correctly in Trados Studio 2024"](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/studio/57904/differences-in-fuzzy-matches-not-displayed-correctly-in-trados-studio-2024), where multiple users reported the same problem. The fix that worked for them, and that I can now confirm also works for me, involves deleting Trados Studio's settings folders and restoring your user profile.

## The fix

**Important:** Before you start, make sure you have a backup of your `.sdlprofile` file. If you don't know where it is, you can export it first via **File > Setup > Manage User Profiles**.

**Step 1 – Close Trados Studio completely.**

**Step 2 – Delete these two folders:**

```
C:\Users\<yourusername>\AppData\Roaming\Trados\Trados Studio\Studio18
C:\Users\<yourusername>\AppData\Roaming\Trados\Trados Studio\18
```

You can get there quickly by pressing `Win + R` and typing `%appdata%\Trados\Trados Studio\` – the two folders will be visible right there.

**Step 3 – Start Trados Studio.**

It will prompt you to select a user profile. Choose the default profile for now and let it finish loading. The diff highlighting should be working again at this point.

**Step 4 – Restore your user profile.**

Go to **File > Setup > Manage User Profiles > Change user profile**, then:

- Select either of the two profile options depending on your needs
- Click **Next**
- Browse to your backed-up `.sdlprofile` file

Your plugins and customisations will be restored.

## You may need to reinstall some plugins

Trados Studio stores plugins in three locations, and only one of them is affected by this fix:

- **`%AppData%\Trados\Trados Studio\18\Plugins\`** – this folder sits inside the `18\` directory you just deleted, so any plugins installed here **will need to be reinstalled**. (The `Unpacked\` subfolder regenerates automatically from the packages, so you only need to worry about the `.sdlplugin` files in the `Plugins\Packages\` folder.)
- **`%LocalAppData%\Trados\Trados Studio\18\Plugins\`** – not affected. Plugins installed here (including Supervertaler for Trados) will still be there.
- **`%ProgramData%\Trados\Trados Studio\18\Plugins\`** – not affected. System-wide plugins installed here will still be there.

If a plugin you rely on has disappeared after the fix, check which location it was originally installed to – if it was the Roaming folder, you'll need to reinstall it from the `.sdlplugin` file or the RWS AppStore.

## A word of warning

This fix works, but it's not permanent – at least not for me. The bug has come back on multiple occasions, which suggests it's a deeper issue with how Trados Studio manages its settings state rather than a simple one-off corruption. Each time it has reappeared, the same steps above have resolved it. I now keep my `.sdlprofile` backup in a known location and the fix takes about two minutes once you know the drill.

Hopefully RWS will address the root cause properly in a future cumulative update. In the meantime, if this post saves you the head-scratching, job done.

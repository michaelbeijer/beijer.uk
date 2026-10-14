---
title: "Can a local AI model translate a patent?"
description: "I translated a published Dutch patent in memoQ with Gemma 4 31B, a model you can run on your own computer, and with Claude Opus 5.5, and compared both with the official English."
pubDate: 2026-10-14
---

The appeal of a local AI model is obvious: the document never leaves your computer. So I tested one properly, on a real patent, and wrote it up on the Supervertaler website.

I used a published Belgian patent (BE1029761B1, a roller brake tester) that WIPO also published in English, as WO2023042137A1. That gave me a real filing translation of exactly this text, with both versions public, so it was safe to try anything on it.

I pre-translated it twice in memoQ, using Supervertaler for memoQ, with the same settings both times: once with **Gemma 4 31B**, about the largest model a well-equipped PC can run, and once with **Claude Opus 5.5**. (I ran Gemma through Ollama's cloud service to save time; it's the same model you can download.) Then I compared both with the published English, paragraph by paragraph and claim by claim.

[![The comparison spreadsheet for claims 1 to 6, with columns for the Dutch source, the published English, Gemma 4 31B, notes on Gemma, and Claude Opus 5.5. Gemma's cells are mostly red and amber; Claude's are plain or pale blue.](/blog-images/patent-test-spreadsheet-claims.jpg)](/blog-images/patent-test-spreadsheet-claims.jpg)

*Claims 1 to 6 in the comparison spreadsheet. Red: a problem that breaks the claims. Amber: meaning or consistency. Pale yellow: minor. Blue: a comment from the model on the Dutch source. Click to enlarge.*

What I found:

- **Gemma writes fluent, mostly accurate patent English**, but its terminology drifts. The same *inrichting* became "apparatus" in claims 1–4 and "device" in claims 5–9, and in a patent that breaks the claims.
- **Claude kept one name for every part from start to finish**, and pointed out a missing antecedent in claim 4 of the Dutch original.
- **House rules make a real difference.** I added six Dutch patent conventions that Gemma kept getting wrong to my SuperMemory notes, one line each, and it applied all six on the next run.
- **Smaller models (7–8B) weren't good enough for patent work at all.**

So for now, a local model gives you a draft that needs a thorough post-edit. For work that has to be right, I use a strong cloud model under business terms – how I handle that is on my [confidentiality page](/confidentiality).

The full write-up, with every paragraph side by side and the comparison spreadsheet: [Can a local AI model translate a patent?](https://supervertaler.com/articles/local-ai-patent-test/)

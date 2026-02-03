---
title: "Introducing Supervertaler: My New Multicontextual AI Translation Tool"
description: "Why I built Supervertaler, what makes it different (document awareness, visual context, TM integration), and how to get started."
pubDate: 2025-10-08
---

Supervertaler is available on GitHub: https://github.com/michaelbeijer/Supervertaler

After months of experimenting with various AI models for translation work, I finally decided to build something that addresses a major frustration I’ve been having: most AI translation tools treat each sentence in isolation, completely ignoring the broader context of the document.

That’s why I created **Supervertaler** — a Python-based translation and proofreading tool that actually understands context the way we translators do.

### What makes Supervertaler different?

The key innovation is that Supervertaler doesn’t just throw individual sentences at an AI and hope for the best. Instead, it feeds the AI multiple layers of context:

- **Full document awareness**: the AI sees the entire document when translating each sentence, not just isolated segments.
- **Visual context**: when your text references “Fig 1A”, Supervertaler can show that image to the AI (if you provide an images folder).
- **Translation memory integration**: it checks your TM for exact matches before sending anything to the AI — saving API costs and maintaining consistency.
- **Tracked changes from memoQ**: you can import previous editing decisions from bilingual DOCX files as additional context.
- **Custom instructions**: add project-specific instructions without needing to modify code.

### Two modes: Translate and Proofread

Supervertaler has two distinct modes:

- **TRANSLATE**: translates source text while leveraging your TM for exact matches.
- **PROOFREAD**: reviews and revises existing translations against the source — useful for post-editing work or quality checks.

The input/output format is simple tab-delimited text, which makes it easy to integrate with other tools in your workflow. In proofread mode, you also get comments explaining what the AI changed and why.

### Multiple AI providers supported

Rather than locking you into one AI provider, Supervertaler supports models via APIs from:

- Anthropic (Claude)
- Google (Gemini)
- OpenAI (ChatGPT)

This makes it possible to switch between models depending on your language pair, budget, or quality preferences.

### Why I built this

As translators, we know that context is everything. A term that’s perfect in one paragraph might be completely wrong three pages later. Traditional CAT tools segment our texts and while that’s great for leveraging TMs, it often means AI assistants miss crucial context.

Supervertaler bridges that gap.

The tool automatically chunks large documents into manageable pieces that fit within AI context windows — but each chunk still has awareness of the full document context.

![Supervertaler screenshot (v2.3.0)](https://michaelbeijer.co.uk/w/images/thumb/b/b1/supervertaler_screenshot_v2.3.0.jpg/709px-supervertaler_screenshot_v2.3.0.jpg)

### Get started

Supervertaler is open source and available on GitHub. You’ll need Python and API keys for whichever AI provider(s) you want to use.

If you’re tired of AI translations that miss obvious context clues, give Supervertaler a try. And feel free to reach out at info@michaelbeijer.co.uk with questions or suggestions.

Note: I also published this article on LinkedIn: https://www.linkedin.com/pulse/introducing-supervertaler-my-new-multicontextual-ai-tool-beijer-i3npe

---

Source: https://michaelbeijer.co.uk/introducing_supervertaler

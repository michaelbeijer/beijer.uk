---
title: "Trados termbase woes (finally being fixed?)"
description: "Trados Studio's termbase system has been unreliable for years due to fragile MultiTerm interop and the old JET/Access database engine. RWS finally decoupled terminology handling in Studio 2024 SR1 – but has it actually fixed things?"
pubDate: 2026-03-14
---

Termbases not working reliably in Trados Studio is a long-standing issue. The underlying technology – MultiTerm communicating with Studio via inter-process calls, on top of the old Microsoft JET/Access database engine – has been fragile for years, and it shows up as:

- term recognition that randomly stops working mid-session
- termbases that won't accept new entries ("MultiTerm is unable to add the entry")
- general instability over long sessions, requiring termbase reorganisation or even project recreation

The [community forum history](https://community.rws.com/search?q=term%20recognition) is extensive (see below), and it's hard not to see this as a persistent "tax" on translators' time. As one long-suffering user [put it](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/studio/51825/term-recognition-does-not-work-in-certain-termbases-after-latest-update/): "This has been my experience when working with Trados for the past 10 years or so – term recognition simply stopping working, terms not being shown, completely unreliable F8 check."

### The root cause

The fundamental problem was architectural. Studio didn't handle terminology directly – it delegated everything to MultiTerm running in the background. That behind-the-scenes communication channel was brittle, and once it broke during a session, term recognition would silently fail. The underlying JET/Access database engine only made things worse, adding its own layer of instability.

### The promised fix: Studio 2024 SR1

In mid-2025, Daniel Brockmann (Principal Product Manager for Trados Studio) [acknowledged the problem publicly](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/multiterm/55704/unable-to-add-a-new-term-to-termbase-multiterm---error-message) on the RWS Community, responding directly to complaints about termbase reliability:

> "You are right that this has been a challenge for us for many years (no beating around the bush here). The potentially interesting news is that for the upcoming Studio 2024 SR1 release, we have done some very deep changes in our code to bring all of the terminology logic into the Studio code base itself (most of it was living in the MultiTerm code base, and communication behind the scenes between Studio and MultiTerm could become fragile). As one example, this has helped us address term recognition problems where it might not work reliably anymore after a certain time of working. This should hopefully be a thing of the past now."

Studio 2024 SR1 was released in the second half of 2025 and the [official release notes](https://docs.rws.com/en-US/trados-studio-2024-sr1-1187677/changes-for-trados-studio-2024-sr1-1230624) describe the change as a "MultiTerm decoupling" – Studio now functions independently from MultiTerm for terminology handling. The [SR1 blog post](https://www.trados.com/blog/whats-new-in-trados-studio-2024-sr1/) adds that terminology management has been "modernized, with all processing now happening entirely within Studio", and that "term recognition and search now pull results from all loaded termbases more reliably".

### Has it actually worked?

The architectural change is real and substantial – they genuinely ripped out the old MultiTerm interop layer and brought terminology into Studio's own codebase. On the developer side, the legacy `Sdl.MultiTerm.TMO.Interop.dll` has been [removed entirely](https://developers.rws.com/studio-api-docs/articles/hints_tips/Update_Plugins/how_to_update_plugins_to_trados_studio_2024_sr1.html) from the Studio installation folder.

But has it fixed the day-to-day experience? The jury is still out. As recently as October 2025, users who had upgraded to SR1 were [still reporting](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/studio/59250/term-recognition-still-not-working) that term recognition only worked for very short terms, with the problem persisting across different projects and file types. And the [developer forums](https://community.rws.com/developers-more/trados-portfolio/trados-studio-developers/f/sdk_qa/58913/sdl-multiterm-tmo-interop-trados-studio-2024-sr1) show that the decoupling introduced new bugs for third-party terminology providers.

Brockmann himself was honest about this, noting that they were "still stabilising this area after making these very extensive changes". So the right foundations may now be in place – but I'll believe it when I see reliable term recognition in my own daily work. The translators who depend on Trados deserve better than "hopefully a thing of the past".

This is actually one of the reasons I built [Supervertaler for Trados](https://supervertaler.com/trados/) – a Studio plugin that sidesteps MultiTerm entirely and uses its own SQLite-powered terminology system for lookups directly in the editor. It also includes an AI chat assistant and a batch translator. If you're tired of fighting with term recognition, it might be worth a look.

### References and links

- [Trados 2022 term recognition is not working with selected term bases](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/multiterm/56115/trados-2022-term-recogntion-is-not-working-with-selected-term-bases) (Philippe Galinier)
- [Term recognition problem](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/studio/53463/term-recognition-problem) (Margus Enno)
- [Term recognition problem](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/studio/41381/term-recognition-problem) (Anthony Rudd)
- [Term recognition doesn't work](https://community.rws.com/product-groups/trados-portfolio/f/licensing/54610/term-recognition-doesn-t-work/) (Therese Rose)
- [TB not showing Terms on Term Recognition](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/multiterm/55997/tb-not-showing-terms-on-term-recognition/) (Jenifer Araújo)
- [Term recognition in Studio](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/multiterm/53829/term-recognition-in-studio/) (Alan Patrick Hynds Carr)
- [Term recognition problem: only the terms recognized in the first (default) termbase are shown in full](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/multiterm/9401/term-recognition-problem-only-the-terms-recognized-in-the-first-default-termbase-are-shown-in-full/) (Yejun Huang)
- [Unable to add a new term to termbase/Multiterm – error message](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/multiterm/55704/unable-to-add-a-new-term-to-termbase-multiterm---error-message/) (Ines de Azcarate)
- [Term search not working in Multiterm term base](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/multiterm/52286/term-search-not-working-in-multiterm-term-base) (Stéphane Clément)
- [Issue with Term Recognition not working for Cloud Termbase](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/studio/53939/issue-with-term-recognition-not-working-for-cloud-termbase) (Hye Kang Shin)
- [Trados 2022 crashes when adding terms to term base](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/studio/53177/trados-2022-crashes-when-adding-terms-to-term-base) (Markus)
- [Termbase problem](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/multiterm/50155/term-base-problem) (dawoon jeong)
- [Words in term base not recognized](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/studio/49948/words-in-term-base-not-recognized/) (Jochen Schliesser)
- [Term Base Not Pulling Results Adequately](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/multiterm/47029/term-base-not-pulling-results-adequately) (Maryse van Caloen)
- [Term recognition does not work in certain termbases after latest update](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/studio/51825/term-recognition-does-not-work-in-certain-termbases-after-latest-update/) (Pavel Tsvetkov)
- [No Term Recognition for default termbase but for other termbases](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/studio/56728/no-term-recognition-for-default-termbase-but-for-other-termbases) (Christine Eulriet)
- [Term Recognition not working](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/multiterm/33443/term-recognition-not-working/) (Patrice Philippi)
- [Term recognition not working in Trados Studio 2022](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/multiterm/42898/term-recognition-not-working-in-trados-studio-2022/) (Charlotte Kauczor)
- [TRADOS 2021 "no results available" for more than half of the segments (though they have terms from my Term Base)](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/studio/39294/trados-2021-no-results-available-for-more-than-half-of-the-segments-though-they-have-terms-from-my-term-base) (Kathryn Arsenault)
- [Term adding not working from inside Trados Studio 2024 – 18.0.0.1013](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/studio/54662/term-adding-not-working-from-inside-trados-studio-2024---18-0-0-1013) (Pavel Tsvetkov)
- [TERM RECOGNITION STILL NOT WORKING](https://community.rws.com/product-groups/trados-portfolio/trados-studio/f/studio/59250/term-recognition-still-not-working) (post-SR1, October 2025)

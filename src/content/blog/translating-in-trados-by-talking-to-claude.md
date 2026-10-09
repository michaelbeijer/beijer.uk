---
title: "Translating in Trados Studio by talking to Claude"
description: "The new Supervertaler MCP Server connects Claude for Desktop to Trados Studio. Combine it with a good dictation tool like Wispr Flow, and translating becomes something entirely new: a spoken conversation about your project."
pubDate: 2026-07-26
hidden: true
---

For as long as I've been translating, the basic physical activity has been the same: sit at a keyboard, look at a segment, type. The tools around that activity have changed enormously – CAT tools, translation memories, termbases, machine translation, post-editing – but the fingers-on-keys part has always remained.

That has just changed for me, and I want to describe the new setup, because it's the most fun I've had with translation technology in years.

## The Supervertaler MCP Server

The [Supervertaler MCP Server](https://docs.supervertaler.com/trados/mcp-server/) connects Claude for Desktop to [Supervertaler for Trados](https://supervertaler.com/trados/), my plug-in for Trados Studio 2024/2026. Once the connection is made, Claude has full access to my open Trados project: the segments in the grid, my termbases, my translation memories, and even Trados Studio comments. It can read them – and it can change them.

MCP (Model Context Protocol) is the open standard that makes this possible: it's the plumbing that lets an AI assistant like Claude talk to other software on your computer. In this case, that other software is Trados Studio. And because it's an open standard, Claude for Desktop is only one possible client: the same server lets me chat with my Trados project from Claude Code in VS Code or in a terminal – wherever I happen to be working.

There are no commands to memorise – you just ask, in plain language. If you're ever unsure what's possible, you can literally ask Claude "What can I do?":

![Asking Claude what you can do with the Supervertaler MCP Server](/blog-images/supervertaler-mcp-what-can-i-do.png)

## Standing on Trados Studio's shoulders

It's worth pausing on how this is even possible, because it says something about Trados Studio that I think often goes unappreciated: Studio has a genuinely deep extensibility story. It isn't just a CAT tool; it's a platform, with a .NET plug-in framework and a set of public APIs that give third-party developers access to almost everything Studio itself can do.

Supervertaler for Trados is built on those APIs:

- The **Integration API** lets a plug-in add its own views, panels and ribbon actions, and gives access to the editor – the active document, the active segment, navigation, and so on.
- The **Bilingual File API** exposes the actual content of the files: segment pairs, source and target text, confirmation statuses, and even Trados Studio comments.
- The **Project Automation API** lets a plug-in run Studio's own batch tasks programmatically – analyse files, pre-translate, update main translation memories, verify, generate target translations.
- The **Translation Memory API** allows searching and updating TMs, and the **terminology provider API** does the same for termbases.
- And when it's all built, the **RWS AppStore** gives you a distribution channel straight into your users' copies of Studio.

The Supervertaler MCP Server is, in a sense, a thin translation layer on top of all this: a small program that Claude for Desktop talks to, which forwards each request to the plug-in running inside Trados Studio. Every tool Claude can use – "get me the segments", "search the TM", "update this target", "add a comment" – maps down to those same public Trados APIs. The reason I could expose around fifty different operations to an AI assistant is simply that Studio's API surface is rich enough to support them. If RWS hadn't invested in that developer platform over the years, none of this would exist.

## An app store before app stores were cool

The [RWS AppStore](https://appstore.rws.com/) deserves its own paragraph in this story. It launched back in 2010 as the SDL OpenExchange, alongside Trados Studio 2009, was later renamed the SDL AppStore, and is now the RWS AppStore – but the idea has been the same throughout: open up the product's APIs, let third-party developers build plug-ins, and give them a central marketplace to distribute through.

Sixteen years on, no other major commercial CAT tool has anything comparable. The only ecosystem I can think of that comes close is [OmegaT](https://omegat.org/), the open-source CAT tool, which has a healthy collection of community-built plugins – the Okapi filters, various machine-translation connectors, and more. But that's a community effort around an open-source project, scattered across wikis and repositories; there's no store, no curation, no one-click install into a commercial product used by hundreds of thousands of translators. What SDL built in 2010 was genuinely ahead of its time.

And here's the thing: the AI world is now busy reinventing exactly this idea. ChatGPT has its plug-ins and GPT store; Claude has its connector directory, skills, and the whole MCP ecosystem. The pattern is identical – a platform opens itself up, third parties extend it, and a marketplace connects the two. The RWS AppStore is what allowed a freelance translator like me to build Supervertaler for Trados and put it in front of Trados users worldwide, and [Supervertaler is distributed through it](https://appstore.rws.com/plugin/432) today. In the near future, I'm hoping to complete the circle: I'm working on getting the Supervertaler MCP Server listed in Claude's public directory of MCP connectors, so that it's available to everyone there too – one plug-in, listed in both generations of app store.

## The workflow

After implementing the server, I started using it on real translation jobs. The workflow goes like this:

1. I open a project in Trados Studio 2026.
2. I open a fresh chat in Claude for Desktop and give it a prompt along these lines:

> I'm translating a project from English into Dutch, and I have it open in Trados Studio 2026. Please analyse the project.
>
> As you'll see, a large portion of it is already 100% and CM (context) matches – i.e. confirmed. As a rule, we can ignore any confirmed segment. Your job is to translate the rest and make sure it's consistent with the whole document.
>
> It's also your job to make sure the whole document is consistent and correct. If you find things in already-confirmed segments that aren't correct, you can fix them.
>
> If you find a segment that isn't confirmed, isn't set to translated, and has a high fuzzy match (say 93–95%), you can use it as a reference – but make sure to insert a 100% correct translation. Don't just copy high matches or use them without thinking.
>
> Please also consult all the client's notes and references in this folder: D:\Example\refs
>
> You can also look at the source document as a PDF for reference if you need it: D:\Example\Example source document.pdf

3. I then translate the project interactively in Studio, just by chatting with Claude.

## Add dictation, and everything changes

Here's the part that turns this from a clever integration into a genuinely new way of working: I don't type any of this. I use [Wispr Flow](https://www.wispr.com/) for all the communication with Claude.

I keep the Claude chat window open on one monitor, with Trados Studio on my main monitor. As I talk, I can watch things update in real time in my Trados project – segments filling in, statuses changing, comments appearing – without me touching the keyboard or mouse at all.

The effect is hard to describe until you've tried it. Translating stops being typing and becomes a conversation *about* the document:

- "Have a look at segments 40 to 60 – the client's reference PDF uses a different term for that component; check which one and make it consistent throughout."
- "That fuzzy match in the active segment is close, but the date format is wrong – fix it and confirm."
- "Search the TM for how we translated this phrase last time, and use that."

Any decent dictation tool would work, but a fast, accurate one like Wispr Flow matters here, because the whole point is that speaking becomes the primary interface. If dictation is slow or clumsy, you fall back to the keyboard and the spell is broken. When it's fast, you genuinely lean back and direct the work.

## QA on a whole new level

A small real example: I asked Claude to go through the open project and give me a working glossary I could use while translating. It read the whole job, checked my termbase, and produced this – noting where a rendering was already confirmed in my own termbase:

![Claude building an English–Dutch glossary from the open Trados project](/blog-images/supervertaler-mcp-glossary.png)

Not only does Claude answer questions about the project perfectly, but because it has access to the whole job, it spots things there is no way I would have spotted unless I had spent an inordinate amount of time combing through the entire project: an inconsistent term used in segment 12 and segment 847, a number that doesn't match the source, a confirmed 100% match that is actually wrong in this context.

Traditional QA in CAT tools is mechanical: pattern matching, number checks, forbidden-term lists. Useful, but blunt. An AI with contextual knowledge of the whole file can hold the entire document in its head and suggest changes across giant projects – the kind of consistency checking that previously only happened if you had the time (and the caffeine) to re-read everything.

And crucially, you remain in charge. Claude proposes, explains and asks; you decide. It's less like handing your project to a machine and more like having an infinitely patient assistant who has actually read the whole document – and all the client's reference material.

## Improving the tool while using it

One more trick that I love. If Claude is unable to do something – some operation the MCP server doesn't support yet – I simply switch to the Claude Code tab in the Claude for Desktop app and tell Claude Code to implement it. It gets to work on the plug-in's source code, and I switch back to the translation chat tab to carry on translating.

This means I can improve the system iteratively while using it to translate a real project at the same time. The tool grows to fit the work, mid-job.

## Trados Studio 2026: better for developers too

Supervertaler for Trados supports both Studio 2024 and the new [Studio 2026](https://www.trados.com/spotlight/whats-new-studio-2026/), and having ported the plug-in to 2026, I can say the changes under the bonnet are substantial – and very welcome from a developer's point of view.

**64-bit at last.** Studio 2026 is now a fully 64-bit application. For users, that means the old 32-bit memory ceiling is gone: large files and projects open dramatically faster, and RWS reports processing enormous files that previously caused crashes. For developers, it means we're no longer building against a 32-bit process with all the legacy constraints that entailed.

**A modern termbase format.** Local termbases have moved from the legacy .sdltb format to the new **.ttb** format. This one deserves a special mention. The old .sdltb was built on a Microsoft JET database engine dating back decades, which could only be read through 32-bit drivers – supporting it in a plug-in involved some genuinely archaeological work. The new .ttb format is a clean, modern SQLite database with built-in full-text search (FTS5). For a developer, that's night and day: it's an open, well-documented format that any modern library can read, and it's fast. Studio 2026 also includes a wizard for converting existing .sdltb termbases, and handles conversion automatically when opening project packages, so the migration path is taken care of.

**API continuity.** Perhaps most importantly for anyone who builds on the platform: despite the major internal re-architecture, RWS preserved the existing public plug-in APIs. Supervertaler for Trados kept working on Studio 2026 without a forced rewrite – the same terminology provider interfaces, the same integration points. That kind of API stewardship through a big-bang release is not a given in this industry, and it's the reason the AppStore ecosystem can survive a transition like 32-bit to 64-bit intact.

## Try it yourself

If you'd like to try this workflow, grab the trial version of [Supervertaler for Trados on the RWS App Store](https://appstore.rws.com/plugin/432). The MCP Server setup is documented [here](https://docs.supervertaler.com/trados/mcp-server/).

The trial period is 14 days, but I would be more than happy to extend it as long as you need – just ask. And if you have any questions at all, get in touch at [support@supervertaler.com](mailto:support@supervertaler.com).

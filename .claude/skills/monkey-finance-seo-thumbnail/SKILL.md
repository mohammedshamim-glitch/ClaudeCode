---
name: monkey-finance-seo-thumbnail
description: >
  World-class YouTube SEO + Thumbnail skill for the Monkey Finance channel.
  Produces a complete click-optimisation package: SEO-engineered title, full video
  description, tags, hashtags, chapter timestamps, and a detailed AI image generation
  prompt for a high-CTR thumbnail — all tuned for the UK personal finance audience.
  Automatically saves the complete SEO package to Google Drive and displays it for
  immediate copy-paste use in YouTube Studio.
  Use this skill whenever Sham asks for SEO, a title, a description, tags, a thumbnail
  brief, a thumbnail prompt, "make it clickable", "optimise this for YouTube", "write
  the metadata", "generate a thumbnail prompt", or any combination of the above.
  Always use this skill before writing YouTube metadata or thumbnail directions —
  never guess, never wing it. A great video nobody clicks is a wasted video.
---

# 🎯 Monkey Finance — SEO & Thumbnail Skill

One principle above all others: **the best video in the world is worthless if nobody clicks it.**

This skill produces a complete click-optimisation package for every Monkey Finance video — engineered to win the impression, earn the click, and signal quality to the YouTube algorithm.

---

## What This Skill Produces

Every run outputs a complete **Click Package** containing:

| Output | What it is |
|---|---|
| **Title (Primary)** | SEO-engineered, CTR-optimised, under 60 chars |
| **Title (Alt A & B)** | Two A/B test variants with different emotional hooks |
| **Description** | 300–500 words, front-loaded, keyword-rich, human-first |
| **Tags** | 10–12 researched tags, broad to specific |
| **Hashtags** | 3–5 targeted hashtags for the description |
| **Chapters** | Timestamped sections for watch time and search visibility |
| **Upload timing** | Best day and time to publish for maximum launch-window impact |
| **Pinned comment** | Ready-to-post comment — paste within 60 minutes of going live |
| **Caption note** | YouTube auto-generates captions — no SRT needed. Language set to en-GB on upload. |
| **Thumbnail Brief** | Visual concept, emotional trigger, layout direction |
| **AI Image Prompt** | Ready-to-paste Grok/Midjourney prompt for the thumbnail |

---

## Reference Files — Read All Three Before Starting

| File | What it covers |
|---|---|
| `references/SEO.md` | Title engineering, description architecture, tags, hashtags, chapters |
| `references/THUMBNAIL.md` | CTR psychology, visual hierarchy, Monkey Finance design system, brief format |
| `references/PROMPTS.md` | AI image generation prompt templates and formulas for Grok |

---

## When to Run This Skill — Pipeline Position

**Run AFTER video assembly and Whisper timing generation, not before.**

This is the correct pipeline order:
1. Script → TTS → Images → Video assembly → Whisper timings
2. **Then run this skill** — using the Whisper CSV for exact chapter timestamps
3. Upload video + metadata + thumbnail together in one session

**Why this order matters:**
- Chapter timestamps must come from `audio_timings_new.csv` — not estimated from word counts
- Thumbnail is ready at upload time, not added later in Studio
- Everything ships together cleanly in a single upload session
- YouTube auto-generates en-GB captions — no SRT file needed

---

## Input

This skill works from any of:
- A completed script + `audio_timings_new.csv` (best — exact timestamps available)
- A completed script only (chapters estimated from word counts — less accurate)
- A content brief from the trend report
- A topic title + key talking points
- A topic title only (skill infers the rest — confirm angle before proceeding)

---

## Process

**Step 1 — Read all three reference files**

**Step 2 — Identify the video's core promise**
One sentence: what does the viewer get from watching this? This becomes the spine of both the title and thumbnail.

**Step 3 — Determine the emotional trigger**
Choose the dominant emotion for this video's packaging:

| Trigger | When to use | Title/thumbnail signal |
|---|---|---|
| 😨 Fear / Warning | Tax changes, rule changes, risks | "Warning", "Cost you", "Before it's too late" |
| 🤑 Aspiration | Investing, growing wealth, savings wins | "How to", number-based gains, upward visuals |
| 😮 Shock / Surprise | Counterintuitive insights, surprising stats | Bold stat, "Nobody tells you", "The truth about" |
| 🧐 Curiosity | Gap-based topics, hidden rules | "The secret", "Why most people", question format |
| 😅 Relief / Urgency | Deadlines, windows closing, easy fixes | "Before [date]", "Still time to", "Here's what to do" |

**Step 4 — Engineer the title** (see `SEO.md`)

**Step 5 — Write the description** (see `SEO.md`)

**Step 6 — Pull competitor tags with yt-dlp, then generate tags, hashtags, chapters**

Before writing the tag list, use yt-dlp to extract the exact hidden tags from the top 3–5 competitor videos on the same topic:

```
For each competitor video URL:
→ Extract: tags array, description, view count
```

Use the competitor tags to:
- Identify the terms that top-performing videos rank for
- Include the strongest ones in our tag list where relevant
- Spot gaps — tags they're not using that we should own

Then generate tags, hashtags, and chapters per `SEO.md`. Tag list should blend competitor-validated terms with channel-specific long-tails.

**Step 7 — Build the thumbnail brief and AI prompt** (see `THUMBNAIL.md` and `PROMPTS.md`)

**Step 8 — Deliver the full Click Package** 

Output the complete Click Package in clean, labelled sections. Then automatically:

1. **Save the SEO package** to Google Drive in the run's project folder as `06-seo-metadata.txt` — title variants, description, tags, hashtags, chapters, thumbnail brief, and AI thumbnail prompt.

2. **Save the thumbnail prompt alone** as `07-thumbnail-prompt.txt` — the AI image generation prompt only, nothing else. No labels, no headers, no brief. Just the raw prompt text ready to paste directly into Grok.

3. **Thumbnail naming reminder**: When Sham saves the generated thumbnail to Drive, it must be named `thumbnail` in the episode folder. `upload_youtube.py` finds it by that name and uploads it automatically alongside the video.

4. **Display the package** on-screen in copy-paste ready format for immediate use in YouTube Studio and Grok.

5. Once saved, confirm with the Drive links and ask: *"SEO package complete. `06-seo-metadata.txt` and `07-thumbnail-prompt.txt` saved to Drive. Have you saved the thumbnail to Drive as 'thumbnail'? Once ready, we can upload everything in one go."*

---

## Quality Standards

Before delivering, verify:
- [ ] Primary keyword appears in title within first 40 characters
- [ ] Title is under 60 characters
- [ ] Title passes the "would I click this?" test at a glance
- [ ] Description first 2 lines work as a standalone hook (no "Show More" required)
- [ ] Description naturally uses primary + secondary keywords without stuffing
- [ ] Tags move from broad → specific → long-tail
- [ ] **Green suit monkey is present in EVERY thumbnail prompt** — the monkey is the channel brand and must appear in every single thumbnail without exception. If the AI prompt doesn't include "green suit monkey", rewrite it before saving.
- [ ] Monkey has a specific expression AND a specific body action (never just standing) — both must be stated explicitly in the prompt
- [ ] Monkey is reacting TO the content (pointing at a stat, jaw dropped at a number, looking between two options) — not posing beside it
- [ ] Thumbnail brief and AI prompt are specific enough to produce a distinctive, clickable image
- [ ] All 3 title variants use different emotional hooks — not just word swaps
- [ ] Everything is UK-first — no American products, platforms, or terminology

---

*SEO architecture: `references/SEO.md` · Thumbnail design: `references/THUMBNAIL.md` · AI prompt formulas: `references/PROMPTS.md`*

---
name: monkey-finance-scriptwriter
description: >
  Elite scriptwriting skill for the Monkey Finance YouTube channel. Produces
  fully-written, broadcast-ready narration scripts engineered for maximum retention,
  built on storytelling psychology, dopamine loop architecture, and the Monkey Finance
  brand voice — punchy, relatable, conversational, and UK-first. Breaks content into
  exactly 25-word scenes and outputs two files: structured script with section headers
  and clean narration-only file for TTS audio generation.
  Use this skill whenever Sham asks to write a script, draft a video, create narration,
  or says anything like "write the script", "script this up", "write me a video",
  "turn this into a script", "draft the narration", "write episode X", or "write the next one".
  Also trigger automatically when a content brief or approved topic is in context and
  the next logical step is a script. Never write Monkey Finance narration without this skill.
---

# ✍️ Monkey Finance — Elite Scriptwriter

One job. One standard. **A script so good viewers forget they're watching a finance video.**

Every script produced by this skill is engineered across three dimensions simultaneously:
- **Retention psychology** — dopamine loops, curiosity gaps, value escalation
- **Storytelling craft** — narrative spine, emotional arc, character and analogy
- **Monkey Finance voice** — punchy, warm, UK-first, occasionally playful

---

## Reference Files — Read ALL THREE before writing a single word

| File | What it covers | When to read |
|---|---|---|
| `references/VOICE.md` | Brand voice, tone, UK language rules, monkey theme, analogy craft | Always — read first |
| `references/STRUCTURE.md` | Script blueprint, section jobs, word counts, pacing, value escalation | Always — read second |
| `references/RETENTION.md` | Dopamine loop architecture, curiosity gap science, hook formulas, the 4-pass writing method | Always — read third |

**Do not write until all three are loaded. The references are the craft. This file is the process.**

---

## Input Modes — Adapt to What You're Given

| Input | Action |
|---|---|
| **Full content brief** (from trend report) | Maximum quality mode. Use every element — hook angle, audience signals, SEO data, emotional trigger. No guessing needed. |
| **Competitor adaptation** (brief flags a source video) | Follow the Competitor Adaptation Workflow below — extract transcript first, then adapt. Never write from scratch when a proven source exists. |
| **Topic + bullet points** | Expand into full narrative. Identify the Grand Payoff first (the single most satisfying moment the viewer clicked to see). Confirm with Sham before writing. |
| **Topic title only** | Research the topic. Determine the best angle, audience level, and emotional hook. State your approach and get Sham's sign-off before writing. |

---

## Competitor Adaptation Workflow

Use this whenever the content brief references a specific competitor video to adapt (e.g. "adapt Wealth Logic's Leasing vs Buying video"). This workflow produces better scripts than writing from scratch because the structure and emotional beats are already proven.

**Step 1 — Find the video ID**
Use the YouTube Data API to search for the video:
```
GET https://www.googleapis.com/youtube/v3/search?part=snippet&q=QUERY&type=video
Authorization: Bearer {youtube_access_token}
```
Get the video ID from the result. If the access token is expired, refresh it using `youtube_refresh_token` from `token.json`.

**Step 2 — Extract the transcript via Gemini**
yt-dlp and youtube-transcript-api are both 403-blocked from this server. Use Gemini instead:
```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}

Body:
{
  "contents": [{
    "parts": [
      {"text": "Please provide a full word-for-word transcript of this YouTube video."},
      {"file_data": {"mime_type": "video/*", "file_uri": "https://www.youtube.com/watch?v=VIDEO_ID"}}
    ]
  }]
}
```
Gemini reads YouTube URLs natively and returns the full transcript.

**Step 3 — Save the source transcript to Drive**
Save as `00-source-transcript-[channel-name]-original.txt` in the episode folder. Prefix `00-` so it sorts to the top. Include a word count in the header.

**Step 4 — Analyse before adapting**
Read the transcript and identify:
- Hook structure (first 60 seconds) — what makes it work?
- Section breakdown and pacing
- Emotional arc and key turning points
- Analogies, examples, and characters used
- The Grand Payoff moment — what did the viewer come to see?

**Step 5 — Adapt to UK**
Keep the proven structure and emotional beats intact. Change everything UK-specific:
- Swap $ for £ and US figures for UK equivalents
- Replace US products/laws with UK equivalents (ISA, SIPP, Section 24, CGT, Section 75, stamp duty, etc.)
- Create new UK characters (never reuse Jake/Marcus — rotate pairs each episode)
- Replace US examples and analogies with UK ones
- Never copy sentences verbatim — rewrite in Monkey Finance voice

**Step 6 — Write the script**
Apply the 4-pass method as normal, using the analysed structure as your scaffold. The adaptation inherits the proven beats; the 4-pass ensures the voice, pacing, and UK context are right.

---

## Audience Calibration — Do This Before Anything Else

Assess the topic and set the level. Get it wrong and you lose the audience in the first two minutes.

| Level | Who they are | Language approach |
|---|---|---|
| **Beginner** | No investment experience, intimidated by finance | Zero jargon. Every term earns its place. Analogies for everything. Warm and reassuring. |
| **Everyday** | Aware of ISAs and pensions, not an expert | Light jargon with fast explanations. Practical and actionable. This is the default. |
| **Intermediate** | Knows the basics, wants nuance | Can assume SIPP, index fund, drawdown without defining fully. Respects their intelligence. |

**Default: Everyday.** Override only when the topic makes it obvious (e.g. "What is compound interest?" = Beginner; "Pension decumulation strategies" = Intermediate).

---

## The 4-Pass Writing Method

Never write start-to-finish in one pass. Use this method — it cuts time by 40% and produces dramatically better output.

### Pass 1 — The Artist (Idea Dump)
Brainstorm every possible angle, example, analogy, stat, and story you could use. Don't filter. The only goal: find the **Grand Payoff** — the single most satisfying moment the viewer clicked to see. If you can't name it, stop and find it before proceeding.

### Pass 2 — The Architect (Structure)
Map the script section by section using `STRUCTURE.md`. Assign your best material to the right sections. Confirm value escalates — each section more compelling than the last. Write the body first. **Write the hook last** — you can't sell a script that doesn't exist yet.

### Pass 3 — The Writer (Drafting)
Write the full narration. Follow the voice rules in `VOICE.md`. Every sentence should make the next one feel worth hearing. No filler. No padding. No "in this video we will..."

### Pass 4 — The Wizard (Retention Edit)
Read the full script aloud. Cut anything you wouldn't say in conversation. Check every section transition has a mini-hook. Verify curiosity gaps aren't closed too early. Confirm value escalates throughout. Run the final quality check below.

---

## Script Specifications

| Spec | Requirement |
|---|---|
| Length | 1,900–2,100 words (14–16 min at ~130 wpm) |
| Format | Pure narration — no visual cues, no stage directions, no timestamps |
| Tone | Storytelling-led, conversational, punchy |
| Monkey theme | Light — 1–2 moments max, never forced |
| Geography | 100% UK — products, examples, legislation, currency |
| Output format | Labelled sections, clean delivery, ready to paste into pipeline |

---

## Final Quality Check — Clear All 9 Before Delivering

- [ ] **Grand Payoff identified** — there's one unmissable moment the whole script builds toward
- [ ] **Hook written last** — and it makes you want to keep reading immediately
- [ ] **No slow open** — zero warm-up lines, zero "welcome back", starts with impact
- [ ] **Value escalates** — each section is more compelling than the one before it
- [ ] **Every section ends with a mini-hook** — the viewer is always pulled forward
- [ ] **Curiosity gaps** — at least 2 open loops planted and paid off across the script
- [ ] **UK-first** — no American terms, products, or references
- [ ] **Word count 1,900–2,100** — not under, not over
- [ ] **Scene format** — 15–25 words per scene (target ~20); numbered items (One:, Two:, Three:, Option one: etc.) always start a new scene

---

## Delivery

**Scene format — non-negotiable:**

Target 15–25 words per scene (aim for ~20). Merge short sentences with adjacent ones to stay within range. Never let a scene run over 25 words — split it.

**Numbered-item exception:** Any sentence beginning with `One:`, `Two:`, `Three:`, `Four:`, `Five:`, `Option one:`, `Option two:`, `Option three:`, `Option four:`, `Option five:` (any case) **always starts a new scene**, regardless of the current word count.

**How to apply:**
- Write the narration naturally first
- Then split into scenes: accumulate sentences until ~20 words, never exceeding 25
- Apply the numbered-item exception throughout
- Scene count will typically be 80–120 scenes for a 1,900–2,100 word script

**Important — narration scenes ≠ images:**
Narration is split at 15–25 word scenes for TTS and audio alignment accuracy. The image prompt generator (Stage 3) groups consecutive narration scenes into ~25-word visual sub-scenes independently. One narration scene does not mean one unique image — Stage 3 handles the grouping.

Then automatically:

1. **Save the structured script** to Google Drive in the run's project folder as `02-narration-script-structured.txt` — full script with a metadata header block at the top (`# Title`, `# Date`, `# Word count`, `# Scene count`), section labels ([HOOK], [THE PROBLEM], etc.), and scene numbers (1.1, 1.2, etc.). Each scene = one sentence (or merged block). Blank line between each scene.

2. **Save the clean narration file** to the same Google Drive folder as `03-narration-script-clean.txt` — spoken words only, no scene numbers, no headers, no section labels. One sentence (or merged block) per line with a blank line between each. This is the file used by the TTS tool, image prompt generator, and Whisper alignment — it must be sentence-level, never multi-sentence blocks.

3. Once both files are saved, confirm with the Drive links and ask:
*"Structured script and clean narration file saved to Drive. Want me to punch up any section, or shall we continue to the next pipeline stage?"*

---

*Voice & tone: `references/VOICE.md` · Structure & pacing: `references/STRUCTURE.md` · Retention science: `references/RETENTION.md`*

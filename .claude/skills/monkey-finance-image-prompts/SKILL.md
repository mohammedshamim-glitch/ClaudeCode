---
name: monkey-finance-image-prompts
description: >
  State-of-the-art image prompt generator for Monkey Finance whiteboard animation videos.
  Transforms a narration script into sub-scenes (~25 words each) and generates eye-catching, 
  narrative-aligned prompts ready for Grok text-to-image generation (Stage 3 of the pipeline).
  Outputs both static image prompts AND video prompts with camera movements. Each prompt ties 
  directly to the script moment, extracts statistics for on-canvas visualisation, and respects 
  strict character and style rules (green suit monkey ONLY in first and final scenes).
  Use this skill whenever Sham asks to generate image prompts, create scene visuals,
  turn a script into animation prompts, run Stage 3 of the pipeline, or says anything like
  "generate the image prompts", "create the scene visuals", "what does scene X look like",
  "make the prompts for Grok", or "image prompt generation".
  Always consult this skill before writing a single image prompt for Monkey Finance — never
  guess the rules, never skip this skill.
---

# 🎨 Monkey Finance — Image Prompt Generator

One job. One standard. **Every scene should stop a viewer mid-scroll if it were a still image.**

Each prompt produced by this skill is engineered across three dimensions simultaneously:
- **Narrative alignment** — the visual directly reflects what the narrator is saying
- **Emotional punch** — the composition, character, and colour communicate the feeling
- **Brand consistency** — every scene fits the Monkey Finance visual identity

---

## Read Before Writing Anything

| File | What it covers | When to read |
|---|---|---|
| `references/VISUAL-RULES.md` | Full brand visual rules, character specs, colour palette, composition principles | Always — read first |
| `references/SCENE-TYPES.md` | Scene classification system, monkey usage rules, prompt formulas by type | Always — read second |
| `references/PROMPT-EXAMPLES.md` | 15 annotated example prompts across all scene types | Read when in doubt |

**Do not write a single prompt until all three are loaded.**

---

## Inputs

| Input | Source | Notes |
|---|---|---|
| `narration_script.txt` | Pipeline Stage 2 output / Drive | Plain text, scenes separated by blank lines |
| `content_brief` | Drive or conversation | Used for emotional arc and topic context |
| `scene_count` | Calculated from narration | Must match sub-scene count exactly (typically 35-45 sub-scenes) |

---

## The Sub-Scene Method

Parse the narration into sub-scenes at ~25 words each. One scene per 20-30 words of narration. Label as 1.1, 1.2, 2.1, 2.2, etc.

### Pass 1 — Parse & Map (The Director)
Split narration paragraphs into sub-scenes. For a 100-word paragraph, create ~4 sub-scenes. For each sub-scene, identify:
- **What specific moment** is being narrated (not the whole paragraph concept)
- **What emotion** this specific moment creates
- **What visual** best represents this exact moment
- **Whether a stat/number** appears — if so, it MUST be drawn on the canvas
- **Whether a monkey** adds value — green suit (first & last only) / plain / none

### Pass 2 — Write Two Files (The Artist)
Generate both output files simultaneously:
1. **Image prompts** — static scenes for Grok text-to-image
2. **Video prompts** — identical scenes + camera movement appended

Format: `1.1 2D colourful whiteboard animation style...composition. [Camera movement for video version only]`

### Pass 3 — Quality Edit (The Director Again)
Read all prompts as a sequence. Check:
- [ ] Sub-scene count matches narration parsing (~25 words each)
- [ ] Visual variety across adjacent sub-scenes
- [ ] Emotional arc flows naturally
- [ ] Every stat has the number explicitly written on canvas
- [ ] Green suit monkey ONLY in first and final scenes
- [ ] Scene numbers at start of each line, all content in one paragraph
- [ ] Camera movements logical and varied

---

## Mandatory Opener — Every Prompt Without Exception

```
2D colourful whiteboard animation style. Clean white background.
```

This must be the exact first line of every single prompt. No exceptions. No variations.

---

## Monkey Usage Rules — Strict

| Scene | Rule |
|---|---|
| **Scene 01** | Green suit monkey ONLY — brand intro |
| **Final scene** | Green suit monkey ONLY — brand sign-off |
| **Select emotional scenes** | Plain monkey (no suit) — shock, confusion, relief, realisation |
| **Most scenes** | No monkey — pure visual storytelling |

**Plain monkey threshold:** Use a plain monkey in roughly 15–20% of scenes (8–12 scenes in a typical 55-scene video). Choose moments of strongest emotional reaction: the "aha" moment, the horror reveal, the satisfied conclusion.

**Never use:**
- ❌ Green suit monkey in any scene except Scene 01 and the final scene
- ❌ A monkey in scenes that work better as pure data/diagram visuals
- ❌ Logos of any kind
- ❌ A physical whiteboard object (frame, tray, eraser) — just clean white background
- ❌ Jungle settings, vines, tropical colours as primary environment
- ❌ 3D rendering, photorealism, cinematic lighting

---

## Stat & Number Rule — Non-Negotiable

Wherever the narration mentions a statistic, percentage, or number, the image prompt **MUST** explicitly instruct that number to be hand-written on the canvas in large, readable marker text.

**Examples:**
- Narration: *"inflation hit 9.1%"* → Prompt must say: *"bold red marker text reading '9.1%' hand-written large on the canvas"*
- Narration: *"the average increase is £34,000"* → Prompt must say: *"'£34,000' written in large bold red marker, underlined twice"*
- Narration: *"10,500 estates affected"* → Prompt must say: *"'10,500' hand-drawn in thick black marker, prominent on the left side of the canvas"*

---

## Ken Burns Composition Rules

Videos are assembled using Ken Burns effects — slow zoom in, zoom out, or pan across each static image. Compose every prompt with KB in mind:

**Rule 1 — Focal element off-centre, not at edges.**
The KB zoom travels *toward* the main element. If it's dead-centre, the zoom just enlarges. If it's slightly right-of-centre, the pan+zoom has somewhere to go. Specify position explicitly (e.g. "key stat positioned right of centre").

**Rule 2 — 15–20% white margin on all edges.**
KB crops edges during zoom. Critical content — stats, faces, labels — must sit inside the central 80% of the canvas. Say so in the prompt.

**Rule 3 — Left-to-right layouts for pan scenes.**
Before/after comparisons, timelines, and two-column splits should place the "setup" left and the "payoff" right. The KB pan travels left to right and lands on the payoff.

**Rule 4 — Sparse compositions travel better.**
Overcrowded scenes don't give KB anything to move through. One dominant element with clear negative space is always better than multiple competing elements.

**Apply in prompts:** Add a brief composition note to each prompt (e.g. "Left-to-right layout; '£78,000' right of centre as the KB pan destination" or "Central focal element with 20% white margin all sides for KB zoom room").

---

## Output Format

Generate TWO files — **no headers, no section labels, no title block**. Just scene number and prompt text, blank line between each scene.

### Image Prompts (`04-image-prompts.txt`)
```
1.1 2D colourful whiteboard animation style. Clean white background. [full scene description + KB composition note] Bold colourful hand-drawn illustration, 16:9 widescreen aspect ratio, landscape composition.

1.2 2D colourful whiteboard animation style. Clean white background. [full scene description + KB composition note] Bold colourful hand-drawn illustration, 16:9 widescreen aspect ratio, landscape composition.
```

### Video Prompts (`05-video-prompts.txt`)
```
1.1 2D colourful whiteboard animation style. Clean white background. [full scene description + KB composition note] Bold colourful hand-drawn illustration, 16:9 widescreen aspect ratio, landscape composition. Slow push in toward the headline text — urgency builds as the words get closer.

1.2 2D colourful whiteboard animation style. Clean white background. [full scene description + KB composition note] Bold colourful hand-drawn illustration, 16:9 widescreen aspect ratio, landscape composition. Hold steady, then slow zoom out to reveal the full checklist.
```

**Critical formatting:**
- Scene number at start of line (e.g. `1.1`, `2.3`) — nothing else before it
- Everything in one paragraph per scene
- Blank line between scenes
- KB composition note woven into the scene description (not tacked on at the end)
- Camera movement appended to end for video version only
- **No file title, no section headers, no dividers** — prompts only

Save both files to Drive in run's project folder.
Total sub-scene count: typically 45–55 sub-scenes for a 10-15 minute script.

---

## Final Quality Check — Clear All 9 Before Delivering

- [ ] **Sub-scene count matches narration** — ~25 words each, total 45–55 sub-scenes
- [ ] **Scene numbers match the structured script** — use the same `X.Y` numbering
- [ ] **Every prompt starts** with `2D colourful whiteboard animation style. Clean white background.`
- [ ] **Green suit monkey** appears only in Scene 01 and the final scene
- [ ] **Plain monkey** used in 15–20% of scenes at emotional peak moments
- [ ] **Every stat scene** has the number explicitly drawn on the canvas
- [ ] **No logos, no whiteboard object, no jungle** in any scene
- [ ] **Visual variety** — no two adjacent scenes are compositionally identical
- [ ] **KB composition note** in every prompt — focal element position, margin, and pan direction specified
- [ ] **No headers or section labels** in either output file — scene number and prompt text only

---

## Delivery

Output both `04-image-prompts.txt` and `05-video-prompts.txt` to Drive and display the on-screen approval prompt per CONTEXT.md §5.
Then confirm: *"Stage 3 complete — {sub_scene_count} image & video prompts saved to Drive. Ready for your review before Stage 4."*

---

*Visual rules & colour palette: `references/VISUAL-RULES.md` · Scene types & formulas: `references/SCENE-TYPES.md` · Annotated examples: `references/PROMPT-EXAMPLES.md`*

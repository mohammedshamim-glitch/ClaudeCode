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
1. **Image prompts** (`04-image-prompts.txt`) — static scenes for Grok text-to-image, with central 60% / 20% border rule in every prompt
2. **KB movements** (`05-kb-movements.txt`) — one line per scene: scene number + camera movement only

Format image prompts: `1.1 2D colourful whiteboard animation style...All critical elements within the central 60% of the frame — minimum 20% clear margin on all edges. Bold colourful hand-drawn illustration, 16:9 widescreen aspect ratio, landscape composition.`

Format KB file: `1.1 Slow push in toward X — [why it works emotionally].`

### Pass 3 — Quality Edit (The Director Again)
Read all prompts as a sequence. Check:
- [ ] Sub-scene count matches narration parsing (~25 words each)
- [ ] Visual variety across adjacent sub-scenes
- [ ] Emotional arc flows naturally
- [ ] Every stat has the number explicitly written on canvas
- [ ] Green suit monkey ONLY in first and final scenes
- [ ] Scene numbers at start of each line, all content in one paragraph
- [ ] Central 60% / 20% border instruction present in every image prompt
- [ ] KB movements in separate file only — never embedded in image prompts
- [ ] Camera movements logical and varied

---

## Mandatory Opener — Every Prompt Without Exception

```
2D colourful whiteboard animation style. Clean white background.
```

This must be the exact first line of every single prompt. No exceptions. No variations.

---

## Mandatory Rule — No Channel Branding Ever

**This rule applies to every single scene, including and especially the final scene.**

Never write any of the following on the canvas in any prompt:
- ❌ "Monkey Finance"
- ❌ "Monkey See Money"
- ❌ Any channel name, show name, or brand name
- ❌ Any URL, handle, or social media reference

The green suit monkey in the final scene is the brand sign-off — the visual alone is the identifier. No text branding is ever needed or permitted. If you catch yourself writing a channel name into a prompt, delete it immediately.

---

## Monkey Usage Rules — Strict

| Scene | Rule |
|---|---|
| **Scene 01** | Green suit monkey ONLY — brand intro |
| **Final scene** | Green suit monkey ONLY — brand sign-off |
| **Most scenes** | Monkey — present in ~75% of all scenes as guide, narrator, reactor |
| **Stat-heavy scenes** | No monkey — pure data/diagram visuals only (~25% of scenes) |

**Monkey threshold:** Use a monkey in approximately 75% of scenes. Reserve no-monkey treatment for scenes where a statistic or diagram is the sole centrepiece and a character would distract from the number. The monkey acts as guide, narrator, and emotional reactor throughout — not just at peak moments.

**Never use:**
- ❌ Green suit monkey in any scene except Scene 01 and the final scene
- ❌ A monkey in scenes where a stat must dominate the entire frame
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

Videos use Ken Burns effects — slow zoom in, zoom out, or pan across each static image. Two rules are non-negotiable:

**Rule 1 — Central 60% only. Always.**
All critical elements (stats, characters, key text, diagrams) must be positioned within the central 60% of the frame. Leave a minimum 20% clear margin on all four edges. The KB pan will travel across the outer 20% — anything outside the 60% zone risks being cropped.

Add this exact instruction to every single prompt, just before the closing style line:
> `All critical elements within the central 60% of the frame — minimum 20% clear margin on all edges.`

**Rule 2 — KB applies to 25% of scenes only.**
Only every 4th scene gets a Ken Burns effect — the rest are static. Design all images with the 20% margin regardless, but do not force dramatic off-centre compositions for static scenes.

**Rule 3 — Sparse beats crowded.**
One dominant element with generous white space. Overcrowded compositions look worse under any movement.

---

## The 4 KB Effects — Use These Exact Labels

There are exactly **4 effects** available. Every scene in `05-kb-movements.txt` must use one of these four labels verbatim — nothing else:

| Label | What it does | Best for |
|---|---|---|
| `pan left to right` | Camera travels left → right | Timelines, before/after, reveal on the right |
| `pan right to left` | Camera travels right → left | Contrast, correction, reversal of expectation |
| `pan top to bottom` | Camera drifts downward | Downward pressure, falling values, bad news |
| `pan bottom to top` | Camera drifts upward | Rising charts, growth, upward momentum, optimism |

**Assign by choosing the effect that serves the scene's emotional job.** When in doubt, `pan left to right` is the default.

Vary the effects across the video — avoid using the same effect more than 3 times in a row.

---

## Output Format

Generate TWO files — **no headers, no section labels, no title block**. Just scene number and content, blank line between each scene.

### Image Prompts (`04-image-prompts.txt`)
```
1.1 2D colourful whiteboard animation style. Clean white background. [full scene description] All critical elements within the central 60% of the frame — minimum 20% clear margin on all edges. Bold colourful hand-drawn illustration, 16:9 widescreen aspect ratio, landscape composition.

1.2 2D colourful whiteboard animation style. Clean white background. [full scene description] All critical elements within the central 60% of the frame — minimum 20% clear margin on all edges. Bold colourful hand-drawn illustration, 16:9 widescreen aspect ratio, landscape composition.
```

### KB Movements (`05-kb-movements.txt`)
One of the 4 exact effect labels per scene. Scene number + label only. No descriptions, no explanations.
```
1.1 pan left to right

1.2 pan right to left

1.3 pan top to bottom

1.4 pan bottom to top
```

**Critical formatting:**
- Scene number at start of every line in both files
- Image prompts: everything in one paragraph, blank line between scenes
- KB file: scene number + exact effect label only, blank line between scenes
- **Only these 4 labels are valid:** `pan left to right` / `pan right to left` / `pan top to bottom` / `pan bottom to top`
- **Central 60% / 20% border instruction verbatim in every single image prompt** — never omit
- **KB movements in `05-kb-movements.txt` ONLY** — never embedded in image prompts
- **No file title, no section headers, no dividers** — scene number and label only

Save both files to Drive in run's project folder.
Total sub-scene count: typically 45–55 sub-scenes for a 10-15 minute script.

---

## Final Quality Check — Clear All 9 Before Delivering

- [ ] **Sub-scene count matches narration** — ~25 words each, total 45–55 sub-scenes
- [ ] **Scene numbers match the structured script** — use the same `X.Y` numbering
- [ ] **Every prompt starts** with `2D colourful whiteboard animation style. Clean white background.`
- [ ] **Green suit monkey** appears only in Scene 01 and the final scene
- [ ] **Monkey** used in 15–20% of scenes at emotional peak moments
- [ ] **Every stat scene** has the number explicitly drawn on the canvas
- [ ] **No logos, no whiteboard object, no jungle** in any scene
- [ ] **No channel name, brand name, or text branding** of any kind — no "Monkey Finance", "Monkey See Money", or any channel identifier written in the scene
- [ ] **Visual variety** — no two adjacent scenes are compositionally identical
- [ ] **KB composition note** in every prompt — focal element position, margin, and pan direction specified
- [ ] **No headers or section labels** in either output file — scene number and prompt text only

---

## Delivery

Before generating any files, ask: *"Do you want me to also generate the KB movements file (`05-kb-movements.txt`) alongside the image prompts, or image prompts only?"*

- If image prompts only → save `04-image-prompts.txt` to Drive only.
- If both → save `04-image-prompts.txt` and `05-kb-movements.txt` to Drive.

Then confirm: *"Stage 3 complete — {sub_scene_count} image prompts saved to Drive. Ready for your review before Stage 4."*

---

*Visual rules & colour palette: `references/VISUAL-RULES.md` · Scene types & formulas: `references/SCENE-TYPES.md` · Annotated examples: `references/PROMPT-EXAMPLES.md`*

---
name: monkey-finance-image-prompts
description: >
  State-of-the-art image prompt generator for Monkey Finance whiteboard animation videos.
  Transforms a narration script into sub-scenes (~25 words each) and generates eye-catching, 
  narrative-aligned prompts ready for Grok text-to-image generation (Stage 3 of the pipeline).
  Outputs static image prompts only (04-image-prompts.txt). Each prompt ties 
  directly to the script moment, extracts statistics for on-canvas visualisation, and respects 
  strict character and style rules (monkey appears in ~80% of scenes; never specify suit colour).
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

## Before Starting — Check for Named Characters

If the episode has named characters, read `00b-character-references.txt` from the episode Drive folder before writing a single prompt. It tells you:
- Which characters appear in this episode
- Which scenes each character appears in
- Their colour identity (for consistent scene composition)

If the episode is monkey-only, skip this step.

---

## The 1:1 Scene Method

**One image prompt per narration scene. No grouping. No merging.**

The narration script uses scenes of varying length — one visual beat per scene, typically 5–29 words. There is no fixed word-count target. Short sentences that share the same visual moment may appear grouped on one line in the script; honour those boundaries exactly. Sham edits scene boundaries in the V2 Google Doc — always reverse-engineer the structured script from his edited clean script, never re-split by word count. Numbered items (One:, Two:, Three:, Option one: etc.) always start a new scene. Every narration scene gets its own image prompt — label using the structured script's scene numbers (e.g. 0.1, 0.2, 1.1, 1.2, 3.4, etc.). A 107-scene script produces 107 image prompts.

### Pass 1 — Parse & Map (The Director)
For each narration scene, identify:
- **What specific moment** is being narrated
- **What emotion** this specific moment creates
- **What visual** best represents this exact moment
- **Whether a stat/number** appears — if so, it MUST be drawn on the canvas
- **Whether a monkey** adds value — present / none (never specify suit colour)

### Pass 2 — Write the Image Prompts File (The Artist)
Generate one output file:
1. **Image prompts** (`04-image-prompts.txt`) — static scenes for Grok text-to-image, with central 60% / 20% border rule in every prompt

**Note: `05-video-prompts.txt` is deprecated and no longer generated.** Image prompts only.

Format image prompts: `1.1 2D colourful whiteboard animation style. Clean white background. All critical elements within the central 60% of the frame — minimum 20% clear margin on all edges. 16:9 widescreen aspect ratio, landscape composition. [scene description] Bold colourful hand-drawn illustration.`

The 60% border + 16:9 instruction is always the **second sentence** — immediately after "Clean white background." and before any scene description. Never at the end.

Example — monkey with prop:
`1.1 2D colourful whiteboard animation style. Clean white background. All critical elements within the central 60% of the frame — minimum 20% clear margin on all edges. 16:9 widescreen aspect ratio, landscape composition. A monkey pulling back a large curtain to reveal a bold question mark drawn on the canvas behind it, expression curious and wide-eyed. Bold colourful hand-drawn illustration.`

Example — stat scene (no monkey):
`1.2 2D colourful whiteboard animation style. Clean white background. All critical elements within the central 60% of the frame — minimum 20% clear margin on all edges. 16:9 widescreen aspect ratio, landscape composition. Bold hand-drawn text reading '£4,500' in thick red marker, underlined once. A small hand-drawn house sketch beside it with an arrow pointing to the number. Bold colourful hand-drawn illustration.`

### Pass 3 — Quality Edit (The Director Again)
Read all prompts as a sequence. Check:
- [ ] Prompt count matches narration scene count exactly (1:1)
- [ ] Visual variety across adjacent prompts
- [ ] Emotional arc flows naturally
- [ ] Every stat has the number explicitly written on canvas
- [ ] No suit colour specified in any monkey prompt
- [ ] Scene numbers at start of each line, all content in one paragraph
- [ ] Central 60% / 20% border instruction present in every image prompt
- [ ] **Character expressions**: every named character scene has a contextually appropriate facial expression — anxious/worried for setbacks, confident/relieved for wins, surprised for reveals, thoughtful for realisations

---

## Mandatory Opener — Every Prompt Without Exception

Every image prompt must begin with these two statements in this exact order:

```
2D colourful whiteboard animation style. Clean white background. All critical elements within the central 60% of the frame — minimum 20% clear margin on all edges. 16:9 widescreen aspect ratio, landscape composition.
```

Statement 1: style + background. Statement 2: composition constraints + aspect ratio. Then the scene description. Then the closing style line. No exceptions. No variations.

---

## Mandatory Rule — No Channel Branding Ever

**This rule applies to every single scene, including and especially the final scene.**

Never write any of the following on the canvas in any prompt:
- ❌ "Monkey Finance"
- ❌ "Monkey See Money"
- ❌ Any channel name, show name, or brand name
- ❌ Any URL, handle, or social media reference

The monkey in the final scene is the brand sign-off — the visual alone is the identifier. No text branding is ever needed or permitted. Never specify a suit colour in any monkey prompt — let Grok determine it. If you catch yourself writing a channel name into a prompt, delete it immediately.

---

## Named Character Rule — Non-Negotiable

**If a scene names a character, that character must appear in the image. The monkey never replaces a named character.**

In character-driven episodes (e.g. Sarah vs David, Jake vs Marcus), if a scene's narration references a named character by name, that character must be visually present in the prompt. The monkey may also appear in that scene as a narrator or guide — but it must be *alongside* the named characters, never *instead of* them.

**Examples:**
- Scene says "Sarah signs a PCP deal. David takes a personal loan." → Sarah AND David must both appear. Monkey may be present as a small narrator figure pointing at them — but monkey does not replace Sarah.
- Scene says "David makes his final payment." → David must appear. Monkey optional as narrator.
- Scene has no named character references → normal monkey/no-monkey rules apply.

---

## Monkey Action Rule — Non-Negotiable

**The monkey must always be DOING something. Never just standing.**

Every scene with a monkey requires an active physical action with a prop — pressing a button, holding an umbrella in a storm, looking through binoculars, assembling puzzle pieces, waving a flag, carrying a weight, pulling back a curtain, writing on a board. The monkey should look mid-action, not posed. A static standing monkey is a failed prompt — rewrite it before delivering.

Full action library is in `references/VISUAL-RULES.md`.

---

## Monkey Usage Rules — Strict

| Scene | Rule |
|---|---|
| **Scene 01** | Monkey — brand intro |
| **Final scene** | Monkey — brand sign-off |
| **Most scenes** | Monkey — present in ~80% of all scenes as guide, narrator, reactor |
| **Stat-heavy / diagram scenes** | No monkey — pure data/diagram visuals only (~20% of scenes) |

**Monkey threshold:** Use a monkey in approximately 80% of scenes. The monkey is the consistent visual narrator throughout the video — always active, always doing something with a prop. Reserve no-monkey treatment only for scenes where a large statistic or diagram must dominate the entire frame without distraction (e.g. a full-canvas £680,000 reveal, a 40% tax threshold chart). If in doubt, include the monkey.

**Never use:**
- ❌ Any suit colour specified in a monkey prompt
- ❌ "cartoon monkey" — always just "monkey"
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

## Composition Rules

**Rule 1 — Central 60% only. Always.**
All critical elements (stats, characters, key text, diagrams) must be positioned within the central 60% of the frame. Leave a minimum 20% clear margin on all four edges.

Add this exact instruction to every single image prompt, just before the closing style line:
> `All critical elements within the central 60% of the frame — minimum 20% clear margin on all edges.`

**Rule 2 — Sparse beats crowded.**
One dominant element with generous white space. Overcrowded compositions lose impact.

---

## Output Format

Generate TWO files — **no headers, no section labels, no title block**. Just scene number and content, blank line between each scene.

### Image Prompts (`04-image-prompts.txt`)
```
1.1 2D colourful whiteboard animation style. Clean white background. All critical elements within the central 60% of the frame — minimum 20% clear margin on all edges. 16:9 widescreen aspect ratio, landscape composition. [full scene description] Bold colourful hand-drawn illustration.

1.2 2D colourful whiteboard animation style. Clean white background. All critical elements within the central 60% of the frame — minimum 20% clear margin on all edges. 16:9 widescreen aspect ratio, landscape composition. [full scene description] Bold colourful hand-drawn illustration.
```

**Critical formatting:**
- Scene number at start of every line
- Everything in one paragraph, blank line between scenes
- **Central 60% / 20% border + 16:9 instruction is always the second statement** — immediately after "Clean white background." Never at the end, never omitted
- **No file title, no section headers, no dividers** — scene number and content only

Save `04-image-prompts.txt` to Drive in the episode folder.
Total prompt count: matches the narration scene count exactly — typically 80–120 prompts.

---

## Final Quality Check — Clear All Before Delivering

**Image prompts:**
- [ ] **Prompt count matches narration scene count exactly** — 1 prompt per scene, no grouping
- [ ] **Scene numbers match the structured script** — use the same `X.Y` numbering
- [ ] **Every prompt starts** with `2D colourful whiteboard animation style. Clean white background.`
- [ ] **No suit colour** specified in any monkey prompt
- [ ] **Monkey** used in ~80% of scenes as guide, narrator, reactor
- [ ] **Every monkey scene** has the monkey performing an active action with a prop — never just standing
- [ ] **Named characters appear in scenes that reference them** — monkey never replaces a named character, only accompanies them
- [ ] **Every stat scene** has the number explicitly drawn on the canvas
- [ ] **No logos, no whiteboard object, no jungle** in any scene
- [ ] **No channel name, brand name, or text branding** of any kind
- [ ] **Visual variety** — no two adjacent scenes are compositionally identical
- [ ] **Central 60% / 20% border instruction** present in every image prompt
- [ ] **Named characters have scene-appropriate expressions** — never a neutral or generic pose
- [ ] **No headers or section labels** in output file

---

## Delivery

Generate one file only. Save to Drive in the episode folder:
- `04-image-prompts.txt`

Then confirm: *"Stage 3 complete — {scene_count} image prompts (1 per narration scene). Saved to Drive. Ready for your review before Stage 4."*

---

*Visual rules & colour palette: `references/VISUAL-RULES.md` · Scene types & formulas: `references/SCENE-TYPES.md` · Annotated examples: `references/PROMPT-EXAMPLES.md`*

# PROMPTS.md — AI Thumbnail Prompt System (LOCKED TEMPLATE)

## The one template — use it verbatim (Sham-approved, 30 Oct 2026)

Every thumbnail prompt is written from the **single locked template** below. It replicates the proven Wealth Logic layout with our monkey mascot as the host. **Do not invent new layouts, do not use the old "clean white background / hand-drawn marker" style, do not clutter the background.** Readability beats busyness — if a viewer can't read it in half a second in the feed, it loses.

The locked composition (what made the approved samples work):
- **Character on the LEFT** (~35–40% of frame): the Monkey mascot, big, upper-body, green suit + green tie + gold 'M' badge, ONE strong exaggerated expression matching the topic.
- **Two text lines, upper half, dominating:** setup line in solid **BLACK** heavy condensed block-caps, then the punch line in **WHITE** caps inside a **solid bright RED rectangle**. Typographic poster font (Impact/Anton), never hand-drawn/marker/outlined. Only these two text elements.
- **ONE simple clear visual** bottom-right: a single metaphor (two options / one object), **one bold £ number**, and **one thick RED arrow**. Nothing else.
- **Clean, simple background** — plain light colour or flat panel. **NO charts, graphs, grids, confetti or scattered currency symbols in the background.**
- £ only, never $/€. No company/person names. Never spoil which option wins (both look equally appealing).

### The template (fill the four `[CAPS]` slots):

```
Professional high-CTR YouTube thumbnail, clean bold 2D cartoon vector illustration, 16:9 landscape, extreme contrast and punchy, easy to read at a glance. NO border, NO frame, NO whiteboard panel, NO rounded corners. Clean simple background — a plain solid light colour; do NOT fill the background with charts, graphs, grids or scattered currency symbols. CHARACTER (left third): the Monkey mascot drawn LARGE as an upper-body figure, wearing its signature bright GREEN business suit, green tie and gold 'M' lapel badge exactly matching the reference image, with a strong exaggerated [EXPRESSION], clearly reacting to the scene. TEXT: clean BOLD HEAVY CONDENSED SANS-SERIF BLOCK CAPITALS (Impact / Anton poster font), crisp and typographic, NEVER hand-drawn, marker, sketchy or outlined. Setup line reads '[SETUP LINE]' in solid BLACK caps. Punch line reads '[PUNCH LINE]' in solid WHITE caps sitting inside a solid bright RED rectangle highlight bar. Only these two text elements, large and dominating the upper half. No other words anywhere. IMAGERY (right side): ONE single simple clear visual — [ONE VISUAL METAPHOR] — drawn large and bold, with one thick RED arrow and one big bold black £ number. Nothing else cluttering it. Money shown ONLY in UK pounds with the £ symbol — never $ or €. Do NOT reveal which option wins; keep both options looking equally appealing. Clean, bold, readable, scroll-stopping finance thumbnail.
```

**The four slots:**
- `[EXPRESSION]` — see the Expression Guide below; match the topic's emotion.
- `[SETUP LINE]` — 3–4 words max, the hook setup (ADDS to the title, never repeats it).
- `[PUNCH LINE]` — 2–3 words max, the curiosity punch (a question or payoff).
- `[ONE VISUAL METAPHOR]` — a single clean metaphor with one £ number + one red arrow.

---

## Filled examples (all in the locked style)

### Comparison / versus (the default for "A vs B — Real Math" episodes)
```
...with a strong exaggerated thoughtful look — one hand stroking the chin, eyebrow raised, glancing between the two choices... Setup line reads 'PAY OFF THE MORTGAGE' in solid BLACK caps. Punch line reads 'OR INVEST?' in solid WHITE caps sitting inside a solid bright RED rectangle highlight bar... IMAGERY (right side): ONE single simple clear visual — on one side a hand-drawn house, on the other a rising green stock-market chart arrow, with a large bold black '£250,000' between them — drawn large and bold, with one thick RED arrow...
```

### Question / hook
```
...with a strong exaggerated worried, uncertain expression, looking back and forth between the two choices... Setup line reads 'RENT OR BUY' in solid BLACK caps. Punch line reads 'A HOUSE?' in solid WHITE caps sitting inside a solid bright RED rectangle highlight bar... IMAGERY (right side): ONE single simple clear visual — a small rented flat with a 'TO LET' sign on one side and a house with a 'SOLD' sign on the other, with a large bold black '£100,000' between them — drawn large and bold, with one thick RED arrow...
```

### Single big stat / warning
```
...with a strong exaggerated shocked expression, jaw dropped, one hand raised to the side of the face... Setup line reads 'YOUR PENSION' in solid BLACK caps. Punch line reads 'DEATH TAX?' in solid WHITE caps sitting inside a solid bright RED rectangle highlight bar... IMAGERY (right side): ONE single simple clear visual — a single large bold black '£40,000' with a red downward arrow beside a simple hand-drawn pension pot — drawn large and bold...
```

---

## Monkey Expression Guide — pick one, state it precisely

Always one clear expression, matched to the topic's emotion. Never neutral.

| Emotion | Expression to write |
|---|---|
| 🧐 Curiosity / weighing it up | thoughtful look, one hand stroking the chin, eyebrow raised, glancing between the choices |
| 😨 Fear / warning | shocked, jaw dropped, eyes wide, one hand raised to the side of the face |
| 😮 Shock / surprise | eyes wide, brows high, mouth open in an O, one hand on head |
| 🤑 Aspiration / excited | big smile, eyes lit up, one finger pointing upward |
| 😤 Serious / stern | furrowed brow, tight mouth, intense eyes, arms crossed or one finger pointing firmly |
| 😕 Uncertain / torn | worried, puzzled, looking back and forth between two choices |

---

## Flow / generation requirements — non-negotiable

Whether generated in Flow (default) or via the API:
1. **Attach `Monkey.webp`** (Character References folder `1ObdWnyzOsU6pOCvbd-I_bdDjShcC-yps`) as the reference image so the mascot stays on-model (green suit, M badge).
2. **Set aspect ratio to 16:9.** Via the API this means `generationConfig.imageConfig.aspectRatio="16:9"` — never rely on prompt text alone.
3. Output size target **1280×720** (resize on save if the model returns 1344/1376-wide).
4. Thumbnails may use the **Pro** model (`gemini-3-pro-image`) when generating via API — worth the fidelity for the one image.

---

## 07-thumbnail-prompt.txt output format

`07-thumbnail-prompt.txt` contains **only the raw filled prompt** — the locked template with the four slots filled for this episode. No headers, no labels, no brief, nothing else. Ready to paste straight into Flow.

---

## Prompt Quality Checklist

- [ ] Built from the locked template verbatim (no new layout invented)
- [ ] Monkey on the LEFT, green suit + M badge, ONE precise expression stated
- [ ] Setup line solid BLACK caps; punch line WHITE caps in a solid RED box
- [ ] Typographic poster font specified — NOT hand-drawn/marker/outlined
- [ ] Exactly ONE visual metaphor + ONE £ number + ONE red arrow
- [ ] Clean simple background — NO background charts/graphs/grids/scattered symbols
- [ ] £ only, no $/€; no company/person names; winner NOT spoiled
- [ ] Flow reminder present (attach Monkey.webp, 16:9) where relevant
- [ ] No channel name or branding on the thumbnail

---

## Negative prompts (append if the model drifts)

```
no border, no frame, no whiteboard panel, no rounded corners,
no background charts, no graphs, no grids, no scattered currency symbols,
no hand-drawn or marker text, no outlined or glowing text, no rainbow text,
no $ or € symbols, no company or brand names, no photorealistic style,
no cluttered background, no small illegible text, no American references
```

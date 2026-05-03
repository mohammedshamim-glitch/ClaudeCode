# PROMPTS.md — AI Image Generation Prompt System for Thumbnails

## The Monkey Finance Visual Identity

Every thumbnail uses the **same consistent style** as the pipeline's scene images. This is non-negotiable — visual consistency across the channel builds brand recognition and trust.

**Core style DNA:**
- 2D colourful whiteboard animation style
- Clean white background (always)
- Monkey in a **green suit** — this is the fixed character design
- Bold hand-drawn illustration aesthetic — thick marker strokes, expressive lines
- Text on the whiteboard is always written in **thick marker style** (not digital fonts)
- High contrast, expressive composition
- Landscape orientation, 1280x720
- **No logos. No watermarks. No channel branding on the thumbnail.**

---

## The Master Prompt Formula

Every prompt is built in this order:

```
2D colourful whiteboard animation style. Clean white background. 
[MONKEY DESCRIPTION — green suit, position, expression, action]. 
On the whiteboard, [WHITEBOARD CONTENT — what's drawn/written and how]. 
[ADDITIONAL VISUAL ELEMENTS if needed]. 
Bold hand-drawn illustration style, high contrast, expressive composition, 
landscape orientation, YouTube thumbnail 1280x720, 
no logos, no watermarks, no text cutoff.
```

---

## The Whiteboard Content System

The whiteboard is the main communication surface. Everything the viewer reads happens on it.

### Text on the whiteboard — always specify:
- **Position** (top, centre, left side, right side)
- **Size** (largest/boldest, slightly smaller, small)
- **Marker colour** (thick black marker, thick red marker, thick green marker, thick blue marker, thick yellow marker)
- **Style** (written in thick marker, drawn in bold hand-drawn style, underlined in red)

### Graphic elements on the whiteboard — always hand-drawn, never digital icons:

| Element | Description for prompt |
|---|---|
| Arrow up | "bold green arrow shooting sharply upward, hand-drawn style" |
| Arrow down | "bold red arrow plunging downward, hand-drawn style" |
| Explosion/burst | "red hand-drawn explosion starburst icon" |
| Question mark | "large yellow question mark drawn in thick marker" |
| Pound sign | "large bold £ symbol in green marker" |
| Percentage | "oversized % symbol in red marker, hand-drawn" |
| Calendar | "hand-drawn calendar page with a date circled in red" |
| Warning sign | "hand-drawn red triangle warning icon" |
| Upward graph | "bold hand-drawn line graph shooting upward in green" |
| Downward graph | "bold hand-drawn line graph plunging downward in red" |
| Versus divider | "bold vertical line dividing whiteboard into two halves" |
| Highlight circle | "rough hand-drawn circle in red around the key word" |
| Clock/timer | "hand-drawn clock face with urgent red hands" |

---

## Monkey Expression & Action Guide

Always specify the monkey in a **green suit**. Always give both a precise **expression** AND a **body action**. Never leave either vague.

| Trigger | Expression | Body action |
|---|---|---|
| 😨 Fear / Warning | Wide eyes, open mouth, jaw dropped | Both hands raised to face in shock, or pointing frantically at the board |
| 😮 Shock / Surprise | Eyes wide, brows at top of head, mouth open in O | One hand on head, one pointing at the stat |
| 🧐 Curiosity | Head tilted, one eyebrow raised | Chin resting on hand, or tapping whiteboard thoughtfully |
| 🤑 Aspiration | Big smile, eyes lit up | Arms spread wide, or one fist pumped in the air |
| 😅 Relief | Relaxed expression, slight smile | Shoulders down, hands open, calm posture |
| 😤 Concern / Serious | Furrowed brow, tight mouth, intense eyes | Arms crossed, or one finger pointing firmly at text |
| 🎉 Excited | Huge grin, bright eyes | Both arms raised in celebration |

---

## Layout Templates

### Layout A: Big Stat / Number
*Use when the headline is a shocking number, percentage, or figure.*

```
2D colourful whiteboard animation style. Clean white background. 
Monkey in a green suit, [EXPRESSION DETAIL], positioned on the right side of the frame, 
[ACTION]. On the whiteboard, a single massive "[STAT]" written in the largest boldest 
thick [COLOUR] marker, dominating the left two-thirds of the frame. Below it in slightly 
smaller thick [COLOUR] marker: "[2-3 WORD LABEL]". [Optional hand-drawn graphic element 
next to the stat]. At the top of the whiteboard in thick black marker with [COLOUR] underline: 
"[HEADLINE]". Bold hand-drawn illustration style, high contrast, expressive composition, 
landscape orientation, YouTube thumbnail 1280x720, no logos, no watermarks.
```

**Example — Pension Tax:**
```
2D colourful whiteboard animation style. Clean white background. Monkey in a green suit, 
jaw dropped in shock, eyes wide open, one hand on head and the other pointing frantically 
at the whiteboard, positioned on the right side of the frame. On the whiteboard, a single 
massive "40%" written in the largest boldest thick red marker, dominating the left 
two-thirds of the frame. Below it in slightly smaller thick red marker: "DEATH TAX". 
To the left, a bold hand-drawn red explosion starburst icon. At the top of the whiteboard 
in the largest boldest thick black marker with red underline: YOUR PENSION. Bold hand-drawn 
illustration style, high contrast, expressive composition, landscape orientation, 
YouTube thumbnail 1280x720, no logos, no watermarks.
```

---

### Layout B: Question / Hook
*Use for "should I?", "why?", or counterintuitive curiosity topics.*

```
2D colourful whiteboard animation style. Clean white background. 
Monkey in a green suit, [EXPRESSION DETAIL], [ACTION]. 
On the whiteboard, at the top in the largest boldest thick black marker 
with [COLOUR] underline: "[QUESTION]". Below that in slightly smaller thick 
[COLOUR] marker: "[SUBTEXT]". [Optional visual element — graph, icon, symbol]. 
A large hand-drawn question mark in thick yellow marker [position]. 
Bold hand-drawn illustration style, high contrast, expressive composition, 
landscape orientation, YouTube thumbnail 1280x720, no logos, no watermarks.
```

**Example — Mortgage:**
```
2D colourful whiteboard animation style. Clean white background. Monkey in a green suit, 
head tilted to the side, one eyebrow raised in deep thought, one hand on chin and the other 
gesturing at the whiteboard, positioned centre-left. On the whiteboard, at the top in the 
largest boldest thick black marker with red underline: FIX NOW OR WAIT? Below that in 
slightly smaller thick blue marker: MORTGAGE RATES 2026. To the right, a large bold yellow 
question mark drawn in thick marker. Below the question mark, a hand-drawn line graph 
showing rates rising then beginning to fall, drawn in blue marker. Bold hand-drawn 
illustration style, high contrast, expressive composition, landscape orientation, 
YouTube thumbnail 1280x720, no logos, no watermarks.
```

---

### Layout C: Two-Option Comparison
*Use for versus topics — ISA vs ISA, cash vs stocks, fix vs tracker.*

```
2D colourful whiteboard animation style. Clean white background. 
Monkey in a green suit, [EXPRESSION DETAIL], positioned [centre / left], [ACTION]. 
On the whiteboard, a bold vertical line dividing it into two halves. 
On the left side: "[OPTION A]" in thick [COLOUR] marker at top, "[VALUE A]" below 
in [COLOUR] marker, and a hand-drawn [ICON A] beneath. 
On the right side: "[OPTION B]" in thick [COLOUR] marker at top, "[VALUE B]" below 
in [COLOUR] marker, and a hand-drawn [ICON B] beneath. 
Bold hand-drawn illustration style, high contrast, expressive composition, 
landscape orientation, YouTube thumbnail 1280x720, no logos, no watermarks.
```

**Example — ISA comparison:**
```
2D colourful whiteboard animation style. Clean white background. Monkey in a green suit, 
eyes darting between both sides in wide-eyed disbelief, both hands raised in a 
"what do I choose?" shrug gesture, positioned centre-bottom. On the whiteboard, a bold 
vertical line dividing it into two halves. On the left: "CASH ISA" in thick black marker 
at top, "4.5%" below in thick blue marker, a flat horizontal arrow in blue marker beneath. 
On the right: "STOCKS ISA" in thick black marker at top, "12%?" below in thick green marker, 
a bold arrow shooting sharply upward in green marker beneath. Bold hand-drawn illustration 
style, high contrast, expressive composition, landscape orientation, YouTube thumbnail 
1280x720, no logos, no watermarks.
```

---

## Style Modifiers — Always Append

```
Bold hand-drawn illustration style, high contrast, expressive composition, 
landscape orientation, YouTube thumbnail 1280x720, 
no logos, no watermarks, no text cutoff at edges, 
no photorealistic style, no digital-looking fonts on the whiteboard, 
no gradients, no drop shadows, clean white background
```

---

## Prompt Quality Checklist

- [ ] Opens with `"2D colourful whiteboard animation style. Clean white background."`
- [ ] Monkey described in **green suit** with specific **expression detail** AND **body action**
- [ ] Whiteboard text has **exact words**, **marker colour**, and **relative size**
- [ ] All graphic elements described as **hand-drawn** not digital
- [ ] Layout type is clear (A, B, or C)
- [ ] Style modifiers appended
- [ ] `1280x720` specified
- [ ] `no logos, no watermarks` included
- [ ] No channel name or branding referenced

---

## Iteration Tips

**Expression not reading clearly:** `"mouth open in a perfect O shape, both eyebrows raised to the top of the forehead, whites of eyes visible all around the iris"`

**Text looks digital:** Add `"all whiteboard text must look hand-written in thick marker, slightly imperfect lettering, not a computer font"`

**Too cluttered:** Add `"maximum 3 elements on the whiteboard, generous white space, nothing overlapping"`

**Monkey doesn't feel like a character:** Add `"the monkey should look like a recurring cartoon character with consistent design, full of personality"`

**Whiteboard feels flat:** Add `"slight texture on whiteboard surface, bold expressive line weight, dynamic energetic composition"`

---

## Negative Prompts

```
no watermarks, no logos, no channel name, no text cutoff, 
no photorealistic style, no digital computer fonts, 
no gradients, no drop shadows, no cluttered background, 
no more than 3 whiteboard elements, no small illegible text, 
no American references
```

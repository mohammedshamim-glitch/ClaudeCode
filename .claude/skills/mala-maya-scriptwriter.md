---
name: mala-maya-scriptwriter
description: >
  Scriptwriter for the Maya & Mala Kids channel. Writes original children's stories
  (Path A) or nursery song lyrics (Path B) — age-appropriate, engaging, 18+ scenes,
  targeting 7+ minutes of content. Supports Maya & Mala named characters or generic
  child figures. Use this skill whenever the user asks to write a story, write lyrics,
  draft the script, or says "Step 1" in the Mala and Maya pipeline.
---

# ✍️ Maya & Mala Kids — Scriptwriter

Two content types. One standard. **Every piece of content should make a child want to watch again.**

---

## Inputs — Confirm Before Writing

Before starting, confirm:
1. **Path A (Children's Story)** or **Path B (Nursery Song)**
2. **Include Maya & Mala** (default) or **No named characters**
3. The **approved topic** from Step 0

---

## Maya & Mala Character Descriptions

When including named characters, use consistent descriptions throughout:

| Character | Description |
|---|---|
| **Maya** | Black pigtails, bright curious eyes, loves adventure |
| **Mala** | Curly brown hair, warm smile, loves singing and animals |

Both characters are always shown together, rendered at equal size.

When no named characters: use "you", "we", "friends", or "a child" — no specific names.

---

## Path A — Children's Story

**Target:** 18+ scenes, at least 7 minutes (~420 seconds) of narration

**Structure:**
- Clear beginning, middle, and end
- One core lesson or emotional message
- Age-appropriate language (3–7 years old)
- Short paragraphs — one thought per paragraph (this becomes one scene)
- No dialogue — narration only
- Warm, gentle, encouraging tone

**Output:** `01_story_approved.txt`

**Format:**
```
Title: [Story Title]

[Scene paragraph 1 — one thought, ~20–30 words]

[Scene paragraph 2]

[Scene paragraph 3]

...
```

Each blank-line-separated paragraph = one scene. Minimum 18 paragraphs.

---

## Path B — Nursery Song Lyrics

**Target:** 18+ sections, at least 7 minutes of sung content

**Structure:**
- Intro → Verse 1 → Chorus → Verse 2 → Chorus → Bridge → Verse 3 → Chorus → Outro
- One action or thought per section — keep it singable
- Repetitive, catchy choruses children can memorise
- Rhyming scheme: AABB or ABAB preferred
- Style: playful, bouncy, fun — matches `children's nursery rhymes, playful, fun and sing along`

**Output:** `01_song_lyrics_approved.txt`

**Format:**
```
Title: [Song Title]
Suno Style: children's nursery rhymes, playful, fun and sing along, upbeat, bouncy, whimsical, kids pop

[Intro]
[lyrics]

[Verse 1]
[lyrics]

[Chorus]
[lyrics]

...
```

Label each section clearly (Intro, Verse 1, Chorus, Bridge, Outro). Minimum 18 labelled sections.

---

## Quality Check — Clear All Before Saving

**Path A:**
- [ ] 18+ scene paragraphs (blank line between each)
- [ ] Age-appropriate for 3–7 year olds — no complex vocabulary
- [ ] Clear narrative arc (beginning, middle, end)
- [ ] One lesson or emotional takeaway
- [ ] No dialogue — narration only
- [ ] Maya & Mala consistent (if included): black pigtails / curly brown hair, always together

**Path B:**
- [ ] 18+ labelled sections (Intro, Verse, Chorus, Bridge, Outro)
- [ ] Suno style line included at top
- [ ] Each chorus identical (or near-identical) for singalong effect
- [ ] Rhyme scheme consistent throughout
- [ ] One action/thought per section — not too dense

---

## Delivery

Write the full story or lyrics and post in chat for approval **before** saving to Drive.

Once approved:
1. Save to Drive in the episode folder as `01_story_approved.txt` or `01_song_lyrics_approved.txt`
2. Confirm with Drive link
3. Ask: *"Happy with this? Shall we move to image prompts?"*

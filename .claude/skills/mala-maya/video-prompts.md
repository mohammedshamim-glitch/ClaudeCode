---
name: mala-maya-video-prompts
description: >
  Video prompt generator for the Maya & Mala Kids channel. Combines Disney/Pixar
  style scene visuals with rich camera movement descriptions — one entry per scene,
  two lines each — ready for Grok video generation. Use this skill whenever the user
  asks for video prompts, camera movements, or says "Step 2B" in the Mala and Maya pipeline.
---

# 🎬 Maya & Mala Kids — Video Prompt Generator

One entry per scene. Two lines each. Line 1: what it looks like. Line 2: how it moves.

---

## Inputs

- Approved story or lyrics from Step 1
- Approved image prompts from Step 2A (`02_image_prompts.txt`)
- Character option: Maya & Mala included or no named characters

---

## Video Prompt Format

Each entry is two lines with no labels, no scene numbers in the output file — just content and blank lines:

```
Disney/Pixar style: [same visual description as the image prompt for this scene]. [If Maya & Mala: "Both characters rendered at equal size."]
[Camera movement description from the reference list below — rich descriptive context].
```

Blank line between each scene entry.

---

## Camera Movement Reference

Choose the most appropriate movement for each scene's emotional beat. Vary movements — never use the same one more than twice in a row.

| Movement | Best for |
|---|---|
| **Slow Dolly In** | Intimate emotional moments, character focus |
| **Slow Dolly Out** | Revealing scale, ending a section, pulling back for perspective |
| **Slow arc / orbit** | Two characters interacting, circular reveal |
| **Crane up** | Hopeful moments, rising energy, wide reveal |
| **Crane down** | Landing on a moment, grounding energy |
| **Tilt up** | Building anticipation, revealing something tall |
| **Tilt down** | Focusing in, settling on a detail |
| **Pan left / Pan right** | Following movement, scanning a landscape |
| **Rack focus (foreground to background)** | Shifting attention between two subjects |
| **Slow zoom in** | Highlighting an expression or detail |
| **Slow zoom out** | Revealing the bigger picture |
| **Hold steady** | Still, peaceful moments — let the scene breathe |
| **Over-the-shoulder** | Character looking at something, point-of-view feel |
| **Hyper zoom** | High-energy openings, exciting transitions |

Write camera movements with descriptive context — not just the name. Example:
- ❌ `Slow dolly in`
- ✅ `Slow dolly in toward Maya's face as her eyes widen with excitement, warm golden light behind her, the room gently expanding in depth as the camera moves closer`

---

## Maya & Mala in Video Prompts

When characters are included:
- Add `Both characters rendered at equal size.` at the end of Line 1
- Camera movements should frame both characters when they are together
- For solo moments (if story calls for it), frame the relevant character

---

## Quality Check — Clear All Before Saving

- [ ] One entry per scene — count matches story/lyrics and image prompts
- [ ] Every entry is exactly two lines (visual + camera movement)
- [ ] Blank line between each entry
- [ ] No scene numbers, no labels, no headers in the output file
- [ ] Camera movements are descriptive — not just movement names
- [ ] Variety — no identical movement on adjacent scenes, no same movement more than twice in a row
- [ ] "Both characters rendered at equal size." in every Maya & Mala scene (Line 1)
- [ ] All prompts are family-friendly

---

## Delivery

Post all prompts in chat for approval before saving.

Once approved:
1. Save to Drive in the episode folder as `02_video_prompts.txt`
2. Confirm with Drive link
3. Ask: *"Video prompts saved. Moving to SEO?"*

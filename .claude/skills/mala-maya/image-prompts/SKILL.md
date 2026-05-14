---
name: mala-maya-image-prompts
description: >
  Image prompt generator for the Maya & Mala Kids channel. Transforms a story or
  nursery song into Disney/Pixar style image prompts — one per scene — ready for
  Grok or Whisk text-to-image generation. Handles both Maya & Mala named characters
  and generic child figures. Use this skill whenever the user asks for image prompts,
  scene visuals, or says "Step 2A" in the Mala and Maya pipeline.
---

# 🎨 Maya & Mala Kids — Image Prompt Generator

One visual per scene. Disney/Pixar quality. Every image should delight a child and stop a parent mid-scroll.

---

## Inputs

- Approved story or lyrics from Step 1 (`01_story_approved.txt` or `01_song_lyrics_approved.txt`)
- Character option: Maya & Mala included or no named characters

---

## Maya & Mala Character Descriptions

Always reference these descriptions consistently when characters appear:

- **Maya**: A cheerful girl with black pigtails, bright curious eyes, wearing colourful clothes
- **Mala**: A warm girl with curly brown hair, a big smile, wearing colourful clothes
- Both characters are always rendered at equal size, side by side

When no named characters: use "two cheerful children" or "a child" as appropriate.

---

## Parsing the Input

Split the story/lyrics by blank lines — each paragraph or labelled section = one scene.

Write one image prompt per scene. Label as Scene 1, Scene 2, etc.

---

## Image Prompt Format

Every prompt must follow this exact structure:

```
Scene [N]: Disney/Pixar style: [full visual description — characters, setting, mood, colours, composition]. [If Maya & Mala: "Both characters rendered at equal size."] Vibrant, polished, family-friendly 3D animation style, cinematic lighting, 16:9 widescreen.
```

**Rules:**
- Start every prompt with `Disney/Pixar style:`
- Focus on mood, colours, composition, and character expressions
- Rich, vibrant colours — warm and joyful palette
- Consistent character design across all scenes
- Family-friendly — no darkness, no fear, no violence
- One dominant visual focus per scene — don't overcrowd

---

## Scene Variety

Vary the settings and compositions across scenes:
- Close-up on faces for emotional moments
- Wide shots for landscapes or group scenes
- Action shots for movement (hopping, dancing, singing)
- Quiet moments for reflective or gentle beats

---

## Quality Check — Clear All Before Saving

- [ ] One prompt per scene — count matches the story/lyrics scene count
- [ ] Every prompt starts with `Disney/Pixar style:`
- [ ] Maya & Mala consistently described (if included): black pigtails / curly brown hair
- [ ] "Both characters rendered at equal size." present in every Maya & Mala scene
- [ ] Visual variety across adjacent scenes — no two identical compositions
- [ ] All prompts are family-friendly and age-appropriate
- [ ] 16:9 widescreen specified in every prompt

---

## Delivery

Post all prompts in chat for approval before saving.

Once approved:
1. Save to Drive in the episode folder as `02_image_prompts.txt`
2. Confirm with Drive link
3. Ask: *"Image prompts saved. Shall we move to video prompts?"*

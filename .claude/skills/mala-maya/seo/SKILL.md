---
name: mala-maya-seo
description: >
  YouTube SEO and thumbnail prompt skill for the Maya & Mala Kids channel.
  Produces a complete metadata package: title, description, timestamps, tags,
  hashtags, kids category settings, end screen suggestions, and a Grok thumbnail
  prompt — tuned for children's content and family-friendly YouTube search.
  Use this skill whenever the user asks for SEO, a title, a description, tags,
  a thumbnail prompt, or says "Step 3" in the Mala and Maya pipeline.
---

# 🎯 Maya & Mala Kids — SEO & Thumbnail Skill

One goal: **maximum clicks from parents and carers searching for children's content.**

---

## What This Skill Produces

| Output | What it is |
|---|---|
| **Title** | Keyword-rich, engaging, under 60 chars |
| **Description** | Story/song summary + scene timestamps |
| **Tags** | 10–15 relevant children's content tags |
| **Hashtags** | 5–8 hashtags for the description |
| **Category** | Kids & Family (set "Made for Kids" = Yes) |
| **End Screen Suggestions** | Related video recommendations |
| **Thumbnail Brief** | Visual concept for Grok image generation |
| **AI Thumbnail Prompt** | Ready-to-paste Grok prompt (16:9) |

Both files saved: `03_youtube_seo.txt` + `03_thumbnail_prompt.txt`

---

## Inputs

- Approved story or lyrics from Step 1
- Video title / topic

---

## Title Engineering

**Rules:**
- Under 60 characters
- Lead with the content type where helpful: "🐰 Hop Little Bunnies | ..."
- Include searchable keywords parents type: "nursery rhyme", "kids song", "children's story", "learn", "educational"
- Warm and inviting — not clickbait
- Emoji in title is fine for kids content (use sparingly, 1–2 max)

**Example patterns:**
- `Hop Little Bunnies 🐰 | Fun Nursery Rhyme for Kids`
- `Maya & Mala's Feelings Garden | Children's Story`
- `Body Parts Song for Kids 🎵 | Dance & Learn`

---

## Description

**Structure:**
1. First 2 lines: hook summary of the video (visible before "Show More")
2. Brief synopsis (2–3 sentences)
3. Timestamps for each scene/section
4. Tags line: `#MayaAndMala #KidsSongs #NurseryRhymes`
5. Channel subscribe prompt

**Timestamps format:**
```
0:00 Intro
0:30 [Scene/Section name]
1:15 [Scene/Section name]
...
```

Estimate timestamps proportionally from the total expected duration (7+ minutes, ~420 seconds) if exact timings aren't available.

---

## Tags

Mix of broad → specific → long-tail:

**Broad (always include):**
- nursery rhymes, kids songs, children's story, educational videos for kids, toddler songs

**Topic-specific:**
- Add 5–8 tags directly related to the video topic

**Channel-specific:**
- Maya and Mala, Maya Mala Kids, kids animation, Disney style kids video

---

## Audience Settings

Always set:
- **Made for Kids**: Yes
- **Category**: Kids & Family (ID: 20)
- **Language**: en-GB

---

## Thumbnail Brief

A strong kids thumbnail:
- Bright, saturated colours (yellows, oranges, blues, greens)
- Large expressive faces — exaggerated emotion (joy, surprise, delight)
- Clear subject, minimal clutter
- Title text overlay: large, bold, rounded font (white with dark outline)
- Maya & Mala visible if they appear in the video

**Thumbnail prompt format for Grok:**
```
Disney/Pixar style 3D animation: [scene description]. Bright vibrant colours, expressive faces, clean composition. Title text overlay: "[VIDEO TITLE]" in large bold rounded white font with dark outline, positioned at [top/bottom]. 16:9 widescreen, high resolution.
```

**Grok settings reminder:** grok.com/imagine → sign in with Google → paste prompt → ratio 16:9 → save as `thumbnail` in the episode Drive folder.

---

## Quality Check — Clear All Before Saving

- [ ] Title under 60 characters and contains searchable keywords
- [ ] First 2 description lines work as a standalone hook
- [ ] Timestamps cover all major scenes/sections
- [ ] "Made for Kids" noted clearly
- [ ] Tags move broad → specific → long-tail
- [ ] Thumbnail prompt is specific enough to produce a distinctive, clickable image
- [ ] Both files created: `03_youtube_seo.txt` and `03_thumbnail_prompt.txt`

---

## Delivery

Post the full package in chat for approval before saving.

Once approved:
1. Save to Drive as `03_youtube_seo.txt` (full package) and `03_thumbnail_prompt.txt` (raw prompt only)
2. Confirm with Drive links
3. Say: *"SEO saved. To generate the thumbnail: go to grok.com/imagine → paste the prompt → set ratio 16:9 → save as 'thumbnail' in the episode folder. Ready for audio when you are."*

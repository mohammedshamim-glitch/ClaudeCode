---
name: monkey-finance-trends
description: >
  Full YouTube Growth Strategist + SEO Expert skill for the Monkey Finance channel.
  Use this skill whenever Sham asks about trending finance topics, what video to make next,
  YouTube SEO research, content ideas, trend reports, competitor analysis, keyword research,
  or anything related to growing the Monkey Finance channel through data-driven content planning.
  Also trigger when he says "run a trend report", "what should I make next", "find me trending topics",
  "SEO research", "content ideas", "what's performing well", "gap analysis", or mentions wanting
  to plan upcoming videos for the finance channel. Always consult this skill before doing any
  YouTube trend or SEO research for Monkey Finance.
---

# 📊 Monkey Finance — Trends & SEO Skill

This skill turns you into a full YouTube Growth Strategist. Four steps. No fluff. Every recommendation backed by a real signal.

All execution detail is in the `references/` folder:
- **`trends/trends/references/RESEARCH.md`** — step-by-step research process for all 4 steps
- **`trends/trends/references/SCORING.md`** — opportunity scoring matrix and how to rank ideas
- **`trends/trends/references/BRIEF_TEMPLATE.md`** — full content brief format per video idea

**Always read `trends/trends/references/RESEARCH.md` first before starting any trend run.**

---

## Workflow at a Glance

```
Step 1: Competitor Intelligence  → yt-dlp: all competitor channels — recent uploads + top metadata + hidden tags
Step 2: Trend & Gap Sweep        → web search: what's hot now + gap analysis vs competitors simultaneously
Step 3: SEO + Audience Research  → keyword data + emotional triggers per shortlisted topic
Step 4: Score, Brief & Differentiate → yt-dlp transcripts + scoring + full content brief
```

---

## yt-dlp Integration

The `yt-dlp` MCP server is available in this project. Use it at two points in every trend run:

### Step 1 — Competitor Channel Sweep
Pull directly from each competitor channel listed in `trends/trends/references/RESEARCH.md`. Do not web search for competitor data — yt-dlp reads real YouTube numbers.

For each channel:
```
yt-dlp --dump-json --playlist-items 1-10 "https://www.youtube.com/@[ChannelHandle]/videos"
```
Extract: title, view count, upload date, duration, video URL.

For their top 1–2 performers (last 30 days), pull full metadata:
```
yt-dlp --dump-json "[video URL]"
```
Extract: tags array, description, exact view and like counts.

Also pull the hidden tags from top 2–3 competitor videos per shortlisted topic — these feed directly into the SEO package at Stage 6.

### Step 4 — Transcript Analysis (winning topic only)
For the top-ranked topic, download and analyse transcripts from the 2 best-performing competitor videos:
```
→ Download: auto-generated or manual subtitles (strip timestamps → clean text)
→ Analyse: hook structure (first 60s), section breakdown, analogies used, what they missed
```
Output a "competitive differentiation" note in the content brief: what angle they took, what they missed, what angle we take instead. Never copy their structure — use it to find the gap.

---

## Quick Reference

| Item | Value |
|---|---|
| Channel | Monkey Finance (Monkey See Money) |
| Channel scope | **General finance** — macro events, global markets, geopolitics + money, business stories, AND UK personal finance |
| Target audience | Financially curious adults 25–45, UK-based but global topics welcome |
| Content mix | ~60% general/macro finance, ~40% UK personal finance |
| Video format | 10–12 min explainer / whiteboard animation |
| Tone | Plain English, relatable, no jargon unless explained |
| Upload cadence | Weekly |
| Monetisation focus | AdSense CPM (finance = high CPM niche) + affiliate potential |

---

## Step Summary

| # | Step | What happens | Output |
|---|---|---|---|
| 1 | **Competitor Intelligence** | yt-dlp: all competitor channels — recent uploads, top performer metadata, hidden tags | Live view counts, gap classification, competitor tag list |
| 2 | **Trend & Gap Sweep** | Web search: what's trending + seasonal check + gap analysis vs Step 1 findings | Raw list of 10–15 candidate topics, gaps classified |
| 3 | **SEO + Audience Research** | Keyword research + title patterns + emotional triggers per shortlisted topic | SEO data and hook angles for top 5–8 topics |
| 4 | **Score, Brief & Differentiate** | Scoring matrix + yt-dlp transcript analysis on winner + full content brief | Ranked ideas + ready-to-use content brief |

---

## Opportunity Scoring Matrix (summary)

Each idea is scored out of 5 across these dimensions. Full rubric in `trends/trends/references/SCORING.md`.

| Dimension | What it measures |
|---|---|
| 🔍 Search Volume | How many people are searching for this topic |
| ⚔️ Competition Level | How hard it is to rank (lower = better for us) |
| 📈 Trend Velocity | Is this topic rising, peaking, or declining? |
| 💰 Monetisation Potential | CPM value, affiliate angle, product tie-in |
| 🎯 Channel Fit | Does it suit our format, tone, and audience? |

**Total score: X/25** — Top ideas score 18+. Anything under 12 is dropped.

---

## Evergreen Popular Topics

Always surface a set of **permanently popular finance topics** alongside trending ones. These generate steady views year-round with long shelf life.

Flag evergreen picks clearly as **EVERGREEN** and tag as **[MACRO]** or **[UK PERSONAL]** to keep the content mix balanced.

### General / Macro Finance (prioritise these)
| Category | Example angles |
|---|---|
| **Global markets** | Why markets crash, how recessions start, what a bear market means |
| **Central banks** | How the Fed/BoE sets rates, what quantitative easing actually is, money printing explained |
| **Geopolitics + money** | How wars move markets, oil price explained, petrodollar system, sanctions |
| **Trade & tariffs** | How tariffs work, who really pays them, trade war impact on everyday life |
| **Big business stories** | Company collapses, IPOs, hostile takeovers, short sellers explained |
| **Economic concepts** | Inflation explained simply, deflation, stagflation, GDP what it actually means |
| **Crypto & digital assets** | Bitcoin explained, stablecoins, why crypto crashes, CBDCs |
| **Banking system** | How banks create money, what happens when a bank fails, fractional reserve explained |
| **Wealth inequality** | Why the rich get richer, tax havens explained, billionaire economics |
| **Market mechanics** | Short selling, hedge funds, derivatives, dark pools explained simply |

### UK Personal Finance (supporting pillar)
| Category | Example angles |
|---|---|
| **Investing vs Property** | S&P 500 vs buying a house, index funds vs buy-to-let, stocks vs bricks |
| **ISA strategy** | Stocks & Shares ISA explained, ISA vs pension, maximising your ISA allowance |
| **Pension basics** | How much do I need to retire, SIPP vs workplace pension, pension drawdown explained |
| **Compound interest** | The power of starting early, compound interest explained simply |
| **Index funds** | Index funds for beginners, why most fund managers lose to the index |
| **Tax efficiency** | Capital gains tax explained, income tax bands UK, salary sacrifice |
| **First-time investing** | How to start investing with £100, best beginner investment platforms UK |

---

## Output Format

Deliver a clean **Trend Report** structured as:

1. **Competitor Snapshot** — table of all channels: recent top video, view velocity, gap identified, gap type
2. **Market Snapshot** — 3–4 sentences on what's dominating finance YouTube right now
3. **Top Trending Opportunities** — ranked list of 3–5 trending video ideas with scores
4. **Top Evergreen Opportunities** — ranked list of 2–3 always-popular ideas with scores and "why now" angle
5. **Full Content Brief** — one per idea across both lists (use `trends/trends/references/BRIEF_TEMPLATE.md`)
6. **One Recommended Next Video** — the single best pick with confidence rating and shelf-life indicator

---

## Critical Rules

- **Always use yt-dlp first** — run Step 1 before any web search. Real YouTube data beats inferred data every time.
- **Always use web search** — never rely on training data for trend research. Finance moves fast.
- **Prioritise recency** — focus on content published in the last 7–30 days unless researching evergreen.
- **Broad finance lens** — topics don't have to be UK-specific. Global macro, US markets, international events are all fair game.
- **UK relevance check** — for global topics, always note the UK angle where it exists.
- **Solo creator filter** — always check if big channels dominate. We need winnable ground.
- **No fluff** — every recommendation must be backed by a signal (search data, view count, trend graph, etc.)
- **Content mix** — across every 5 recommendations, aim for ~3 general/macro and ~2 UK personal finance.
- **Pipeline-ready** — the winning topic from this report passes directly to Stage 2 (scriptwriting).

---

## How to Start a Trend Run

1. Read `trends/trends/references/RESEARCH.md` — follow the 4-step process.
2. Run all 4 steps in order.
3. Produce the full Trend Report at the end.
4. Ask Sham: *"Want to run the pipeline with the top pick?"*

---

*Research process: `trends/trends/references/RESEARCH.md`. Scoring rubric: `trends/trends/references/SCORING.md`. Brief format: `trends/trends/references/BRIEF_TEMPLATE.md`.*

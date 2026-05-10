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

This skill turns you into a full YouTube Growth Strategist. It researches what's trending in finance right now, analyses the SEO landscape, identifies gaps you can win, and produces a ranked content brief ready to feed straight into the pipeline.

All execution detail is in the `references/` folder:
- **`references/RESEARCH.md`** — step-by-step research process, search queries, signal sources
- **`references/SCORING.md`** — opportunity scoring matrix and how to rank ideas
- **`references/BRIEF_TEMPLATE.md`** — full content brief format per video idea

**Always read `references/RESEARCH.md` first before starting any trend run.**

---

## Workflow at a Glance

```
Phase 0: YouTube Live Data     → yt-dlp search: real view counts, tags, upload dates
Phase 1: Trend Sweep           → find what's hot RIGHT NOW in finance (last 7–30 days)
Phase 2: SEO Deep Dive         → keywords, titles, tags, length, competition
Phase 2E: Competitor Tag Pull  → yt-dlp: exact hidden tags from top 5 competing videos
Phase 3: Gap Analysis          → high demand + weak competition = your opportunity
Phase 4: Audience Signals      → emotional triggers, comment sentiment, algorithm cues
Phase 4C: Transcript Analysis  → yt-dlp: pull + analyse top 2 competitor scripts on topic
Phase 5: Scoring & Ranking     → score each idea on 5-point matrix
Phase 6: Content Brief Output  → full brief per top idea, ready for pipeline
```

---

## yt-dlp Integration — How to Use It

The `yt-dlp` MCP server is available in this project. Use it at three points in every trend run:

### Phase 0 — Competitor Channel Sweep (run before Phase 1)
Pull directly from each competitor channel listed in `references/RESEARCH.md` using yt-dlp. Do not web search — yt-dlp reads real YouTube data.

For each channel, fetch their 10 most recent uploads and extract:
- Title, view count, upload date, duration

Then for their top 1–2 performers (last 30 days), pull full metadata:
- Tags array, description, exact view and like counts

This tells you what topics are being pushed by the algorithm right now, what's performing, and — most importantly — what gaps the competitors have left open. The gap analysis IS the content brief. Feed these findings directly into Phase 1.

### Phase 2E — Competitor Tag Pull (run after shortlisting)
Once you have 3–5 candidate topics, pull hidden tags from the top 2 competitor videos per topic:

```
For each competing video URL:
→ Extract: tags, description, exact title, view count
```

Tags are invisible to regular users but yt-dlp reads them directly. This data feeds straight into the SEO package at Stage 5.

### Phase 4C — Transcript Analysis (run on the winning topic before finalising brief)
For the top-ranked topic, download and analyse the transcript of the 2 best-performing competitor videos:

```
For each competitor video:
→ Download: auto-generated or manual subtitles (strip timestamps → clean text)
→ Analyse: hook structure (first 60 seconds), section breakdown, analogies used, what they missed
```

Output a brief "competitive differentiation" note in the content brief:
- What angle the competitors took
- What they didn't cover or got wrong
- The angle Monkey See Money should take to be clearly different and better

**Never copy their structure. Use it to find the gap.**

---

## Quick Reference

| Item | Value |
|---|---|
| Channel | Monkey Finance (Monkey See Money) |
| Channel scope | **General finance** — macro events, global markets, geopolitics + money, business stories, AND UK personal finance. Not exclusively UK personal finance. |
| Target audience | Financially curious adults 25–45, UK-based but global topics welcome |
| Content mix | ~60% general/macro finance, ~40% UK personal finance |
| Video format | 10–12 min explainer / whiteboard animation |
| Tone | Plain English, relatable, no jargon unless explained |
| Upload cadence | Weekly |
| Monetisation focus | AdSense CPM (finance = high CPM niche) + affiliate potential |

---

## Phase Summary

| # | Phase | What happens | Output |
|---|---|---|---|
| 0 | **Competitor Channel Sweep** | yt-dlp: pull latest 10 uploads + top performer metadata from each competitor channel | Real view counts, tags, and gap analysis per channel |
| 1 | Trend Sweep | Web search YouTube + Google Trends + Reddit + news | Raw list of 15–20 candidate topics |
| 1E | Evergreen Sweep | Research always-popular UK finance topics with sustained demand | Raw list of 8–10 evergreen candidates |
| 2 | SEO Deep Dive | Keyword research, title patterns, video length, tags | SEO data per topic |
| 2E | **Competitor Tag Pull** | yt-dlp: extract hidden tags from top competing videos | Exact tags competitors rank for |
| 3 | Gap Analysis | Competition check, authority dominance, underserved angles | Shortlist of 5–8 winnable ideas |
| 4 | Audience Signals | Emotional triggers, comment sentiment, algorithm cues | Hook angles per idea |
| 4C | **Transcript Analysis** | yt-dlp: download + analyse top 2 competitor scripts on winning topic | Competitive differentiation note for brief |
| 5 | Scoring & Ranking | Score each idea on matrix (see SCORING.md) | Ranked top 3–5 ideas |
| 6 | Content Brief | Full brief per idea including competitive differentiation note | Ready-to-use content briefs |

---

## Opportunity Scoring Matrix (summary)

Each idea is scored out of 5 across these dimensions. Full rubric in `references/SCORING.md`.

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

In addition to trending topics, always surface a set of **permanently popular finance topics** — videos that get steady views year-round regardless of news cycles. These are lower-risk bets with long shelf life and consistent search demand.

Run Phase 1E (see `references/RESEARCH.md`) alongside the trend sweep. Score evergreen topics on the same matrix — note that Trend Velocity scores lower (by design) but Search Volume and Monetisation often score higher.

**Seed list — always check these categories for fresh angles:**

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

When surfacing an evergreen pick, flag it clearly as **EVERGREEN** and tag it as either **[MACRO]** or **[UK PERSONAL]** so the content mix stays balanced.

---

## Output Format

Deliver a clean **Trend Report** structured as:

1. **Market Snapshot** — 3–4 sentences on what's dominating finance YouTube right now
2. **Top Trending Opportunities** — ranked list of 3–5 trending video ideas with scores
3. **Top Evergreen Opportunities** — ranked list of 2–3 always-popular ideas with scores and "why now" angle
4. **Full Content Brief** — one per idea across both lists
5. **One Recommended Next Video** — the single best pick (trending or evergreen) with confidence rating and shelf-life indicator

---

## Critical Rules

- **Always use yt-dlp** — run Phase 0 before any web search. Real YouTube data beats inferred data every time.
- **Always use web search** — never rely on training data for trend research. Finance moves fast.
- **Prioritise recency** — focus on content published in the last 7–30 days unless researching evergreen.
- **Broad finance lens** — topics don't have to be UK-specific. Global macro, US markets, international events are all fair game if they're explainable simply and relevant to a financially curious audience.
- **UK relevance check** — for global topics, always note the UK angle or impact where it exists, but don't reject a topic just because it's not UK-only.
- **Solo creator filter** — always check if big channels dominate. We need winnable ground.
- **No fluff** — every recommendation must be backed by a signal (search data, view count, trend graph, etc.)
- **Content mix** — across every 5 recommendations, aim for ~3 general/macro and ~2 UK personal finance. Never all one type.
- **Pipeline-ready** — the winning topic from this report should be passable directly to Stage 1 of the pipeline.

---

## How to Start a Trend Run

1. Read `references/RESEARCH.md` — follow the search strategy step by step.
2. Run all 6 phases in order.
3. Produce the full Trend Report at the end.
4. Ask Sham: *"Want to run the pipeline with the top pick?"*

---

*Research process: `references/RESEARCH.md`. Scoring rubric: `references/SCORING.md`. Brief format: `references/BRIEF_TEMPLATE.md`.*

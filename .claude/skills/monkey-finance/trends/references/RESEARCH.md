# RESEARCH.md — Trend Research Process

Four steps. Run them in order. Never skip a step. Never rely on training data — finance moves fast.

---

## Before You Start — Seasonal Check

Check today's date and identify which seasonal window applies. Being early is worth 10× the views of being late.

| Month(s) | Event | Top content angles |
|---|---|---|
| **Jan–Mar** | ISA season build-up | "Max your ISA before April", "ISA vs pension 2026", "best Stocks & Shares ISA UK", "ISA deadline explained" |
| **Mar** | Spring Statement / Budget | "Budget explained in plain English", "what the budget means for your money", "winners and losers" |
| **Apr** | Tax year end → new year | "New tax year changes", "what changes in April", "capital gains tax year end", "use it or lose it" |
| **Apr–May** | Post-ISA / new allowances reset | "New ISA allowance 2026", "pension contribution limits", "dividend allowance changes" |
| **Jun–Aug** | Summer — lower news cycle | Evergreen wins here: compound interest, index funds, emergency fund, debt payoff |
| **Sep–Oct** | Back to basics season | "Start investing", "first ISA", "pension review", beginner content performs well |
| **Nov** | Autumn Statement | Same as Spring Budget — "what the statement means for your wallet" |
| **Dec** | Year-end tax planning | "Use your allowances before April", "salary sacrifice before year end", "pension top-up" |
| **Ongoing** | Bank of England MPC meetings | Rate decisions → mortgage content spikes every 6 weeks |
| **Ongoing** | Inflation data releases | CPI/RPI releases → savings rate content, real returns content |

If we're within 6 weeks of a major event — **prioritise time-sensitive content above everything else.** A video 3 weeks before the ISA deadline outperforms the same video after by 5–10×.

---

## Step 1: Competitor Intelligence

**Goal:** Know exactly what the top UK finance channels have published in the last 30 days, what's performing, and — most importantly — what gaps they've left open.

**Method: yt-dlp only. No web search for this step.**

### Channels to Track

| Channel | Handle | Why they matter |
|---|---|---|
| **Damien Talks Money** | @DamienTalksMoney | Closest competitor — similar relatable style, overlapping audience |
| **James Shack** | @JamesShack | High-production investing content, strong SEO |
| **Toby Newbatt** | @TobyNewbatt | UK FIRE/investing, consistent uploader, good search traffic |
| **Be Clever With Your Cash** | @BeCleverWithYourCash | Deals/savings, very high search traffic |
| **Pensioncraft** | @Pensioncraft | Pension specialist — deep content, engaged audience |
| **Casual Finance** | @CasualFinance | Direct niche overlap |
| **MonkeyExplains** | @MonkeyExplains | Similar animated/explainer format |
| **Primate Economics** | @PrimateEconomics | Possible direct competitor given name |
| **Wealth Logic** | @WealthLogic | UK finance content |

### What to Pull

For each channel, fetch their 10 most recent uploads:
```
yt-dlp --dump-json --playlist-items 1-10 "https://www.youtube.com/@[Handle]/videos"
```

Extract per video: title, upload date, view count, duration, video URL.

For their top 1–2 performers (highest views, uploaded in last 30 days), pull full metadata:
```
yt-dlp --dump-json "[video URL]"
```
Extract: tags array, description, exact view count, like count.

### Three Questions to Answer

**1. What have they published in the last 30 days?**
List all uploads. This shows what topics are being fed to the algorithm right now.

**2. What's their top-performing video this month?**
High view velocity = algorithm is pushing it = topic is hot. If you can make a better version, do it now.

**3. What have they NOT covered?**
Scan their last 30–50 videos. Find:
- Topics ignored entirely
- Angles that leave obvious follow-up questions unanswered
- UK-specific versions of US topics nobody has done
- Old videos (2+ years) on topics still being searched — the refresh opportunity

### Gap Classification

Label each competitor gap as:

| Type | What it means |
|---|---|
| 🟥 **Hard gap** | Nobody has covered this topic at all — first mover wins |
| 🟧 **Angle gap** | Topic covered but only from one angle — your different take wins |
| 🟨 **Quality gap** | Topic covered but badly — your better version wins |
| 🟩 **Refresh gap** | Topic covered 2+ years ago — new video wins on recency |

Prioritise 🟥 and 🟧 first.

### Step 1 Output

```
## Competitor Snapshot

| Channel | Recent top video | View velocity | Gap identified | Gap type |
|---------|-----------------|---------------|----------------|----------|
| Damien Talks Money | [title] | [views/day] | [gap] | 🟥/🟧/🟨/🟩 |
| James Shack | ... | ... | ... | ... |
...

**Biggest gap this week:** [One sentence — the clearest opportunity the competitors have left open]
```

Also save the hidden tags from Step 1 top performers — these feed into Step 3 SEO research and Stage 6.

---

## Step 2: Trend & Gap Sweep

**Goal:** Build a raw list of 10–15 candidate finance topics trending right now, cross-referenced against the gaps identified in Step 1.

**Method: web search.**

### 2a — YouTube Trend Signals
Run these searches. Note top results (title, views, upload date, channel size):
- `finance youtube trending [current month] 2026`
- `"personal finance" youtube most viewed this week`
- `"investing" youtube viral 2026`
- `"economy explained" youtube trending 2026`
- `best performing finance youtube videos [current month]`

Note per result: topic, view velocity (views ÷ days), channel sub count (flag if under 100k — winnable), evergreen or timely.

### 2b — Google Trends + News Check
- `google trends finance topics rising 2026`
- `finance news UK trending [current month]`
- `reddit UKPersonalFinance hot posts this week`
- `BBC news personal finance [current month] 2026`

Look for topics with a rising trajectory — not already peaked. Reddit and news validate real-world conversation volume.

### 2c — Evergreen Sweep
Run alongside the trend search to find topics with sustained year-round demand:
- `most searched personal finance topics UK`
- `top finance youtube videos all time UK`
- `investing basics youtube most views UK`

For any evergreen candidate, check: `"[topic]" youtube 2023 OR 2024 OR 2025`
- Top videos 2+ years old? → **Refresh opportunity**
- US-focused? → **UK angle opportunity**
- Long and dense? → **Accessible plain-English opportunity**

### 2d — Gap Cross-Reference
For each candidate topic from 2a–2c, check it against the Step 1 competitor gaps:
- Does this topic map to a 🟥 or 🟧 gap? → Move to shortlist immediately
- Is it already well-covered by a competitor with high view velocity? → Lower priority
- Does it combine a trending signal AND a competitor gap? → Top priority

### Step 2 Output

Raw candidate list:
```
Topic | Source | Trending signal | Competitor gap? | Evergreen or Timely
```

Shortlist of 5–8 topics to take forward to Step 3.

---

## Step 3: SEO + Audience Research

**Goal:** For each shortlisted topic, gather keyword data, title patterns, and the emotional angle that will make it click.

Work through each shortlisted topic from Step 2.

### 3a — Keyword Research

For each topic, search:
- `"[topic]" youtube keyword search volume`
- `best keywords for "[topic]" youtube 2025`
- `"[topic]" related searches google`

Identify:
- **Primary keyword** — the main search term
- **Secondary keywords** — 3–5 supporting terms
- **Long-tail variants** — specific questions people search (great for titles)

Blend these with the competitor tags pulled in Step 1.

### 3b — Title Pattern Analysis

Search top videos on the topic and identify:
- Common title formulas (e.g. "X Things You Need to Know About...", "Why [Topic] is About to Change")
- Power words appearing frequently (e.g. "Warning", "Mistake", "Secret", "Explained")
- Use of numbers (listicles perform well in finance)
- Optimal title length (aim for 60 chars or under)

### 3c — Competition Check

For each topic:
- How many videos exist on this exact topic?
- Are the top results from channels with 500k+ subscribers? (if yes = hard to crack without a specific angle)
- Are there videos from smaller channels in top results? (if yes = opportunity)
- When were the top videos uploaded? (if 2+ years ago = refresh opportunity)

### 3d — Emotional Trigger

Finance content performs on these emotions. Identify which applies to each topic:
- 😨 **Fear** — "You're losing money if you don't know this"
- 🤑 **Greed/Aspiration** — "How to make your money work harder"
- 😤 **Frustration** — "Why your bank is ripping you off"
- 😮 **Curiosity** — "The secret most people don't know about ISAs"
- 😅 **Relief/Urgency** — "It's not too late to start investing"

### Step 3 Output

Per shortlisted topic:
```
Topic | Primary keyword | Secondary keywords | Best title formula | Emotional trigger | Competition level
```

---

## Step 4: Score, Brief & Differentiate

**Goal:** Score all shortlisted topics, identify the winner, analyse competitor transcripts on the winning topic, and produce the full content brief.

### 4a — Score All Topics

Apply the Opportunity Scoring Matrix from `references/SCORING.md` to each shortlisted topic.

```
| Idea | Search Vol | Competition | Trend Velocity | Monetisation | Channel Fit | TOTAL |
|------|-----------|-------------|----------------|--------------|-------------|-------|
```

Drop anything under 12/25. Rank the rest.

### 4b — Transcript Analysis (winning topic only)

For the top-ranked topic, use yt-dlp to download transcripts from the 2 best-performing competitor videos:
```
yt-dlp --write-auto-sub --skip-download --sub-format vtt "[video URL]"
```
Strip timestamps → clean text. Analyse:
- Hook structure (first 60 seconds)
- Section breakdown and pacing
- Analogies and examples used
- What they missed or got wrong

Output a "competitive differentiation" note:
- What angle the competitors took
- What they didn't cover or glossed over
- The angle Monkey See Money should take to be clearly different and better

**Never copy their structure. Use it to find the gap.**

### 4c — Full Content Brief

Produce one full brief per top-ranked idea using `references/BRIEF_TEMPLATE.md`. The brief for the winning topic must include the competitive differentiation note from 4b.

### Step 4 Output — Full Trend Report

Deliver the complete Trend Report:

1. **Competitor Snapshot** — table from Step 1
2. **Market Snapshot** — 3–4 sentences on what's dominating finance YouTube right now
3. **Top Trending Opportunities** — ranked list of 3–5 trending ideas with scores
4. **Top Evergreen Opportunities** — ranked list of 2–3 evergreen ideas with scores and "why now" angle
5. **Full Content Briefs** — one per idea
6. **Recommended Next Video** — the single best pick, confidence rating, shelf-life indicator

Then ask Sham: *"Want to run the pipeline with the top pick?"*

# 🤖 Agents & Orchestration — *Etsy Market Research Scraper*

This document defines the agent architecture, responsibilities, data contracts, and runbook that power the Etsy Market Research Scraper. It’s designed so you (or contributors) can extend/replace pieces without breaking the pipeline.

> TL;DR: One orchestrator coordinates a set of focused agents: **Seeds ➝ Autocomplete ➝ Etsy Analysis ➝ Trends ➝ (Amazon/Social optional) ➝ Scoring ➝ Reporting**, with robust rate-limiting, retries, and checkpointing.

---

## 1) System Overview

```
[SeedManager]
     │ seeds
     ▼
[AutocompleteAgent] ──► suggestions
     │
     ▼
[EtsyAnalyzer] ──► listing_count, price stats, category, competition_level
     │
     ├──► (optional) [AmazonAnalyzer]
     │
     └──► (optional) [SocialSignalsAgent]
     │
     ▼
[TrendsAgent] ──► trend_score, trend_direction
     │
     ▼
[ScoringAgent] ──► opportunity_score, recommendation
     │
     ▼
[Reporter] ──► CSV, summary.txt
     │
     ▼
[Checkpoint & Persistence]
```

**Cross-cutting services:** `RateLimiter`, `RetryPolicy`, `Logger`, `StateStore`.

---

## 2) Agent Index (at a glance)

| Agent                        | Purpose                                               | Key Inputs            | Key Outputs                                                            |
| ---------------------------- | ----------------------------------------------------- | --------------------- | ---------------------------------------------------------------------- |
| `SeedManager`                | Provide initial seeds (from built-ins or file)        | seeds file / defaults | seed strings                                                           |
| `AutocompleteAgent`          | Expand seeds via Etsy autocomplete                    | seed                  | suggestions\[]                                                         |
| `EtsyAnalyzer`               | Get listing count, price stats, category, competition | seed/suggestion       | listing\_count, avg\_price, price\_range, category, competition\_level |
| `TrendsAgent`                | Google Trends metrics & direction                     | term                  | trend\_score, trend\_direction                                         |
| `AmazonAnalyzer` *(opt)*     | Validate cross-market demand                          | term                  | amazon\_count/range (optional fields)                                  |
| `SocialSignalsAgent` *(opt)* | Directional demand from social                        | term                  | social\_score/notes (optional fields)                                  |
| `ScoringAgent`               | Compute `opportunity_score` & recommendation          | all features          | score, recommendation string                                           |
| `Reporter`                   | Write CSV + summary                                   | records\[]            | `etsy_market_research.csv`, `opportunity_summary.txt`                  |
| `Checkpoint`                 | Save/restore progress                                 | run state             | `scraping_checkpoint.json`                                             |
| `Logger`                     | Structured logs + screenshots on failure              | events                | `scraping_log.txt`, `etsy_*png`                                        |
| `RateLimiter`                | Human-like pacing                                     | policy                | backoff delays                                                         |

---

## 3) Orchestrator (Runner)

**Responsibilities**

* Parse CLI flags (`--resume`, `--headless`, `--delay`, `--no-trends`, `--no-etsy-analysis`, `--enable-amazon`, `--enable-social`).
* Initialize services (`RateLimiter`, `Logger`, `Checkpoint`).
* Stream seeds → expand → enrich → score → persist.
* Handle **resume** by reading `scraping_checkpoint.json` and continuing from last processed `(seed, suggestion)` pair.

**Pseudo-flow**

1. Load seeds from `SeedManager`.
2. For each **seed**:

   * `AutocompleteAgent` → `suggestions`.
   * For each **suggestion** (deduped):

     * `EtsyAnalyzer` (unless `--no-etsy-analysis`).
     * `TrendsAgent` (unless `--no-trends`).
     * Optional: `AmazonAnalyzer` & `SocialSignalsAgent`.
     * `ScoringAgent` → `opportunity_score`, `recommendation`.
     * Persist row to CSV (append) and checkpoint progress.
3. After all work: `Reporter` compiles `opportunity_summary.txt`.

**Resilience**

* Each agent call goes through `RetryPolicy(max_retries=CONFIG.max_retries, backoff=exp)` and `RateLimiter(min_delay, max_delay)`.
* Any hard failure emits a structured log and screenshot (for UI selectors).

---

## 4) Agent Specs

### 4.1 `SeedManager`

**Purpose:** Provide well-curated initial seeds + load user seeds from file/env.

* **Inputs:** `seeds.txt` (optional), built-in curated seeds (see README categories)
* **Outputs:** Iterator of `seed: str`
* **Notes:** Deduplicate, normalize (lowercase/trim), drop overly generic seeds (e.g., `"gift"`, `"personalized"`).
* **Errors:** Missing file → fallback to defaults; log a `WARN`.

---

### 4.2 `AutocompleteAgent`

**Purpose:** Expand each seed using Etsy’s search autocomplete (via Playwright).

* **Inputs:** `seed: str`
* **Outputs:** `suggestions: List[str]` (unique, filtered)
* **Key Fields:** `timestamp_utc`, `seed`, `suggestion`
* **Implementation Notes:**

  * Navigate to Etsy home, focus search, type slowly with jitter.
  * Scrape dropdown list items; if no list, try “results page related searches.”
  * Respect `RateLimiter`; screenshot failures to `etsy_debug_*.png`.
* **Errors:** If selectors change: log CSS/XPath attempted; save `etsy_debug_*`.

---

### 4.3 `EtsyAnalyzer`

**Purpose:** For a term, collect listing counts, price stats, category hints, and **competition level**.

* **Inputs:** `term: str`
* **Outputs:**

  * `listing_count: int`
  * `avg_price: float`
  * `price_range: str` (e.g., `"12.99–49.00"`)
  * `category: str`
  * `competition_level: str` in `{low, moderate, high}` (see rule below)
* **Competition Rule (baseline heuristic):**

  * `listing_count < 1,000` → `low`
  * `1,000–10,000` → `moderate`
  * `>10,000` → `high`
* **Notes:** Pull from search results header and first 48 items for price sampling. Remove outliers via IQR or trimmed mean (5–10%).
* **Errors:** If blocked or 0 results, retry with backoff; log and continue.

---

### 4.4 `TrendsAgent`

**Purpose:** Google Trends metrics and direction.

* **Inputs:** `term: str`
* **Outputs:**

  * `trend_score: float` (0–100 averaged last 12 months)
  * `trend_direction: str` in `{growing, declining, stable}`
* **Direction Rule:**
  Fit simple linear regression last 12 months weekly interest: slope > +ε → `growing`; slope < −ε → `declining`; else `stable`. Choose ε so that noise doesn’t flip direction (e.g., 0.15×std).

---

### 4.5 `AmazonAnalyzer` *(optional)*

**Purpose:** Sanity-check cross-market demand.

* **Inputs:** `term`
* **Outputs (optional fields in CSV):** `amazon_listing_count`, `amazon_avg_price`, `amazon_price_range`
* **Notes:** Only included if `--enable-amazon`.

---

### 4.6 `SocialSignalsAgent` *(optional)*

**Purpose:** Directional relevance signals from social (e.g., counts/velocity).

* **Inputs:** `term`
* **Outputs:** `social_score: float` (0–1), `social_notes: str`
* **Notes:** Lightweight heuristics; off by default (`--enable-social`).

---

### 4.7 `ScoringAgent`

**Purpose:** Convert features into `opportunity_score` and a clear `recommendation`.

* **Inputs:**
  `competition_level`, `listing_count`, `trend_score`, `trend_direction`, `avg_price`, `price_range`, `(optional) amazon/social`

* **Outputs:**

  * `opportunity_score: float` (open scale; your README bins apply)
  * `recommendation: str` (one of the preset labels in README)

* **Baseline Formula (tunable):**

  ```
  comp_component =
    { low: +3.0, moderate: +1.0, high: -2.0 }

  trend_component = (trend_score / 20)     # max +5 if score ≈100
  direction_bonus = { growing: +1.5, stable: 0, declining: -1.0 }

  price_component = min( 2.0, log1p(avg_price)/log(30) )  # favors niches w/ room

  dispersion_bonus = clamp( (max_price - min_price)/max_price, 0, 1.0 ) * 1.0
                    # higher dispersion leaves room to position premium variants

  # Optional extras (very lightweight influence):
  amazon_component = present ? +0.5 : 0
  social_component = social_score * 0.5

  opportunity_score = comp_component
                    + trend_component
                    + direction_bonus
                    + price_component
                    + dispersion_bonus
                    + amazon_component
                    + social_component
  ```

* **Binning (per README):**
  `>= 5` → **HIGH**; `2–4` → **GOOD**; `0–1` → **MODERATE**; `<0` → **AVOID**
  **Perfect Opportunity** if `competition_level=low` **and** `trend_direction=growing`.

* **LLM Prompt (if using an LLM to post-process text labels only):**

  * *System:* “You score Etsy niches using structured features. Be conservative, profit-oriented, and penalize saturation.”
  * *User (JSON):* `{"competition_level":"low","trend_score":78,"trend_direction":"growing","listing_count":847,"avg_price":24.5,"price_range":"12.99–49.00"}`
  * *Assistant:* `{"opportunity_score":7.2,"recommendation":"🔥 PERFECT OPPORTUNITY - Low Competition + Growing Trend"}`

---

### 4.8 `Reporter`

**Purpose:** Persist rows to `etsy_market_research.csv` and generate `opportunity_summary.txt`.

* **CSV Columns (must match README):**
  `timestamp_utc, seed, suggestion, competition_level, opportunity_score, trend_score, trend_direction, listing_count, avg_price, price_range, category, recommendation`
* **Summary Rules:**

  * Top 10 **high-opportunity** (score ≥ 5)
  * Top 10 **good-opportunity** (2–4)
  * Category breakdown (mean score, count, median price)
  * Action notes: “Prioritize HIGH with *growing*, listing\_count < 1,000; validate price bands.”

---

## 5) Cross-Cutting Components

### 5.1 `RateLimiter`

* **Policy:** random jitter between `CONFIG.min_delay`–`CONFIG.max_delay`, plus extra backoff on repeated requests to the same origin.
* **Respect:** `--delay N` overrides both min/max (fixed sleep N).

### 5.2 `RetryPolicy`

* **Config:** `max_retries=CONFIG.max_retries`, exponential backoff (e.g., 1.5×).
* **On last failure:** emit structured error + screenshot if browser-bound.

### 5.3 `Logger`

* **File:** `scraping_log.txt`
* **Format (JSON-per-line):**
  `{ "ts":"...", "agent":"EtsyAnalyzer", "seed":"...", "suggestion":"...", "level":"INFO|WARN|ERROR", "msg":"...", "meta":{...} }`
* **Screenshots:**

  * `etsy_debug_*.png` for selector failures
  * `etsy_search_results_*.png` for confirmation snapshots

### 5.4 `Checkpoint & StateStore`

* **File:** `scraping_checkpoint.json`
* **Schema (example):**

  ```json
  {
    "version": 1,
    "last_seed_index": 12,
    "processed": { "vintage botanical prints": ["botanical wall art","vintage plant poster"] },
    "pending_suggestions": [],
    "run_flags": { "no_trends": false, "no_etsy_analysis": false, "enable_amazon": false, "enable_social": false }
  }
  ```

---

## 6) Data Contracts (Strict)

### 6.1 CSV Types

* `timestamp_utc` → ISO string
* `seed`/`suggestion`/`category`/`competition_level`/`trend_direction`/`recommendation` → `str`
* `listing_count` → `int`
* `avg_price` → `float` (2 decimals)
* `price_range` → `str` `"min–max"` (keep en dash or hyphen consistently)
* `trend_score`/`opportunity_score` → `float` (one decimal ok)

### 6.2 Summary File Sections (ordered)

1. `Top 10 — High Opportunity`
2. `Top 10 — Good Opportunity`
3. `Category Breakdown`
4. `Insights & Recommendations`

---

## 7) Configuration Reference

Mirrors your README:

```python
CONFIG = {
  "min_delay": 2,
  "max_delay": 8,
  "max_retries": 3,
  "timeout": 15000,
  "enable_google_trends": True,
  "enable_etsy_analysis": True,
  "enable_amazon_analysis": False,
  "enable_social_analysis": False,
}
```

**CLI → Config mapping**

* `--delay 5` → sets both `min_delay=max_delay=5`
* `--no-trends` → `enable_google_trends=False`
* `--no-etsy-analysis` → `enable_etsy_analysis=False`
* `--enable-amazon` → `enable_amazon_analysis=True`
* `--enable-social` → `enable_social_analysis=True`
* `--headless` → Playwright launch arg
* `--resume` → read checkpoint on start

---

## 8) Implementation Notes (Playwright/Etsy)

* **Selectors:** Target both the **search input** and **autocomplete list**; fall back to **related searches** on the results page. Keep selectors in one module for hot-patching.
* **Typing Strategy:** Type with 50–120ms random delays, insert a brief pause after last character before scraping.
* **Localization:** Pin interface language to English if possible to keep selectors predictable.
* **Sampling:** For price stats, scroll to load at least 48 items; parse numeric price, drop “Ad” and “Variant from” noise.

---

## 9) Testing & QA

* **Unit:**

  * Parser extracts listing counts from sample HTML fixtures.
  * Price stats handle weird formats and currency symbols.
  * ScoringAgent formula returns expected bins on canned inputs.
* **Integration:**

  * Dry-run with `--delay 5 --no-trends` processes ≥ 20 seeds without error.
  * Resume: kill mid-run, re-start with `--resume` matches final CSV row count.
* **Smoke:**

  * Trend slope sign correct on known rising/declining terms.

---

## 10) Privacy, ToS, & Safety

* Emulate **human-like** access with sensible delays.
* Respect robots policies and platform ToS.
* Do not store PII.
* Rate-limit aggressively if you see captchas or throttle signals.

---

## 11) Extensibility Points

* **Add a Source:** Implement `Analyzer` with `analyze(term)->dict` and register in orchestrator pipeline order.
* **Replace Scoring:** Swap weight map in `ScoringAgent` or inject from `weights.json`.
* **New Outputs:** Add columns to CSV and reflect in `Reporter` & README.

---

## 12) Example End-to-End Trace

1. `seed="vintage botanical prints"`
2. `AutocompleteAgent` → `["botanical wall art","vintage plant poster", …]`
3. For `"botanical wall art"`:

   * `EtsyAnalyzer` → `listing_count=847`, `avg_price=24.5`, `price_range="12.99–49.00"`, `category="Art & Collectibles"`, `competition_level="low"`
   * `TrendsAgent` → `trend_score=78`, `trend_direction="growing"`
   * `ScoringAgent` → `opportunity_score=7.2`, `recommendation="🔥 PERFECT OPPORTUNITY - Low Competition + Growing Trend"`
   * `Reporter` appends CSV row; `Checkpoint` updates processed pair.

---

## 13) Runbook (Operator Quick-Start)

**Fresh run (safe test):**

```bash
python etsy_autocomplete.py --delay 5
```

**Long run (recommended):**

```bash
python etsy_autocomplete.py --delay 6 --headless --resume
```

**Faster but less data:**

```bash
python etsy_autocomplete.py --no-trends
```

**Troubleshooting**

* Selector fail → check `etsy_debug_*.png` + `scraping_log.txt`
* Throttled → increase `--delay` to `8–12`
* Crash mid-run → `--resume` continues from last pair

---

## 14) Contributor Checklist

* [ ] Keep selectors centralized and documented.
* [ ] Never change CSV headers without bumping version and updating README.
* [ ] Add tests for any new analyzer or scoring weight change.
* [ ] Validate summary sections render stable ordering (tie-break by score, then listing\_count asc).
* [ ] Confirm `--resume` works before merging.

---

## 15) Field Guide: Turning Outputs into \$\$ (for operators)

* **Start with `opportunity_score ≥ 5` AND `trend_direction=growing`.**
* **Prefer `listing_count < 1,000`.** If `1,000–10,000`, look for **price dispersion** (room to premium-position).
* **Manually verify top 10** terms on Etsy: check first page design sameness → if homogenous, your unique angle can cut through.
* **Run quick mockups** for 3–5 best terms; test with 1–2 listings each; measure CTR & saves in first 72 hours.

---

**End of `agents.md`.**

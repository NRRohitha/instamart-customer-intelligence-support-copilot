# Agent Guide — Instamart Customer Intelligence & Support Copilot

This file is the operating manual for any coding agent working in this repository. Read it before touching code, then read `PLAN.md`, then `TRACKER.md`. The authoritative assignment text is `docs/ASSIGNMENT_BRIEF.md`.

## 1. Mission

Implement the four connected Parts of the capstone so that a grader can clone the public repo, run the README's numbered commands in order, and reproduce every checkpoint:

- Part A: clean the raw exports, build `data/clean/*.csv` and `data/instamart.db`, answer seven SQL questions, do the pandas EDA.
- Part B: RFM segments, K-means, PCA, leak-free lapse model, retention list.
- Part C: privacy-safe ticket triage with guardrails, retries, validation, budget and routing.
- Part D: chunked TF-IDF policy RAG and a ReAct refund agent with safe stops and resume.

## 2. Hard constraints (non-negotiable)

1. `generate_data.py` and `mock_llm.py` must remain byte-for-byte unchanged at the repo root.
   - `generate_data.py` SHA-256: `e5bd939dfa40402281d0285bdf755d3b75f42159265d78098e248e58683de6cd`
   - `mock_llm.py` SHA-256: `77bf9bb7cb96e67f49d808cb2e84befb0e5a346833cd508df924437b606905b6`
   - Verify with `Get-FileHash -Algorithm SHA256 generate_data.py, mock_llm.py`. If a hash differs, restore the file from `docs/ASSIGNMENT_BRIEF.md`; do not "fix" it.
2. Use only the Python standard library plus `pandas`, `numpy`, `scikit-learn`, `joblib`.
3. No network calls, no API keys, no paid/gated services. Every model call goes through `mock_llm.chat`.
4. Fixed seeds: `random_state=42` for every split, model, K-means and resampling operation. Keep `SEED`, `SNAPSHOT`, `LAPSE_CUTOFF` and limits in `src/config.py`.
5. All money is INR, two decimals in reports. Never use `$`.
6. Never commit `.env`, `.venv`, `__pycache__`, logs, charts or images. No screenshots/PDFs/slides in the submission.
7. Work only on branch `main`. Do not create feature branches.
8. Do not commit or push unless the user explicitly asks. When asked, commit on `main` with a concise message.
9. Do not hand-edit graded outputs. Regenerate them by running the pipeline.
10. Do not proceed past a part until its checkpoints pass. A later part consumes earlier artifacts; a hidden earlier error propagates.

## 3. Environment and commands (Windows PowerShell)

The repository root is `D:\Rohitha\project`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python generate_data.py
python -m src.part_a_audit
python -m src.part_a_clean
python -m src.part_a_validate
python -m src.part_a_sql
python -m src.part_a_eda
python -m src.part_b_segments
python -m src.part_b_lapse
python -m src.part_c_triage
python -m src.part_d_rag
python -m src.part_d_agent
python -m unittest discover -s tests -v
```

If activation is blocked, use the venv interpreter directly: `.\.venv\Scripts\python.exe -m src.part_a_clean`.

The README's Reproduce section targets the grader's clean clone (Linux/macOS style). Keep it valid for that environment too.

## 4. File ownership map

| Area | Files | Produces |
|---|---|---|
| Shared | `src/config.py`, `src/checkpoints.py` | paths, seeds, cutoffs, limits and machine-readable reference values |
| Part A audit | `src/part_a_audit.py` | audit figures |
| Part A clean/store | `src/part_a_clean.py` | `data/clean/*.csv`, `data/instamart.db` |
| Part A validate | `src/part_a_validate.py` | exact phrase `ALL CHECKPOINTS PASSED` |
| Part A SQL | `sql/queries.sql`, `src/part_a_sql.py` | seven query results |
| Part A EDA | `src/part_a_eda.py` | pandas cross-check, IQR, correlation |
| Part B segments | `src/part_b_segments.py` | `outputs/customer_segments.csv` |
| Part B lapse | `src/part_b_lapse.py` | `outputs/lapse_model.joblib`, `outputs/retention_list.csv` |
| Part C | `src/part_c_triage.py` | `outputs/triage_results.csv`, `outputs/triage_budget_demo.csv` |
| Part D RAG | `src/part_d_rag.py` | `retrieve()`, `answer()` used by the agent |
| Part D agent | `src/part_d_agent.py` | `outputs/agent_runs.jsonl`, `outputs/refund_ledger.jsonl`, `state/*.json` |
| Docs | `README.md`, `PLAN.md`, `TRACKER.md` | graded narrative and live status |

## 5. Stage gates

Run the gate after every stage. Full values live in `TRACKER.md`; these are the must-match anchors.

- **A audit**: 13,084 rows; 119 exact dupes; 656 pending; 12,309 distinct orders; 120 bad amounts; 106 negative delivery; 2,541 blank delivery; 61 blank age; 6 bad ages; 24 city spellings; 10 gender spellings; 30 blank genders.
- **A clean**: 12,309 orders; 11,110 completed / 1,199 cancelled; completed revenue INR 2,998,668.80; zero missing completed delivery; 1,199 missing cancelled delivery; cities Pune 227 / Delhi 210 / Bengaluru 197 / Chennai 191 / Hyderabad 191 / Mumbai 184; female 610 / male 560 / unknown 30.
- **A SQL**: Q1 30; Q2 30 rows / INR 2,998,668.80 / Bengaluru-Electronics INR 233,909.45; Q3 11; Q4 25; Q5 550 / INR 2,552.06; Q6 8 rank differences; Q7 183 rows / final INR 2,998,668.80.
- **A EDA**: Bengaluru 523,643.40 / 276.47 / 1,894; Mumbai 479,058.50 / 297.00 / 1,613; mean 269.91 vs median 135.00; skew ~4.61; fences 64.80/297.00/645.30; 897 high outliers, 0 low; strongest |r| is order_amount & discount_pct ~-0.095.
- **B RFM**: 1,175 customers; median recency 19; frequency mean 9.46, max 33; monetary mean 2,552.06, max 14,766.55.
- **B K-means**: K=4 inertia 743.1, silhouette 0.526; all K values in `TRACKER.md` within ±5% inertia / ±0.05 silhouette; PCA 0.634/0.218/total 0.852 ±0.02.
- **B lapse**: 1,156 cohort; 443 lapsed (38.32%); 924/232 split; baseline 61.6% accuracy, F1 0; selected model test F1 >= 0.55; balanced 570/570; recall ~0.64 -> ~0.85.
- **C**: 4 empty, 4 long (~734 tokens), 156 eligible; 55/91/132/278 redactions with 0 left; 19 transient errors all recovered; 135/12/9 statuses; 147 classified; 85.7% vs 100% accuracy; 164 output rows.
- **D**: 15 chunks (4/3/3/3/2); retrieval 3/3 refund; 12/12, 12/12, 2/2; zero-overlap fails; S1-S7 outcomes and amounts as in `TRACKER.md`; S1 token-limit and timeout fallbacks; crash/resume exactly four tools and final REFUND 128.25.

## 6. Critical implementation pitfalls

### Part A
- Read `tickets.csv` with `keep_default_na=False`; empty text must remain `""`.
- Clean orders in the brief's exact order: datetime -> drop exact duplicates -> keep latest `order_ts` per `order_id`. Dropping dupes after the latest-per-order step changes counts.
- Count exact duplicates before deduping; the raw file has 119 duplicate rows.
- Invalid ages (outside 10-100) are missing first, then filled with the **city median** via `groupby(...).transform("median")`.
- Fill delivery only for completed orders, using the median of the order's **product category** among completed orders. Never impute cancelled delivery.
- Store `order_ts` in SQLite as text `YYYY-MM-DD HH:MM:SS`.
- Q5's average is over customers with completed spend, not over all orders.

### Part B
- RFM snapshot is `2025-10-01 00:00:00`; only completed orders.
- `KMeans(n_init=10, random_state=42)`; PCA on the **scaled** RFM matrix.
- Premium = segment with the highest mean monetary value, not a fixed cluster number.
- Lapse cutoff is `2025-09-01`. Cohort = completed order strictly before the cutoff; label = no completed order during September 2025.
- Features must use orders before the cutoff only. Cancellation rate uses all final-status orders before the cutoff.
- Never use the Part B segment labels as lapse features. Never fit an encoder, scaler or resampler on test rows.
- Random forest grid is exactly 3 depths x 3 leaf sizes x 5 folds = 45 fits.
- Oversample only training rows; test set stays untouched.
- The Premium flag is a whole-window post-hoc label. State that the retention list is illustrative and not leakage-free.

### Part C
- Process tickets in file order.
- Guardrails run before model calls: blank/whitespace -> `skipped_empty`; `est_tokens(text) > 400` -> `flagged_long`.
- Redact in the exact order email -> phone -> order ID. Count with `re.subn`. Assert no pattern remains.
- The user message content is exactly the redacted text and nothing else.
- Zero-shot system prompt must not contain `EXAMPLES:`; few-shot must contain `EXAMPLES:` plus at least two examples including fraud.
- Call `mock_llm.reset()` immediately before each full run. The mock fails every 9th call (19 failures over 156 tickets).
- Max 3 retries per ticket; wait formula `0.05 * 2**n * random.uniform(0.9, 1.15)` for retry n = 0,1,2; log every retry.
- Validate with `re.findall(r"[a-z]+", text.lower())`; a whitespace split misses `billing-related`.
- Valid JSON with an outside category is `flagged_invalid_output`, never guessed.
- Budget is checked **before** each call; if current tokens >= budget, skip the call.
- Final routing precedence: non-classified -> human review; fraud -> security; premium -> premium desk; else support queue. Missing segment row = not premium.

### Part D
- Chunking is 40 words, overlap 10 (next start +30); stop after a chunk reaches the end. Verify 15 chunks.
- Fit TF-IDF once on all chunks; use cosine similarity. `retrieve` returns `source`, `score`, `text`.
- `answer()` sends exactly two messages; system contains `POLICY ASSISTANT`; user format is `CONTEXT:\n[source]\n<chunk>\n...\nQUESTION:\n<question>`.
- Five tools with exact names and I/O shapes. Ledger appends one JSON line per issue/escalate with timestamp and tool name.
- ReAct: system contains `AGENT`; append assistant tool-call messages and tool result messages; checkpoint after every observation.
- Check timeout at the top of every iteration using `time.monotonic()`; `time_limit_seconds=0` must stop before the first call.
- Check token limit immediately after each call and before executing the requested tool.
- Default `token_limit=6000` must let S7 reach six calls and end with `FALLBACK_MAX_ITERATIONS`; `token_limit=200` on S1 must end with `FALLBACK_TOKEN_LIMIT`.
- Crash demo: crash after the **second** tool checkpoint; resume must execute the remaining tools only. Final tools for S1: `get_order`, `search_policy`, `calculate_refund`, `issue_refund` (four, no repeats).
- Clear run-scoped JSONL/checkpoints at the start of a full run; use separate run ids for demos so the seven-scenario outputs stay clean.

## 7. Work protocol

1. Read `TRACKER.md`; pick the first unchecked task in the current part.
2. Mark it `[~]` before starting.
3. Implement in the assigned module; keep `src/config.py` as the only place for paths/constants.
4. Run the smallest verification (stage script and/or targeted assertions).
5. Update `README.md` with the measured numbers and explanations **at the same time**.
6. Mark the task `[x]` and update the dashboard only after the gate passes.
7. If a checkpoint fails, stop and fix the root cause; do not "adjust" expected numbers.
8. At the end of a part, run the part acceptance checklist and a clean rerun of its scripts.

## 8. Style and quality

- Python 3.11+ syntax; clear function names; small, testable functions.
- Resolve paths from `src/config.py`; scripts must work from the repo root regardless of the caller's cwd.
- Prefer assertions and explicit `print` summaries over silent success.
- Keep report tables in README; keep raw logs out of the repository.
- Do not add explanatory comments to code; use docstrings only where a function's contract is non-obvious.
- No placeholder values in final outputs. Every artifact must be regenerated by code.

## 9. Definition of done

A task is done only when the stage script runs, the relevant checkpoint values match, the required artifact exists with the exact columns, the README contains the required numbers/explanation, and a clean rerun reproduces the result. A part is done when all its tasks and acceptance criteria are satisfied.

## 10. Submission reminders

- One public repo, branch `main`, link resolves to `/tree/main`.
- Required paths exist exactly as listed in the brief.
- README top-level sections in order: Overview, Reproduce, Part A, Part B, Part C, Part D, Limitations and Next Steps.
- No TODO left; no images; no secrets; supplied hashes intact.
- Final commit/push only on explicit user request.

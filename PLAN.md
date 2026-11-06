# Implementation Plan — Instamart Customer Intelligence & Support Copilot

## 0. What the downloaded directory contains

`D:\Rohitha` contains a saved copy of the Masai assessment page, not a starter repository:

| Item | Meaning |
|---|---|
| `Assessment Platform.html` (333 KB) | Saved `assess.masaischool.com/test?...` page. It contains one question, Q1, which is the complete 21-day capstone brief. |
| `Assessment Platform_files/main.6b7b2690.js.download` (7.2 MB) | The site bundle; not part of the assignment deliverable. |
| `Assessment Platform_files/main.48cccd94.css`, `css2`, `masaiLogo...svg` | Page styling and logo; not part of the deliverable. |
| `project/` | Empty target folder for the actual submission. |

The brief was extracted verbatim into `docs/ASSIGNMENT_BRIEF.md` (all 605 lines: supplied code, Parts A-D, reference checkpoints and submission rules). The page shows 39% progress, but the saved HTML contains only Q1; there is no second question to recover.

Baseline verified on this machine:

- Python `3.12.10`, SQLite `3.49.1` (both satisfy the brief's minimums).
- The supplied `generate_data.py` runs and prints exactly `generated: customers=1200 products=40 orders_raw=13084 tickets=164`.
- Raw data and five policy files were generated under `data/raw/` and `data/policies/`.
- Supplied-file SHA-256:
  - `generate_data.py`: `e5bd939dfa40402281d0285bdf755d3b75f42159265d78098e248e58683de6cd`
  - `mock_llm.py`: `77bf9bb7cb96e67f49d808cb2e84befb0e5a346833cd508df924437b606905b6`

## 1. Non-negotiables

1. One public GitHub repository, one branch named `main`, one `README.md`. The submitted link must resolve to `main`.
2. `generate_data.py` and `mock_llm.py` stay byte-for-byte unmodified at the repository root.
3. Allowed libraries only: Python standard library, `pandas`, `numpy`, `scikit-learn`, `joblib`. No paid, gated or network service.
4. Every model call goes through `mock_llm.chat`; no API keys, no network calls.
5. Fixed seeds: data seed `42` is inside the supplied generator; `random_state=42` wherever scikit-learn randomness appears.
6. Every reported number goes into the matching README section. No images, screenshots, PDFs, slides, video or audio.
7. All money is INR, never dollars.
8. Reproducibility is graded: a clean clone plus the README's numbered commands must regenerate every required artifact and checkpoint.
9. No leakage: Part B encoders/scalers/resamplers fit on training rows only; no order dated on or after `2025-09-01` enters lapse features; Part B segment labels are never lapse features.
10. Do not proceed past a part until its reference checkpoints pass.

## 2. Data flow

```text
generate_data.py
  -> data/raw/{customers,products,orders,tickets,policy_eval,agent_scenarios}.csv
  -> data/policies/*.txt

Part A
  -> data/clean/{customers,products,orders}.csv
  -> data/instamart.db (customers, products, orders)
  -> sql/queries.sql results + EDA report

Part B (reads clean orders/customers)
  -> outputs/customer_segments.csv
  -> outputs/lapse_model.joblib
  -> outputs/retention_list.csv

Part C (reads raw tickets + customer_segments.csv)
  -> outputs/triage_results.csv
  -> outputs/triage_budget_demo.csv

Part D (reads policies + instamart.db)
  -> outputs/agent_runs.jsonl
  -> outputs/refund_ledger.jsonl
  -> state/<run_id>.json
```

Dependency rule: A must be correct before B; B's segments must exist before C's final routing; D's tools reuse Part A's database and Part D's own retrieval code.

## 3. Repository layout

```text
project/
  AGENTS.md                  agent operating manual and guardrails
  PLAN.md                    this plan
  TRACKER.md                 live task and checkpoint tracker
  README.md                  graded documentation (required sections in order)
  requirements.txt           pinned pip freeze
  .gitignore                 .env, .venv, __pycache__, logs
  generate_data.py           supplied, unmodified
  mock_llm.py                supplied, unmodified
  docs/ASSIGNMENT_BRIEF.md   extracted brief for reference
  sql/queries.sql            seven Part A queries
  src/
    config.py                shared paths, seeds and constants
    checkpoints.py           machine-readable reference values for assertions
    part_a_audit.py          A1 audit
    part_a_clean.py          A2-A4 cleaning, CSV and SQLite storage
    part_a_validate.py       A4 checkpoint assertions
    part_a_sql.py            A5 seven SQL queries
    part_a_eda.py            A6-A7 pandas cross-check and EDA
    part_b_segments.py       B1-B3 RFM, K-means, profiles, PCA
    part_b_lapse.py          B4-B8 lapse modelling and retention list
    part_c_triage.py         C1-C7 triage pipeline
    part_d_rag.py            D1-D4 chunking, retrieval, grounded answers
    part_d_agent.py          D5-D9 tools, ReAct, safe stops, resume
    run_all.py               optional one-shot orchestrator
  tests/test_setup.py        setup/integrity checks (stdlib unittest)
  data/raw/                  generated inputs
  data/clean/                Part A outputs
  data/policies/             generated policy texts
  data/instamart.db          Part A SQLite database
  outputs/                   all graded outputs
  state/                     Part D checkpoints
```

Scripts are run as modules (`python -m src.part_a_clean`) so relative imports work consistently. `src/run_all.py` calls the same modules in order but is optional; the README lists the explicit sequence.

## 4. Build phases

### Phase 0 — Setup (done by this scaffold)

| Step | Action | Verify |
|---|---|---|
| 0.1 | Create repo folder structure | Tree matches section 3 |
| 0.2 | Copy supplied files verbatim | `sha256sum` matches the two hashes above |
| 0.3 | Create venv and install allowed libraries | `pip freeze` matches `requirements.txt` |
| 0.4 | Run `python generate_data.py` | exact final line `generated: customers=1200 products=40 orders_raw=13084 tickets=164` |
| 0.5 | Write README skeleton, PLAN, TRACKER, AGENTS | `python -m unittest discover -s tests -v` passes setup tests |
| 0.6 | Initialise git on `main` | `git branch --show-current` prints `main` |

### Phase A — Data Foundation (suggested days 1-5, 22 marks)

**A1. Audit raw data** (`src/part_a_audit.py`)
- Load all three raw tables. Read `tickets.csv` with `keep_default_na=False`.
- Report shape, dtypes, and missing count/percentage for every column.
- Report exactly: 13,084 order rows; 119 exact duplicates; 656 pending; 12,309 distinct `order_id`; 120 non-numeric amounts; 106 negative delivery times; 2,541 blank delivery times; 61 blank ages; 6 ages outside 10-100; 24 raw city spellings; 10 raw gender spellings; 30 blank genders.
- Gate: none of these numbers may differ.

**A2. Clean customers** (`src/part_a_clean.py`)
- City: strip, title-case, assert six cities.
- Gender: map every spelling to `male`, `female`, or `unknown`; blank -> `unknown`.
- Age: coerce numeric; values outside 10-100 -> missing; fill with city median via `groupby(...).transform("median")`.
- `signup_date` -> datetime.
- Gate: Pune 227, Delhi 210, Bengaluru 197, Chennai 191, Hyderabad 191, Mumbai 184; female 610, male 560, unknown 30; zero missing ages; min 18, max 60.

**A3. Clean orders** (`src/part_a_clean.py`)
- `order_ts` -> datetime.
- Drop exact duplicate rows (119).
- Keep the latest `order_ts` per `order_id` (12,309 rows).
- `order_amount` -> numeric; unparseable -> missing; fill as `round(price_inr * quantity * (1 - discount_pct/100), 2)` after joining products.
- Negative `delivery_minutes` -> missing. Completed: fill with the median delivery time for the order's product category among completed orders. Cancelled: leave missing.
- Gate: 12,309 rows; 11,110 completed, 1,199 cancelled; zero pending; zero missing amount; zero missing completed delivery; 1,199 missing cancelled delivery; completed revenue INR 2,998,668.80.

**A4. Store and validate** (`src/part_a_clean.py`, `src/part_a_validate.py`)
- Write `data/clean/*.csv`; write SQLite tables `customers`, `products`, `orders`; store `order_ts` as `YYYY-MM-DD HH:MM:SS` text.
- Validation asserts at least eight checkpoints and prints exactly `ALL CHECKPOINTS PASSED`.
- Gate: clean-clone regeneration works and the exact phrase appears.

**A5. SQL analysis** (`sql/queries.sql`, `src/part_a_sql.py`)
- Q1 WHERE/HAVING -> 30 customers.
- Q2 three-table join -> 30 rows, total INR 2,998,668.80, largest Bengaluru/Electronics INR 233,909.45.
- Q3 scalar subquery -> 11 products.
- Q4 LEFT JOIN -> 25 customers.
- Q5 CTE -> 550 customers, average INR 2,552.06.
- Q6 ranking windows -> top rows: Bengaluru C0082 12,856.20; Chennai C0930 10,151.40; Delhi C0291 13,742.60; Hyderabad C0743 12,730.05; Mumbai C0693 14,766.55; Pune C0426 10,377.10; exactly 8 rows where `RANK()` differs from `ROW_NUMBER()`.
- Q7 running total -> 183 daily rows; final cumulative INR 2,998,668.80.

**A6-A7. Pandas cross-check and EDA** (`src/part_a_eda.py`)
- `pivot_table(..., margins=True)` grand total equals SQL total.
- City groupby: Bengaluru sum 523,643.40, mean 276.47, count 1,894; Mumbai 479,058.50, 297.00, 1,613.
- Completed amounts: mean 269.91, median 135.00, skew ~4.61, Q1 64.80, Q3 297.00, upper fence 645.30, 897 above, none below.
- Correlation: largest absolute pair `order_amount`/`discount_pct` ~-0.095; `order_amount`/`quantity` ~+0.087; explicitly say correlation does not establish causation.
- Write the <=200-word interpretation into README.

### Phase B — Segments and Lapse (suggested days 6-11, 28 marks)

**B1. RFM** (`src/part_b_segments.py`)
- Snapshot `2025-10-01 00:00:00`; completed orders only.
- Recency in whole days, frequency = distinct completed orders, monetary = completed sum.
- Gate: 1,175 customers; recency median 19, min 0, max 180; frequency mean 9.46, max 33; monetary mean 2,552.06, max 14,766.55.

**B2. K-means**
- `StandardScaler` on RFM; K=2..8 with `KMeans(n_clusters=K, n_init=10, random_state=42)`; record inertia and silhouette.
- Expected: K=2 1820.8/0.465; K=3 1268.2/0.445; K=4 743.1/0.526; K=5 617.4/0.481; K=6 503.2/0.482; K=7 408.5/0.416; K=8 366.5/0.412 (inertia ±5%, silhouette ±0.05).
- Choose from {3,4,5}; K=4 is the reference choice. Explain why tiny inertia at K=8 cannot select K alone.

**B3. Profiles, names, PCA, segment file**
- K=4 sizes about 436/138/419/182; the 138 segment monetary ~7,130 and frequency ~6.8; the 419 segment frequency ~19.4 and recency ~8.8 days.
- Mark the highest-mean-monetary segment as Premium.
- `PCA(n_components=2)` on scaled RFM: ratios ~0.634 and ~0.218, total ~0.852 (±0.02).
- Write `outputs/customer_segments.csv` with `customer_id, recency, frequency, monetary, segment_id, segment_name, is_premium`.
- State that cluster IDs are unordered labels.

**B4. Lapse cohort**
- Cutoff `2025-09-01`; cohort = customers with a completed order before cutoff.
- Label 1 if no completed order in `2025-09-01`..`2025-09-30`.
- Features only before cutoff: recency, frequency, monetary, avg discount, cancellation rate, avg completed delivery, favourite category, city, age, gender, tenure.
- Gate: 1,156 customers; 443 lapsed (38.32%); train 924, test 232; majority baseline accuracy 61.6%, lapsed F1 0.
- Forbidden: segment labels as features; any order on/after cutoff.

**B5. Leak-free preprocessing**
- `ColumnTransformer`: numeric `StandardScaler`; nominal `OneHotEncoder(drop="first", handle_unknown="ignore")`; all inside a `Pipeline` fitted on train only.
- Report learned train mean frequency versus full-cohort mean and explain the difference.
- Assert zero missing feature values.

**B6. Train, tune, evaluate** (`src/part_b_lapse.py`)
- Logistic `GridSearchCV(C in {0.01,0.1,1,10,100}, cv=5, scoring="f1")`.
- Random forest `n_estimators=100, random_state=42`, `max_depth in {3,5,8}`, `min_samples_leaf in {5,10,20}`, 45 fits.
- Report best params/CV F1, then test confusion matrix and lapsed precision/recall/F1. Reference LR test F1 ~0.62, RF ~0.65; selected model must reach >=0.55.
- Justify selection via cost of missing a lapsing customer versus wrongly targeting a loyal one.

**B7. Class balance**
- Training rows only; duplicate lapsed rows with replacement (`random_state=42`) until both classes equal (570/570 reference).
- Compare precision/recall/F1 on the unchanged test set. Reference recall ~0.64 -> ~0.85, precision ~0.6 (does not rise).

**B8. Interpret, persist, use**
- Top five random-forest importances; three logistic coefficient signs with one-line business reading.
- `joblib.dump`/`joblib.load`; prove identical test predictions.
- `outputs/retention_list.csv`: Premium test customers ranked by predicted lapse probability, top 10 with `customer_id, lapse_probability, actually_lapsed`.
- State that Premium is a post-hoc whole-window label and the list is illustrative.

### Phase C — Support Triage (suggested days 12-15, 22 marks)

**C1. Input guardrails** (`src/part_c_triage.py`)
- Iterate tickets in file order.
- Blank/whitespace -> `skipped_empty`, no model call.
- `est_tokens(text) > 400` -> `flagged_long`, no model call.
- Gate: 4 empty, 4 long; long tickets ~734 tokens; 156 eligible.

**C2. Redaction**
- Apply exactly in order: email `[\w.+-]+@[\w-]+\.[\w.]+` -> `[EMAIL]`; phone `\b[6-9]\d{9}\b` -> `[PHONE]`; order `ORD-\d{6}` -> `[ORDER_ID]`.
- Count substitutions per type and total: 55 emails, 91 phones, 132 order IDs, 278 total; assert zero patterns remain.
- The user message content must be exactly the redacted text.

**C3. Two prompts**
- Both system prompts contain `CLASSIFY`, list exactly the four categories, and demand JSON-only `{"category": "...", "reason": "..."}`.
- Zero-shot must not contain `EXAMPLES:`.
- Few-shot contains a line `EXAMPLES:` and at least two labelled examples, one fraud.

**C4. Resilient calls**
- `mock_llm.reset()` immediately before each full run.
- Max 3 retries per ticket; wait before retry n (0,1,2) is `0.05 * 2**n * random.uniform(0.9, 1.15)`.
- One log line per retry with ticket id, retry number and wait.
- Gate: exactly 19 `TransientLLMError`s in a full eligible run, all recovered; no permanent errors.

**C5. Validate every answer**
- Valid JSON with allowed category -> `classified_json`.
- Otherwise `re.findall(r"[a-z]+", text.lower())`; exactly one allowed category word -> `classified_keyword`.
- All else, including JSON with an outside category -> `flagged_invalid_output`, human review, never guess.
- Gate: 135 JSON, 12 keyword, 9 invalid over 156 eligible tickets.

**C6. Compare prompts**
- Run full pipeline with zero-shot and few-shot, no budget.
- Report classified count, accuracy over classified, total tokens, tokens/classified.
- Gate: 147 classified; zero-shot 85.7% (126/147; errors are fraud->billing 11 and technical->billing 10); few-shot 100%.
- Include zero-shot confusion table; explain when few-shot tokens are worth it.

**C7. Budget, routing, final outputs**
- Budget check before every call: if running token total >= budget -> `budget_exhausted`, no call, human review.
- Demo with 6000; if no ticket exhausts, lower and report. Save `outputs/triage_budget_demo.csv`.
- Final few-shot run with budget 100000 and routing from `outputs/customer_segments.csv`:
  - skipped/flagged/budget exhausted -> `human_review`, `NORMAL`;
  - fraud -> `security_team`, `HIGH`;
  - premium -> `premium_desk`, `HIGH`;
  - otherwise -> `support_queue`, `NORMAL`.
- Missing segment row = not premium. Columns exactly as specified. Write 164-row `outputs/triage_results.csv`.

### Phase D — RAG and Refund Agent (suggested days 16-21, 28 marks)

**D1. Chunking** (`src/part_d_rag.py`)
- 40-word chunks, 10-word overlap, next start +30 words; stop when a chunk reaches the document end.
- Record source file per chunk. Gate: 15 chunks: refund 4, delivery 3, escalation 3, payment 3, privacy 2.

**D2. Vectorise and retrieve**
- Fit `TfidfVectorizer()` on chunk texts; transform query; rank by `cosine_similarity`.
- `retrieve(query, k=3)` returns dicts with `source`, `score`, `text`.
- Explain TF, IDF and one TF-IDF limitation. Gate: `refund policy late delivery` returns three refund-policy chunks.

**D3. Grounded answer**
- `answer(question)` retrieves three chunks and sends exactly two messages to `mock_llm.chat`.
- System contains `POLICY ASSISTANT`; user is:
  `CONTEXT:` newline, each chunk prefixed by `[<source>]` on its own line, newline `QUESTION:` newline, question.
- Return answer text and sources.

**D4. Evaluate grounding**
- 12 answerable, 2 unanswerable. Gate: 12/12 expected doc in top three, 12/12 expected fact present, 2/2 fallback beginning `I could not find`.
- Repeat with zero overlap; at least one answerable question fails. Name it and explain the chunk-boundary split.

**D5. Tools**
- Five tools with name, one-sentence description and JSON-style parameters in `TOOLS_SPEC`; `TOOL_MAP` name -> function.
- `get_order` reads `data/instamart.db`, returns the four fields or `{"error": "order not found"}`.
- `search_policy` returns retrieval under `results`.
- `calculate_refund` returns 0 at <=45 minutes, full amount above 45.
- `issue_refund` and `escalate_to_human` append one JSON line each to `outputs/refund_ledger.jsonl` with timestamp and tool name; return `refund_inr`.

**D6. ReAct loop and seven scenarios**
- `run_agent(user_message, scenario_id, max_iterations=6, token_limit=6000, time_limit_seconds=10)`.
- Messages start with system containing `AGENT` plus the user message.
- Each iteration: time check; chat; add tokens; final if no tool calls; else append assistant `tool_calls`, execute via `TOOL_MAP`, append tool JSON, loop.
- Return `status`, `final_answer`, `steps`, `llm_calls`, `tokens_used`; status is the word before the colon.
- Write one JSON line per scenario to `outputs/agent_runs.jsonl`.
- Gate: S1 REFUND 128.25; S2 REFUND 135.00; S3 ESCALATE 1999.00; S4 DENIED; S5 DENIED; S6 NOT_FOUND; S7 FALLBACK_MAX_ITERATIONS; S1 five calls; S7 completes six calls under the default 6000 token limit.

**D7. Stop safely**
- `FALLBACK_MAX_ITERATIONS` after six calls without final answer (S7).
- Check tokens immediately after each call; if over `token_limit`, stop before executing the requested tool -> `FALLBACK_TOKEN_LIMIT`; demo S1 with `token_limit=200`.
- At top of each iteration, if `time.monotonic()` elapsed >= limit -> `FALLBACK_TIMEOUT`; demo with `time_limit_seconds=0`, before the first call.
- Every fallback returns completed steps and a short human-handoff summary.

**D8. Crash and resume**
- After every tool observation, write `state/<run_id>.json` with run id, scenario id, full messages, tokens, step, tools already executed.
- `resume_agent(run_id)` loads and continues.
- Demo S1: crash after the second tool's checkpoint, then resume. Gate: tools exactly `get_order, search_policy, calculate_refund, issue_refund` (four, no repeats); final `REFUND` 128.25.

**D9. ReAct versus plan-and-execute**
- <=250 words using measured calls (S1=5, S5=3, S6=2); cover calls/tokens, unexpected observations (`NOT_FOUND`, cancelled order), and a justified choice.

## 5. Cross-cutting engineering rules

- Resolve every path from `src/config.py` (`ROOT = Path(__file__).resolve().parents[1]`), never from the current working directory.
- Use `random_state=42` (or `SEED`) for every split, model, K-means, PCA-sensitive operation and resampling.
- Use `keep_default_na=False` for `tickets.csv`.
- Store money as INR; format two decimals in reports.
- Print machine-checkable stage summaries; assert checkpoints in code so a wrong run fails loudly.
- Clear run-scoped outputs at the start of a full run (`outputs/refund_ledger.jsonl`, `outputs/agent_runs.jsonl`, demo checkpoints) so re-runs are deterministic and do not append duplicates.
- Never commit `.env`, `.venv`, `__pycache__`, logs, charts or images.
- Update `TRACKER.md` after each task and paste measured numbers into `README.md` immediately; do not leave numbers only in console output.
- No comments in source unless they document a non-obvious rule; prefer clear names and assertions.

## 6. Definition of done per part

A part is done only when all of these hold:

1. Its script runs end-to-end from the repo root with the documented command.
2. Every reference checkpoint in `TRACKER.md` for that part matches (within stated tolerance where applicable).
3. Its required artifacts exist at the exact paths and with the exact columns.
4. The README's matching section contains every number, table and explanation the brief requests.
5. Re-running the part from a clean state is deterministic.
6. No earlier part's artifact was manually edited to make a later part pass.

## 7. Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Cleaning order wrong (dedupe before latest-per-order) | 12,309 rows and all revenue checkpoints wrong | Follow A3 order exactly; validate before B |
| Tickets read with default NA handling | Empty tickets become NaN and skip guardrails | Always `keep_default_na=False` |
| Test leakage in Part B | Inflated metrics, failed acceptance | Fit encoders/scalers/resampler on train only; assert feature date < cutoff |
| Segment labels used as lapse features | Leakage and invalid model | Never join `customer_segments.csv` into lapse features |
| Part C retry counter not reset | Wrong number of transient errors | Call `mock_llm.reset()` immediately before each full run |
| Budget checked after the call | Wrong `budget_exhausted` count | Check before every model call |
| Chunk boundary cuts an answer | Zero-overlap evaluation passes unexpectedly | Implement exact 40/10 windows; verify 15 chunks |
| Tool observations serialised differently | S7/token counts shift | Keep stable JSON serialisation and token accounting |
| Crash demo repeats tools on resume | Fails exactly-four-tools gate | Load checkpoint with full message list and executed-tool list |
| `state/` or JSONL outputs appended across runs | Duplicate/invalid artifacts | Clear per-run outputs at start; separate demo run ids |
| Re-running Part D with different prompt lengths | Reference token ranges drift | Keep prompts concise and report actual measured tokens |
| Supplied files accidentally edited | Grade penalty / integrity failure | Compare SHA-256 before submission; restore from brief if needed |

## 8. Final submission checklist

- [ ] `git branch --show-current` is `main`; remote is public; link resolves to `/tree/main`.
- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] Clean-clone dry run: delete `.venv`, `data/raw`, `data/clean`, `data/instamart.db`, `outputs/*`, `state/*`; run README commands in order; every checkpoint matches.
- [ ] Required paths exist: both supplied files, `requirements.txt`, `.gitignore`, `README.md`, clean CSVs, DB, `sql/queries.sql`, all Part B/C/D outputs, `state/`.
- [ ] README top-level sections are in order: Overview, Reproduce, Part A, Part B, Part C, Part D, Limitations and Next Steps.
- [ ] Every "report" number is in the README; no TODO remains.
- [ ] No images/screenshots/PDF/slides/video/audio, no `.env`, no keys, no charts committed.
- [ ] Supplied-file hashes still match.
- [ ] `outputs/triage_results.csv` has 164 rows; `outputs/agent_runs.jsonl` has the seven scenario runs; ledger and checkpoints present.
- [ ] Final commit exists on `main` (only after the user explicitly asks to commit/push).

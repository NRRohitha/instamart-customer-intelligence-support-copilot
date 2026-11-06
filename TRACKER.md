# Progress Tracker — Instamart Customer Intelligence & Support Copilot

Legend: `[ ]` not started · `[~]` in progress · `[x]` done and verified · `[!]` blocked. Update this file and the README together; a task is never `[x]` because code "looks right", only because its checkpoint command passed.

## Dashboard

| Area | Tasks | Done | Gate status |
|---|---|---|---|
| Phase 0 setup | 7 | 7 | setup tests pass; git on `main` |
| Part A (22) | 14 | 14 | all checkpoints pass |
| Part B (28) | 15 | 15 | all checkpoints pass |
| Part C (22) | 9 | 9 | all checkpoints pass |
| Part D (28) | 14 | 14 | all checkpoints pass |
| Final submission | 6 | 6 | published on main |
| **Total** | **65** | **65** | **100%** |

## Phase 0 — Setup

- [x] **P0.1** Create the repository structure (`src/`, `sql/`, `tests/`, `data/{raw,clean,policies}/`, `outputs/`, `state/`, `docs/`).
- [x] **P0.2** Copy `generate_data.py` and `mock_llm.py` verbatim to the repo root; record SHA-256 in `AGENTS.md` and `PLAN.md`.
- [x] **P0.3** Create `.venv`, install allowed libraries, write pinned `requirements.txt` (`pip freeze`).
- [x] **P0.4** Run `python generate_data.py`; verify the exact final line and raw counts.
- [x] **P0.5** Write `README.md` skeleton, `PLAN.md`, `TRACKER.md`, `AGENTS.md`, tests and module stubs.
- [x] **P0.6** Initialise git on branch `main`; confirm `git branch --show-current` prints `main`.
- [x] **P0.7** Run `python -m unittest discover -s tests -v`; all setup tests pass (5 tests, OK).

## Part A — Data Foundation (22 marks)

- [x] **A1** Raw-data audit (`src/part_a_audit.py`): shape, dtypes, missing profile and the 12 audit figures. Gate: all 12 match.
- [x] **A2** Clean customers (`src/part_a_clean.py`): city, gender, age imputation, signup date. Gate: city/gender/age counts match.
- [x] **A3** Clean orders (`src/part_a_clean.py`): dedupe, latest per order, amount fill, delivery fill. Gate: 12,309 / 11,110 / 1,199 and revenue match.
- [x] **A4** Store CSVs + SQLite and write validation (`src/part_a_validate.py`). Gate: prints exactly `ALL CHECKPOINTS PASSED`.
- [x] **A5a** SQL Q1 WHERE/HAVING. Gate: 30 customers.
- [x] **A5b** SQL Q2 three-table join. Gate: 30 rows, total INR 2,998,668.80, max Bengaluru/Electronics INR 233,909.45.
- [x] **A5c** SQL Q3 scalar subquery. Gate: 11 products.
- [x] **A5d** SQL Q4 LEFT JOIN. Gate: 25 customers.
- [x] **A5e** SQL Q5 CTE. Gate: 550 customers, average INR 2,552.06.
- [x] **A5f** SQL Q6 ranking windows. Gate: six city tops, exactly 8 rank/row-number differences; README tie explanation.
- [x] **A5g** SQL Q7 running total. Gate: 183 daily rows, final cumulative INR 2,998,668.80.
- [x] **A6** Pandas pivot cross-check and city groupby. Gate: pivot grand total equals SQL; Bengaluru/Mumbai values match.
- [x] **A7** IQR, correlation and <=200-word interpretation. Gate: mean/median/skew/quartiles/fences/outlier counts and strongest pair match; README text present.
- [x] **A8** README Part A complete with every cleaning rule and rows changed; acceptance criteria reviewed.

## Part B — Customer Segments and Lapse Prediction (28 marks)

- [x] **B1** RFM table (`src/part_b_segments.py`). Gate: 1,175 customers and recency/frequency/monetary references match.
- [x] **B2** K-means K=2..8 table and elbow discussion. Gate: inertia/silhouette within tolerance; K selected from {3,4,5}.
- [x] **B3a** Segment sizes, means, business names, actions, Premium flag. Gate: K=4 profile references match; Premium = highest mean monetary.
- [x] **B3b** PCA explained variance. Gate: ~0.634/0.218, total ~0.852 (±0.02).
- [x] **B3c** Write `outputs/customer_segments.csv` with exact columns. Gate: file exists and columns match.
- [x] **B4** Lapse cohort and label (`src/part_b_lapse.py`). Gate: 1,156 cohort, 443 lapsed (38.32%), 924/232 split; no post-cutoff orders or segment labels in features.
- [x] **B5** Leak-free preprocessing pipeline and missing-value check. Gate: learned train scaler mean printed next to cohort mean; zero missing features; training-only fit proven.
- [x] **B6a** Logistic regression grid search. Gate: grid `C in {0.01,0.1,1,10,100}`, cv=5, f1; best params and test metrics reported.
- [x] **B6b** Random forest grid search (45 fits). Gate: `max_depth in {3,5,8}`, `min_samples_leaf in {5,10,20}`, cv=5; best params and test metrics reported.
- [x] **B6c** Model choice and test F1 >= 0.55. Gate: confusion matrices plus 3-5 sentence cost justification.
- [x] **B7** Class-balance experiment on training only. Gate: balanced 570/570 (or equivalent), recall moves most; test unchanged.
- [x] **B8a** Feature importances and coefficient signs with business readings. Gate: top five RF features and three LR coefficients reported.
- [x] **B8b** Persist/reload model proof. Gate: `outputs/lapse_model.joblib` exists; reloaded predictions identical.
- [x] **B8c** Premium retention list. Gate: `outputs/retention_list.csv` exact columns, top 10, true-lapse count reported; post-hoc-label caveat present in README and Limitations.
- [x] **B9** README Part B complete; acceptance criteria reviewed.

## Part C — Support Ticket Triage with Guardrails (22 marks)

- [x] **C1** Input guardrails (`src/part_c_triage.py`). Gate: 4 empty, 4 long (~734 tokens), 156 eligible, no model call for either group.
- [x] **C2** Redaction in exact order. Gate: 55 emails, 91 phones, 132 order IDs, 278 total, 0 remain; user message is exactly redacted text.
- [x] **C3** Zero-shot and few-shot prompts. Gate: both contain CLASSIFY and four categories; zero-shot lacks `EXAMPLES:`; few-shot has `EXAMPLES:` plus a fraud example; JSON-only instruction.
- [x] **C4** Retry wrapper with 3 retries, exponential backoff and jitter. Gate: one log line per retry; exactly 19 transient errors recovered; no permanent error; `reset()` before run.
- [x] **C5** Output validation. Gate: 135 `classified_json`, 12 `classified_keyword`, 9 `flagged_invalid_output`; outside-list JSON never guessed.
- [x] **C6** Zero-shot vs few-shot full runs. Gate: 147 classified; zero-shot 85.7% (126/147), few-shot 100%; token totals and per-ticket costs reported; zero-shot confusion table.
- [x] **C7a** Budget demo. Gate: `outputs/triage_budget_demo.csv`; at least one `budget_exhausted`; budget and count reported.
- [x] **C7b** Final few-shot routing + `outputs/triage_results.csv`. Gate: 164 rows, exact columns, routing rules applied, missing segment = not premium.
- [x] **C8** README Part C complete; acceptance criteria reviewed.

## Part D — Policy RAG Assistant and Refund Agent (28 marks)

- [x] **D1** Chunking (`src/part_d_rag.py`). Gate: 15 chunks (refund 4, delivery 3, escalation 3, payment 3, privacy 2).
- [x] **D2** TF-IDF retrieval and `retrieve(query, k=3)`. Gate: `refund policy late delivery` top three all refund policy; TF/IDF/limitation explanation.
- [x] **D3** Grounded `answer(question)`. Gate: exact two-message format; returns text + sources; fallback phrase supported.
- [x] **D4a** Evaluation with overlap 10. Gate: 12/12 doc, 12/12 fact, 2/2 fallback.
- [x] **D4b** Evaluation with overlap 0. Gate: at least one answerable question fails; named and explained.
- [x] **D5** Five tools, `TOOLS_SPEC`, `TOOL_MAP`, ledger. Gate: exact I/O shapes; ledger has one JSON line per issue/escalate with timestamp.
- [x] **D6a** ReAct loop (`src/part_d_agent.py`). Gate: system contains AGENT; tool calls executed by name; return dict has status/final_answer/steps/llm_calls/tokens_used.
- [x] **D6b** Seven scenarios. Gate: S1 REFUND 128.25; S2 REFUND 135.00; S3 ESCALATE 1999.00; S4 DENIED; S5 DENIED; S6 NOT_FOUND; S7 FALLBACK_MAX_ITERATIONS; S1 five calls; S7 six calls under 6000 tokens.
- [x] **D6c** `outputs/agent_runs.jsonl`. Gate: one line per scenario with all required fields and steps.
- [x] **D7a** `FALLBACK_TOKEN_LIMIT` demo (S1, token_limit=200). Gate: stop before executing requested tool; README status recorded.
- [x] **D7b** `FALLBACK_TIMEOUT` demo (time_limit_seconds=0). Gate: stops before first model call; README status recorded.
- [x] **D8** Checkpoint/resume and crash demo. Gate: checkpoint fields complete; exactly four tools, no repeats; final REFUND 128.25; README lists tools in order.
- [x] **D9** ReAct vs plan-and-execute (<=250 words). Gate: measured calls, unexpected observations, justified choice.
- [x] **D10** README Part D complete; acceptance criteria reviewed.

## Final submission

- [x] **F1** Clean-clone reproduction: wipe generated artifacts, run the README commands in order, all checkpoints pass.
- [x] **F2** README fully filled: all seven required sections in order; no TODO; every reported number present.
- [x] **F3** Integrity: supplied hashes match; no secrets, `.env`, `.venv`, `__pycache__`, images, PDFs or charts committed.
- [x] **F4** Artifact audit: all required paths and columns exist; `triage_results.csv` 164 rows; `agent_runs.jsonl` 7 scenario lines; ledger and `state/` populated.
- [x] **F5** Branch/public check: `main`, public repository, submitted link resolves to `/tree/main`.
- [x] **F6** Final commit and push on `main` (only when the user explicitly asks).

## Reference checkpoint table

Use this as the single source of truth when asserting. The same values are available to code as dictionaries in `src/checkpoints.py`. Tolerances are stated where the brief allows them.

### Part A

| ID | Checkpoint | Expected |
|---|---|---|
| A-AUD-1 | Raw order rows | 13,084 |
| A-AUD-2 | Exact duplicate rows | 119 |
| A-AUD-3 | Pending rows | 656 |
| A-AUD-4 | Distinct order_id | 12,309 |
| A-AUD-5 | Non-numeric order_amount | 120 |
| A-AUD-6 | Negative delivery_minutes | 106 |
| A-AUD-7 | Blank delivery_minutes | 2,541 |
| A-AUD-8 | Blank ages | 61 |
| A-AUD-9 | Ages outside 10-100 | 6 |
| A-AUD-10 | Raw city spellings | 24 |
| A-AUD-11 | Raw non-blank gender spellings | 10 |
| A-AUD-12 | Blank genders | 30 |
| A-CUS-1 | City counts | Pune 227, Delhi 210, Bengaluru 197, Chennai 191, Hyderabad 191, Mumbai 184 |
| A-CUS-2 | Gender counts | female 610, male 560, unknown 30 |
| A-CUS-3 | Missing ages / range | 0 missing; 18-60 |
| A-ORD-1 | Clean rows | 12,309 |
| A-ORD-2 | Status counts | completed 11,110, cancelled 1,199 |
| A-ORD-3 | Missing amounts | 0 |
| A-ORD-4 | Missing completed delivery / cancelled delivery | 0 / 1,199 |
| A-ORD-5 | Completed revenue | INR 2,998,668.80 |
| A-SQL-1 | Q1 customers | 30 |
| A-SQL-2 | Q2 rows / total / max cell | 30 / INR 2,998,668.80 / Bengaluru-Electronics INR 233,909.45 |
| A-SQL-3 | Q3 products | 11 |
| A-SQL-4 | Q4 customers | 25 |
| A-SQL-5 | Q5 customers / average | 550 / INR 2,552.06 |
| A-SQL-6 | Q6 rank differences | 8 |
| A-SQL-7 | Q7 daily rows / final cumulative | 183 / INR 2,998,668.80 |
| A-EDA-1 | Bengaluru sum/mean/count | 523,643.40 / 276.47 / 1,894 |
| A-EDA-2 | Mumbai sum/mean/count | 479,058.50 / 297.00 / 1,613 |
| A-EDA-3 | Mean / median / skew | 269.91 / 135.00 / ~4.61 |
| A-EDA-4 | Q1 / Q3 / upper fence | 64.80 / 297.00 / 645.30 |
| A-EDA-5 | Outliers above / below | 897 / 0 |
| A-EDA-6 | Strongest absolute correlation | order_amount & discount_pct ~-0.095 |

### Part B

| ID | Checkpoint | Expected |
|---|---|---|
| B-RFM-1 | Customers | 1,175 |
| B-RFM-2 | Recency median/min/max | 19 / 0 / 180 |
| B-RFM-3 | Frequency mean/max | 9.46 / 33 |
| B-RFM-4 | Monetary mean/max | INR 2,552.06 / INR 14,766.55 |
| B-KM | Inertia/silhouette by K | K2 1820.8/0.465; K3 1268.2/0.445; K4 743.1/0.526; K5 617.4/0.481; K6 503.2/0.482; K7 408.5/0.416; K8 366.5/0.412 (inertia ±5%, silhouette ±0.05) |
| B-SEG | K=4 sizes / notable means | 436/138/419/182; 138: monetary ~7,130, frequency ~6.8; 419: frequency ~19.4, recency ~8.8 |
| B-PCA | Explained variance | ~0.634, ~0.218; total ~0.852 (±0.02) |
| B-LAP-1 | Cohort / lapsed / rate | 1,156 / 443 / 38.32% |
| B-LAP-2 | Train / test | 924 / 232 |
| B-LAP-3 | Baseline accuracy / lapsed F1 | 61.6% / 0 |
| B-MOD-1 | LR reference test F1 | ~0.62 |
| B-MOD-2 | RF reference test F1 | ~0.65 |
| B-MOD-3 | Minimum selected test F1 | 0.55 |
| B-BAL | Balanced training counts | 570 / 570 |
| B-BAL-2 | Recall movement | ~0.64 -> ~0.85; precision ~0.6 |

### Part C

| ID | Checkpoint | Expected |
|---|---|---|
| C-GRD-1 | Empty / long / eligible | 4 / 4 / 156 |
| C-GRD-2 | Long-ticket tokens | ~734 |
| C-RED-1 | Email / phone / order / total | 55 / 91 / 132 / 278 |
| C-RED-2 | PII remaining | 0 |
| C-RET-1 | Transient errors | 19, all recovered |
| C-VAL-1 | JSON / keyword / invalid | 135 / 12 / 9 |
| C-CMP-1 | Classified | 147 |
| C-CMP-2 | Zero-shot accuracy | 85.7% (126/147) |
| C-CMP-3 | Few-shot accuracy | 100% |
| C-BUD-1 | Budget demo | at least 1 exhausted; report budget and count |
| C-OUT-1 | Final rows | 164 |

### Part D

| ID | Checkpoint | Expected |
|---|---|---|
| D-CHK-1 | Chunks | 15 total: refund 4, delivery 3, escalation 3, payment 3, privacy 2 |
| D-RET-1 | `refund policy late delivery` top 3 | all refund_policy.txt |
| D-EVL-1 | Overlap 10 | 12/12 doc, 12/12 fact, 2/2 fallback |
| D-EVL-2 | Overlap 0 | at least one answerable question fails |
| D-SCN-1 | S1 | REFUND, INR 128.25, 5 calls |
| D-SCN-2 | S2 | REFUND, INR 135.00 |
| D-SCN-3 | S3 | ESCALATE, INR 1,999.00 |
| D-SCN-4 | S4 | DENIED |
| D-SCN-5 | S5 | DENIED |
| D-SCN-6 | S6 | NOT_FOUND |
| D-SCN-7 | S7 | FALLBACK_MAX_ITERATIONS, six calls under default 6000 |
| D-STOP-1 | S1 token_limit=200 | FALLBACK_TOKEN_LIMIT |
| D-STOP-2 | time_limit_seconds=0 | FALLBACK_TIMEOUT |
| D-RES-1 | Crash/resume tools | get_order, search_policy, calculate_refund, issue_refund (4, none repeated) |
| D-RES-2 | Crash/resume final | REFUND, INR 128.25 |

## Run log

| Date | Command | Result | Notes |
|---|---|---|---|
| 2026-11-06 | `python generate_data.py` | PASS | exact generated line |
| 2026-11-06 | `python -m unittest discover -s tests -v` | PASS | 5 tests OK |
| 2026-11-06 | `git init -b main` | PASS | branch `main`; no commit yet |
| 2026-11-06 | `python -m src.part_a_audit` | PASS | all 12 audit figures match |
| 2026-11-06 | `python -m src.part_a_clean` | PASS | 12,309 orders; revenue INR 2,998,668.80 |
| 2026-11-06 | `python -m src.part_a_validate` | PASS | `ALL CHECKPOINTS PASSED` |
| 2026-11-06 | `python -m src.part_a_sql` | PASS | Q1-Q7 match |
| 2026-11-06 | `python -m src.part_a_eda` | PASS | pivot, IQR and correlations match |
| 2026-11-06 | `python -m src.part_b_segments` | PASS | K=4 sizes 436/138/419/182; PCA 0.634/0.218 |
| 2026-11-06 | `python -m src.part_b_lapse` | PASS | cohort 1,156; 443 lapsed; RF test F1 0.655 |
| 2026-11-06 | `python -m src.part_c_triage` | PASS | 19 retries recovered; 135/12/9; 85.7%/100%; budget 76 exhausted |
| 2026-11-06 | `python -m src.part_d_rag` | PASS | 15 chunks; overlap 10: 12/12, 12/12, 2/2; overlap 0: 10/12 fact |
| 2026-11-06 | `python -m src.part_d_agent` | PASS | S1-S7, token/time fallbacks, crash/resume all match |
| 2026-11-06 | clean-copy full pipeline | PASS | all README commands in order; 5 tests OK |
| 2026-11-06 | `git push -u origin main` | PASS | published https://github.com/NRRohitha/instamart-customer-intelligence-support-copilot |

## Decision log

| Date | Decision | Reason |
|---|---|---|
| 2026-11-06 | Modular `src/part_*.py` pipeline with `python -m` entry points | Matches the four-part dependency chain and keeps each stage independently verifiable |
| 2026-11-06 | Pin exact `pip freeze` versions | Reproducibility is graded |
| 2026-11-06 | Use stdlib `unittest` for setup tests | Allowed libraries only; no extra test dependency |




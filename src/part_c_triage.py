import json
import random
import re
import time

import pandas as pd

import mock_llm
from src.config import (
    DATA_RAW,
    MAX_INPUT_TOKENS,
    OUTPUTS,
    TOKEN_BUDGET,
)

BASE_DELAY = 0.05
MAX_RETRIES = 3
ALLOWED = ["billing", "delivery", "technical", "fraud"]
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE_PATTERN = re.compile(r"\b[6-9]\d{9}\b")
ORDER_PATTERN = re.compile(r"ORD-\d{6}")

ZERO_SHOT = """You are a support ticket classifier. CLASSIFY each ticket into exactly one of these categories: billing, delivery, technical, fraud. Reply only with JSON in the form {"category": "...", "reason": "..."}. Do not add any other text."""

FEW_SHOT = """You are a support ticket classifier. CLASSIFY each ticket into exactly one of these categories: billing, delivery, technical, fraud. Reply only with JSON in the form {"category": "...", "reason": "..."}. Do not add any other text.
EXAMPLES:
Ticket: "I was charged twice for order ORD-123456. Please refund the extra payment." -> {"category": "billing", "reason": "duplicate charge"}
Ticket: "Someone hacked my account and made an unauthorized transaction. This is fraud." -> {"category": "fraud", "reason": "unauthorized transaction"}
Ticket: "The app crashes every time I open the cart." -> {"category": "technical", "reason": "app crash"}
Ticket: "My delivery is late and the rider is not answering." -> {"category": "delivery", "reason": "late delivery"}"""

REDACTION_PATTERNS = [
    ("email", EMAIL_PATTERN, "[EMAIL]"),
    ("phone", PHONE_PATTERN, "[PHONE]"),
    ("order_id", ORDER_PATTERN, "[ORDER_ID]"),
]


def redact(text):
    counts = {"email": 0, "phone": 0, "order_id": 0}
    redacted = text
    for name, pattern, placeholder in REDACTION_PATTERNS:
        redacted, count = pattern.subn(placeholder, redacted)
        counts[name] = count
    return redacted, counts


def validate_answer(text):
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        words = re.findall(r"[a-z]+", (text or "").lower())
        found = [category for category in ALLOWED if category in words]
        if len(found) == 1:
            return "classified_keyword", found[0], words
        return "flagged_invalid_output", None, words
    category = parsed.get("category") if isinstance(parsed, dict) else None
    if category in ALLOWED:
        return "classified_json", category, None
    return "flagged_invalid_output", None, None


def call_with_retry(ticket_id, messages, stats, rng):
    for retry in range(MAX_RETRIES + 1):
        try:
            return mock_llm.chat(messages)
        except mock_llm.TransientLLMError:
            stats["transient_errors"] += 1
            if retry == MAX_RETRIES:
                raise
            wait = BASE_DELAY * (2 ** retry) * rng.uniform(0.9, 1.15)
            stats["retries"] += 1
            print(
                f"RETRY ticket={ticket_id} retry={retry} wait={wait:.4f}s",
                flush=True,
            )
            time.sleep(wait)
    raise RuntimeError("unreachable")


def run_pipeline(tickets, system_prompt, budget=None):
    mock_llm.reset()
    stats = {
        "transient_errors": 0,
        "retries": 0,
        "tokens": 0,
        "calls": 0,
        "budget_exhausted": 0,
    }
    rng = random.Random(42)
    records = []
    for row in tickets.itertuples(index=False):
        text = row.text
        record = {
            "ticket_id": row.ticket_id,
            "customer_id": row.customer_id,
            "status": None,
            "category": "",
            "tokens_used": 0,
            "true_category": row.true_category,
        }
        if not text.strip():
            record["status"] = "skipped_empty"
            records.append(record)
            continue
        if mock_llm.est_tokens(text) > MAX_INPUT_TOKENS:
            record["status"] = "flagged_long"
            records.append(record)
            continue
        if budget is not None and stats["tokens"] >= budget:
            record["status"] = "budget_exhausted"
            stats["budget_exhausted"] += 1
            records.append(record)
            continue
        redacted, _ = redact(text)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": redacted},
        ]
        response = call_with_retry(row.ticket_id, messages, stats, rng)
        stats["calls"] += 1
        stats["tokens"] += response.usage.total_tokens
        status, category, _ = validate_answer(response.choices[0].message.content)
        record["status"] = status
        record["category"] = category or ""
        record["tokens_used"] = response.usage.total_tokens
        records.append(record)
    return pd.DataFrame(records), stats


def evaluate(records, label):
    classified = records[records["status"].isin(["classified_json", "classified_keyword"])]
    correct = (classified["category"] == classified["true_category"]).sum()
    accuracy = correct / len(classified) * 100 if len(classified) else 0
    print(f"\n=== {label} ===")
    print(records["status"].value_counts().to_dict())
    print(f"classified: {len(classified)}")
    print(f"correct: {correct}")
    print(f"accuracy: {accuracy:.1f}%")
    print(f"total tokens: {records['tokens_used'].sum()}")
    print(f"tokens per classified: {records['tokens_used'].sum() / len(classified):.1f}")
    confusion = pd.crosstab(
        classified["true_category"], classified["category"], dropna=False
    )
    print("confusion table (true rows, predicted columns):")
    print(confusion.to_string())
    return accuracy


def print_redaction_counts(tickets):
    totals = {"email": 0, "phone": 0, "order_id": 0}
    redacted_texts = []
    for text in tickets["text"]:
        redacted, counts = redact(text)
        redacted_texts.append(redacted)
        for key, value in counts.items():
            totals[key] += value
    print("=== redaction counts ===")
    print(totals)
    print(f"total: {sum(totals.values())}")
    remaining = {
        "email": sum(bool(EMAIL_PATTERN.search(text)) for text in redacted_texts),
        "phone": sum(bool(PHONE_PATTERN.search(text)) for text in redacted_texts),
        "order_id": sum(bool(ORDER_PATTERN.search(text)) for text in redacted_texts),
    }
    print(f"remaining after redaction: {remaining}")
    assert sum(remaining.values()) == 0
    return totals


def route_records(records, segments):
    segments = segments.copy()
    segments["is_premium"] = (
        segments["is_premium"].astype(str).str.lower().eq("true")
    )
    segment_map = segments.set_index("customer_id")[["segment_name", "is_premium"]]
    rows = []
    for record in records.to_dict("records"):
        customer_id = record["customer_id"]
        segment_name = ""
        is_premium = False
        if customer_id in segment_map.index:
            segment_name = segment_map.loc[customer_id, "segment_name"]
            is_premium = bool(segment_map.loc[customer_id, "is_premium"])
        status = record["status"]
        category = record["category"]
        if status in {
            "skipped_empty",
            "flagged_long",
            "flagged_invalid_output",
            "budget_exhausted",
        }:
            route, priority = "human_review", "NORMAL"
        elif category == "fraud":
            route, priority = "security_team", "HIGH"
        elif is_premium:
            route, priority = "premium_desk", "HIGH"
        else:
            route, priority = "support_queue", "NORMAL"
        rows.append(
            {
                "ticket_id": record["ticket_id"],
                "customer_id": customer_id,
                "status": status,
                "category": category,
                "segment_name": segment_name,
                "priority": priority,
                "route": route,
                "tokens_used": record["tokens_used"],
            }
        )
    return pd.DataFrame(rows)


def main():
    tickets = pd.read_csv(DATA_RAW / "tickets.csv", dtype=str, keep_default_na=False)
    assert len(tickets) == 164
    empty = tickets["text"].str.strip().eq("").sum()
    long_count = sum(
        mock_llm.est_tokens(text) > MAX_INPUT_TOKENS for text in tickets["text"]
    )
    print(f"empty tickets: {empty}")
    print(f"long tickets: {long_count}")
    print(
        "long ticket token estimates: "
        f"{sorted({mock_llm.est_tokens(text) for text in tickets['text'] if mock_llm.est_tokens(text) > MAX_INPUT_TOKENS})}"
    )
    print_redaction_counts(tickets)

    zero_records, zero_stats = run_pipeline(tickets, ZERO_SHOT)
    assert zero_stats["transient_errors"] == 19
    assert zero_stats["calls"] + zero_stats["budget_exhausted"] + empty + long_count == 164
    zero_accuracy = evaluate(zero_records, "zero-shot")

    few_records, few_stats = run_pipeline(tickets, FEW_SHOT)
    assert few_stats["transient_errors"] == 19
    few_accuracy = evaluate(few_records, "few-shot")
    assert {
        "classified_json": int((few_records["status"] == "classified_json").sum()),
        "classified_keyword": int((few_records["status"] == "classified_keyword").sum()),
        "flagged_invalid_output": int((few_records["status"] == "flagged_invalid_output").sum()),
    } == {"classified_json": 135, "classified_keyword": 12, "flagged_invalid_output": 9}
    assert abs(zero_accuracy - 85.7) <= 0.5
    assert few_accuracy == 100.0

    budget = TOKEN_BUDGET
    budget_records, budget_stats = run_pipeline(tickets, ZERO_SHOT, budget=budget)
    if budget_stats["budget_exhausted"] == 0:
        budget = 5000
        budget_records, budget_stats = run_pipeline(tickets, ZERO_SHOT, budget=budget)
    assert budget_stats["budget_exhausted"] > 0
    print(f"\nbudget demo: {budget} tokens; exhausted {budget_stats['budget_exhausted']}")

    segments = pd.read_csv(OUTPUTS / "customer_segments.csv")
    budget_output = route_records(budget_records, segments)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    budget_output.to_csv(OUTPUTS / "triage_budget_demo.csv", index=False)

    final_records, final_stats = run_pipeline(tickets, FEW_SHOT, budget=100000)
    final_output = route_records(final_records, segments)
    final_output.to_csv(OUTPUTS / "triage_results.csv", index=False)
    print(f"final rows: {len(final_output)}")
    print(final_output["route"].value_counts().to_dict())
    print(final_output["status"].value_counts().to_dict())
    print(f"final transient errors: {final_stats['transient_errors']}")


if __name__ == "__main__":
    main()

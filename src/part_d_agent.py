import json
import sqlite3
import time
from datetime import datetime, timezone

import pandas as pd

import mock_llm
from src.config import (
    AGENT_MAX_ITERATIONS,
    AGENT_TIME_LIMIT_SECONDS,
    AGENT_TOKEN_LIMIT,
    DATA_RAW,
    DB_PATH,
    OUTPUTS,
    STATE_DIR,
)
from src.part_d_rag import retrieve

AGENT_RUNS = OUTPUTS / "agent_runs.jsonl"
LEDGER_PATH = OUTPUTS / "refund_ledger.jsonl"

SYSTEM_PROMPT = (
    "You are a refund AGENT. Use the available tools to look up the order, search "
    "the refund policy, calculate the refund, and then issue it or escalate it. "
    "Request one tool at a time and finish with a final answer beginning REFUND:, "
    "ESCALATE:, DENIED: or NOT_FOUND:."
)


class SimulatedCrash(Exception):
    pass


def get_order(order_id):
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT order_id, status, order_amount, delivery_minutes "
            "FROM orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()
    if row is None:
        return {"error": "order not found"}
    return {
        "order_id": row[0],
        "status": row[1],
        "order_amount": float(row[2]),
        "delivery_minutes": None if row[3] is None else int(row[3]),
    }


def search_policy(query):
    return {"results": retrieve(query, k=3)}


def calculate_refund(order_amount, delivery_minutes):
    refund = float(order_amount) if float(delivery_minutes) > 45 else 0.0
    return {"refund_inr": round(refund, 2)}


def _append_ledger(tool_name, order_id, refund_inr):
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool_name,
        "order_id": order_id,
        "refund_inr": round(float(refund_inr), 2),
    }
    with LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def issue_refund(order_id, refund_inr):
    _append_ledger("issue_refund", order_id, refund_inr)
    return {"refund_inr": round(float(refund_inr), 2)}


def escalate_to_human(order_id, refund_inr):
    _append_ledger("escalate_to_human", order_id, refund_inr)
    return {"refund_inr": round(float(refund_inr), 2)}


TOOLS_SPEC = [
    {
        "name": "get_order",
        "description": "Look up one order in the Instamart database.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "search_policy",
        "description": "Search the refund policy documents for relevant text.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "calculate_refund",
        "description": "Calculate the refund from order amount and delivery time.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_amount": {"type": "number"},
                "delivery_minutes": {"type": "number"},
            },
            "required": ["order_amount", "delivery_minutes"],
        },
    },
    {
        "name": "issue_refund",
        "description": "Issue an approved refund and record it in the ledger.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "refund_inr": {"type": "number"},
            },
            "required": ["order_id", "refund_inr"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate a refund above INR 1000 to a human lead.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "refund_inr": {"type": "number"},
            },
            "required": ["order_id", "refund_inr"],
        },
    },
]

TOOL_MAP = {
    "get_order": get_order,
    "search_policy": search_policy,
    "calculate_refund": calculate_refund,
    "issue_refund": issue_refund,
    "escalate_to_human": escalate_to_human,
}


def _save_checkpoint(run_id, scenario_id, messages, tokens, steps, tools, llm_calls):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "messages": messages,
        "tokens_used": tokens,
        "step_number": len(steps),
        "steps": steps,
        "tools_executed": tools,
        "llm_calls": llm_calls,
    }
    (STATE_DIR / f"{run_id}.json").write_text(
        json.dumps(payload, default=str), encoding="utf-8"
    )


def _fallback(status, summary, steps, llm_calls, tokens):
    return {
        "status": status,
        "final_answer": summary,
        "steps": steps,
        "llm_calls": llm_calls,
        "tokens_used": tokens,
    }


def _continue(
    messages,
    steps,
    tools,
    llm_calls,
    tokens,
    scenario_id,
    run_id,
    max_iterations,
    token_limit,
    time_limit_seconds,
    crash_after_steps=None,
):
    start = time.monotonic()
    while llm_calls < max_iterations:
        if time.monotonic() - start >= time_limit_seconds:
            return _fallback(
                "FALLBACK_TIMEOUT",
                "HANDOFF: the agent timed out; a human should review this refund request.",
                steps,
                llm_calls,
                tokens,
            )
        response = mock_llm.chat(messages, tools=TOOLS_SPEC)
        llm_calls += 1
        tokens += response.usage.total_tokens
        if tokens > token_limit:
            return _fallback(
                "FALLBACK_TOKEN_LIMIT",
                "HANDOFF: the token limit was reached; a human should review this refund request.",
                steps,
                llm_calls,
                tokens,
            )
        message = response.choices[0].message
        if not message.tool_calls:
            final = message.content or ""
            return {
                "status": final.split(":", 1)[0].strip(),
                "final_answer": final,
                "steps": steps,
                "llm_calls": llm_calls,
                "tokens_used": tokens,
            }
        messages.append(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": call.id,
                        "name": call.name,
                        "arguments": call.arguments,
                    }
                    for call in message.tool_calls
                ],
            }
        )
        for call in message.tool_calls:
            arguments = (
                call.arguments
                if isinstance(call.arguments, dict)
                else json.loads(call.arguments)
            )
            result = TOOL_MAP[call.name](**arguments)
            steps.append(
                {
                    "tool": call.name,
                    "arguments": arguments,
                    "observation": result,
                }
            )
            tools.append(call.name)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.name,
                    "content": json.dumps(result, default=str),
                }
            )
            _save_checkpoint(
                run_id, scenario_id, messages, tokens, steps, tools, llm_calls
            )
            if crash_after_steps is not None and len(steps) == crash_after_steps:
                raise SimulatedCrash(f"simulated crash after {len(steps)} tools")
    return _fallback(
        "FALLBACK_MAX_ITERATIONS",
        "HANDOFF: the maximum number of iterations was reached; a human should review this refund request.",
        steps,
        llm_calls,
        tokens,
    )


def run_agent(
    user_message,
    scenario_id,
    run_id=None,
    max_iterations=AGENT_MAX_ITERATIONS,
    token_limit=AGENT_TOKEN_LIMIT,
    time_limit_seconds=AGENT_TIME_LIMIT_SECONDS,
    crash_after_steps=None,
):
    if run_id is None:
        run_id = f"{scenario_id}_{int(time.time() * 1000)}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    return _continue(
        messages,
        [],
        [],
        0,
        0,
        scenario_id,
        run_id,
        max_iterations,
        token_limit,
        time_limit_seconds,
        crash_after_steps,
    )


def resume_agent(
    run_id,
    max_iterations=AGENT_MAX_ITERATIONS,
    token_limit=AGENT_TOKEN_LIMIT,
    time_limit_seconds=AGENT_TIME_LIMIT_SECONDS,
):
    payload = json.loads((STATE_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    return _continue(
        payload["messages"],
        payload["steps"],
        payload["tools_executed"],
        payload["llm_calls"],
        payload["tokens_used"],
        payload["scenario_id"],
        run_id,
        max_iterations,
        token_limit,
        time_limit_seconds,
    )


def refund_from_steps(steps):
    for step in steps:
        if step["tool"] == "calculate_refund":
            return float(step["observation"]["refund_inr"])
    return 0.0


def reset_run_outputs(clear_state=True):
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    for path in (AGENT_RUNS, LEDGER_PATH):
        if path.exists():
            path.unlink()
    if clear_state:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        for path in STATE_DIR.glob("*.json"):
            path.unlink()


def main():
    reset_run_outputs()
    scenarios = pd.read_csv(DATA_RAW / "agent_scenarios.csv", keep_default_na=False)
    s1_message = scenarios.loc[scenarios["scenario_id"] == "S1", "message"].iloc[0]

    token_demo = run_agent(
        s1_message, "S1", run_id="demo_token_limit", token_limit=200
    )
    timeout_demo = run_agent(
        s1_message, "S1", run_id="demo_timeout", time_limit_seconds=0
    )

    try:
        run_agent(
            s1_message,
            "S1",
            run_id="demo_crash_resume",
            crash_after_steps=2,
        )
    except SimulatedCrash:
        pass

    resumed = resume_agent("demo_crash_resume")

    agent_runs_path = AGENT_RUNS
    ledger_path = LEDGER_PATH
    for path in (agent_runs_path, ledger_path):
        if path.exists():
            path.unlink()

    results = []
    for row in scenarios.itertuples(index=False):
        result = run_agent(
            row.message,
            row.scenario_id,
            run_id=f"scenario_{row.scenario_id}",
        )
        refund = refund_from_steps(result["steps"])
        line = {
            "scenario_id": row.scenario_id,
            "status": result["status"],
            "final_answer": result["final_answer"],
            "llm_calls": result["llm_calls"],
            "tokens_used": result["tokens_used"],
            "refund_inr": round(refund, 2),
            "steps": result["steps"],
        }
        with AGENT_RUNS.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(line, default=str) + "\n")
        results.append(line)

    print("=== seven scenarios ===")
    for line in results:
        print(
            f"{line['scenario_id']}: {line['status']} refund={line['refund_inr']:.2f} "
            f"calls={line['llm_calls']} tokens={line['tokens_used']}"
        )

    expected = {
        "S1": ("REFUND", 128.25),
        "S2": ("REFUND", 135.00),
        "S3": ("ESCALATE", 1999.00),
        "S4": ("DENIED", 0.00),
        "S5": ("DENIED", 0.00),
        "S6": ("NOT_FOUND", 0.00),
        "S7": ("FALLBACK_MAX_ITERATIONS", 0.00),
    }
    for line in results:
        status, amount = expected[line["scenario_id"]]
        assert line["status"] == status, (line["scenario_id"], line["status"])
        assert abs(line["refund_inr"] - amount) < 0.01
    assert results[0]["llm_calls"] == 5
    assert results[6]["llm_calls"] == 6
    assert results[6]["tokens_used"] <= 6000

    print("\n=== stop safely ===")
    print(f"token_limit=200: {token_demo['status']}")
    print(f"time_limit_seconds=0: {timeout_demo['status']}")
    assert token_demo["status"] == "FALLBACK_TOKEN_LIMIT"
    assert timeout_demo["status"] == "FALLBACK_TIMEOUT"

    print("\n=== crash and resume ===")
    print(f"resumed status: {resumed['status']}")
    print(f"tools: {[step['tool'] for step in resumed['steps']]}")
    print(f"refund: {refund_from_steps(resumed['steps']):.2f}")
    assert [step["tool"] for step in resumed["steps"]] == [
        "get_order",
        "search_policy",
        "calculate_refund",
        "issue_refund",
    ]
    assert resumed["status"] == "REFUND"
    assert abs(refund_from_steps(resumed["steps"]) - 128.25) < 0.01

    with LEDGER_PATH.open(encoding="utf-8") as handle:
        ledger = [json.loads(line) for line in handle]
    print(f"ledger entries: {[entry['tool'] for entry in ledger]}")
    assert [entry["tool"] for entry in ledger] == [
        "issue_refund",
        "issue_refund",
        "escalate_to_human",
    ]


if __name__ == "__main__":
    main()

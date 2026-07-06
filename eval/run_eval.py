from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml

try:
    from .metrics import format_markdown_report, summarize_results
except ImportError:
    from metrics import format_markdown_report, summarize_results


DEFAULT_WORLD_STATE = {
    "location_id": "portfolio_whitebox_room",
    "game_time_label": "eval",
    "quest_stage": 0,
    "relationship_score": 0,
    "debug_enabled": True,
}
UNCERTAINTY_TERMS = [
    "无法确认",
    "不清楚",
    "不知道",
    "没有情报",
    "没有这份情报",
    "没有这项记录",
    "没有记录",
    "不了解",
    "无法判断",
    "难以确认",
]


def main() -> int:
    args = parse_args()
    backend = args.backend.rstrip("/")
    cases_dir = Path(args.cases)
    out_path = Path(args.out)
    json_out_path = Path(args.json_out) if args.json_out else out_path.with_suffix(".json")

    try:
        health = get_json(f"{backend}/api/v1/health", timeout=args.timeout)
    except Exception as exc:
        print(f"Backend health check failed: {exc}", file=sys.stderr)
        return 2
    if not health.get("ok"):
        print(f"Backend health check returned unexpected body: {health}", file=sys.stderr)
        return 2

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    case_specs = load_case_specs(cases_dir)
    case_results = [
        run_case(backend=backend, case=case, run_id=run_id, timeout=args.timeout)
        for case in case_specs
    ]
    report = {
        "schema_version": "npc_agent_eval_report.v1",
        "backend": backend,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metrics": summarize_results(case_results),
        "cases": case_results,
    }

    json_out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    json_out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    out_path.write_text(format_markdown_report(report), encoding="utf-8")

    failed = report["metrics"]["failed_cases"]
    print(f"Wrote {out_path} and {json_out_path}")
    print(f"Eval cases passed: {report['metrics']['passed_cases']}/{report['metrics']['case_count']}")
    return 0 if failed == 0 else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run NPC agent behavior evals against a local backend.")
    parser.add_argument("--backend", default="http://127.0.0.1:8008", help="Backend base URL.")
    parser.add_argument("--cases", default="eval/cases", help="Directory containing YAML eval cases.")
    parser.add_argument("--out", default="eval/reports/latest_report.md", help="Markdown report output path.")
    parser.add_argument("--json-out", default=None, help="JSON report output path.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Per-request timeout in seconds.")
    return parser.parse_args()


def load_case_specs(cases_dir: Path) -> List[Dict[str, Any]]:
    specs: List[Dict[str, Any]] = []
    for path in sorted(cases_dir.glob("*.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        suite = payload.get("suite") or path.stem
        for raw_case in payload.get("cases", []):
            case = dict(raw_case)
            case["suite"] = case.get("suite", suite)
            case["source_file"] = str(path)
            specs.append(case)
    return specs


def run_case(backend: str, case: Dict[str, Any], run_id: str, timeout: float) -> Dict[str, Any]:
    case_id = case["id"]
    npc_id = case["npc_id"]
    player_id = f"{case.get('player_id', case_id)}_{run_id}"
    session_id = f"eval_{case_id}_{run_id}"
    turns = normalize_turns(case)
    turn_results = []
    for index, turn in enumerate(turns, start=1):
        turn_id = turn.get("id", f"turn_{index}")
        started = time.perf_counter()
        response = post_dialogue(
            backend=backend,
            npc_id=npc_id,
            player_id=player_id,
            session_id=session_id,
            player_text=turn["player_text"],
            timeout=timeout,
        )
        latency_ms = (time.perf_counter() - started) * 1000
        turn_results.append(
            evaluate_turn(
                suite=case["suite"],
                case_id=case_id,
                turn_id=turn_id,
                response=response,
                expect=turn.get("expect", {}),
                latency_ms=latency_ms,
            )
        )
    passed = all(turn["status"] == "PASS" for turn in turn_results)
    return {
        "id": case_id,
        "suite": case["suite"],
        "npc_id": npc_id,
        "player_id": player_id,
        "source_file": case.get("source_file", ""),
        "passed": passed,
        "turns": turn_results,
    }


def normalize_turns(case: Dict[str, Any]) -> List[Dict[str, Any]]:
    if "turns" in case:
        return list(case["turns"])
    return [
        {
            "id": "turn_1",
            "player_text": case["player_text"],
            "expect": case.get("expect", {}),
        }
    ]


def post_dialogue(
    backend: str,
    npc_id: str,
    player_id: str,
    session_id: str,
    player_text: str,
    timeout: float,
) -> Dict[str, Any]:
    body = {
        "schema_version": "dialogue_request.v1",
        "session_id": session_id,
        "player_id": player_id,
        "npc_id": npc_id,
        "player_text": player_text,
        "distance_m": 1.2,
        "is_in_range": True,
        "world_state": dict(DEFAULT_WORLD_STATE),
    }
    return post_json(f"{backend}/api/v2/dialogue", body, timeout=timeout)


def evaluate_turn(
    suite: str,
    case_id: str,
    turn_id: str,
    response: Dict[str, Any],
    expect: Dict[str, Any],
    latency_ms: float,
) -> Dict[str, Any]:
    utterances = response.get("utterances", [])
    texts = [str(item.get("text", "")).strip() for item in utterances]
    response_text = "\n".join(text for text in texts if text)
    trace = response.get("trace", {}) or {}
    checks: Dict[str, bool | None] = {
        "format_valid": is_format_valid(texts),
        "persona_ok": None,
        "boundary_ok": None,
        "retrieval_hit": None,
        "tool_call_accuracy": None,
        "world_event_accuracy": None,
        "memory_recall": None,
        "quest_success": None,
    }

    text_contains_ok = contains_all(response_text, expect.get("text_contains", []))
    text_not_contains_ok = contains_none(response_text, expect.get("text_not_contains", []))
    if expect.get("text_contains"):
        checks["text_contains"] = text_contains_ok
    if expect.get("text_not_contains"):
        checks["text_not_contains"] = text_not_contains_ok

    expected_knowledge_ids = expect.get("expected_knowledge_ids", [])
    if expected_knowledge_ids:
        checks["retrieval_hit"] = contains_all(trace.get("used_knowledge_ids", []), expected_knowledge_ids)

    expected_tool_calls = expect.get("expected_tool_calls", [])
    if expected_tool_calls:
        checks["tool_call_accuracy"] = [call.get("tool_name") for call in trace.get("tool_calls", [])] == expected_tool_calls

    expected_world_events = expect.get("expected_world_events", [])
    if expected_world_events:
        checks["world_event_accuracy"] = [event.get("event_type") for event in response.get("world_events", [])] == expected_world_events

    expected_memory_suffixes = expect.get("expected_used_memory_id_suffixes", [])
    if expected_memory_suffixes:
        checks["used_memory_id_suffixes"] = suffixes_present(trace.get("used_memory_ids", []), expected_memory_suffixes)

    expected_candidate_types = expect.get("expected_memory_candidate_types", [])
    if expected_candidate_types:
        checks["memory_candidate_types"] = [
            candidate.get("memory_type") for candidate in trace.get("memory_candidates", [])
        ] == expected_candidate_types

    if suite == "persona":
        checks["persona_ok"] = checks["format_valid"] and text_not_contains_ok
    if suite == "rag_boundary":
        checks["boundary_ok"] = (
            checks["format_valid"]
            and text_not_contains_ok
            and any(term in response_text for term in UNCERTAINTY_TERMS)
        )
    if suite == "memory" and (expect.get("text_contains") or expected_memory_suffixes):
        suffix_ok = bool(checks.get("used_memory_id_suffixes", True))
        checks["memory_recall"] = checks["format_valid"] and text_contains_ok and suffix_ok
    if suite == "quest_flow":
        checks["quest_success"] = (
            checks["format_valid"]
            and checks.get("tool_call_accuracy", True) is not False
            and checks.get("world_event_accuracy", True) is not False
        )

    if expect.get("expected_reflection_absent") is True:
        checks["reflection_absent"] = trace.get("reflection") is None
    if expect.get("expected_reflection_failure_reason"):
        reflection = trace.get("reflection") or {}
        checks["reflection_failure_reason"] = reflection.get("failure_reason") == expect["expected_reflection_failure_reason"]

    failures = [name for name, value in checks.items() if value is False]
    return {
        "id": turn_id,
        "case_id": case_id,
        "status": "PASS" if not failures else "FAIL",
        "latency_ms": latency_ms,
        "response_text": response_text,
        "checks": checks,
        "failures": failures,
        "trace_summary": {
            "intent": (trace.get("plan") or {}).get("intent"),
            "used_knowledge_ids": trace.get("used_knowledge_ids", []),
            "used_memory_ids": trace.get("used_memory_ids", []),
            "tool_calls": [call.get("tool_name") for call in trace.get("tool_calls", [])],
            "world_events": [event.get("event_type") for event in response.get("world_events", [])],
            "reflection": trace.get("reflection"),
        },
    }


def get_json(url: str, timeout: float) -> Dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, body: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{url} returned HTTP {exc.code}: {detail}") from exc


def is_format_valid(texts: List[str]) -> bool:
    if not 1 <= len([text for text in texts if text]) <= 3:
        return False
    return not any(re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", text) for text in texts)


def contains_all(value: Any, expected: List[str]) -> bool:
    if not expected:
        return True
    if isinstance(value, list):
        value_set = {str(item) for item in value}
        return all(item in value_set for item in expected)
    text = str(value)
    return all(item in text for item in expected)


def contains_none(text: str, forbidden: List[str]) -> bool:
    return all(item not in text for item in forbidden)


def suffixes_present(values: List[str], suffixes: List[str]) -> bool:
    return all(any(str(value).endswith(suffix) for value in values) for suffix in suffixes)


def safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    return safe[:40] or "player"


if __name__ == "__main__":
    raise SystemExit(main())

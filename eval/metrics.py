from __future__ import annotations

from typing import Any, Dict, Iterable, List


CHECK_TO_METRIC = {
    "persona_ok": "persona_pass_rate",
    "boundary_ok": "boundary_pass_rate",
    "retrieval_hit": "retrieval_hit_rate",
    "tool_call_accuracy": "tool_call_accuracy",
    "world_event_accuracy": "world_event_accuracy",
    "memory_recall": "memory_recall_rate",
    "format_valid": "format_valid_rate",
    "quest_success": "quest_success_rate",
}


def summarize_results(case_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    turn_results = [turn for case in case_results for turn in case.get("turns", [])]
    metrics: Dict[str, Any] = {
        "case_count": len(case_results),
        "turn_count": len(turn_results),
        "passed_cases": sum(1 for case in case_results if case.get("passed")),
        "failed_cases": sum(1 for case in case_results if not case.get("passed")),
        "average_latency_ms": _average(turn.get("latency_ms", 0.0) for turn in turn_results),
    }
    for check_name, metric_name in CHECK_TO_METRIC.items():
        values = [
            bool(turn.get("checks", {}).get(check_name))
            for turn in turn_results
            if turn.get("checks", {}).get(check_name) is not None
        ]
        metrics[metric_name] = _rate(values)
    metrics["overall_case_pass_rate"] = _rate([bool(case.get("passed")) for case in case_results])
    return metrics


def format_markdown_report(report: Dict[str, Any]) -> str:
    metrics = report["metrics"]
    lines = [
        "# NPC Agent Evaluation Report",
        "",
        f"- Backend: `{report['backend']}`",
        f"- Generated at: `{report['generated_at']}`",
        f"- Cases: {metrics['case_count']} ({metrics['passed_cases']} passed, {metrics['failed_cases']} failed)",
        f"- Turns: {metrics['turn_count']}",
        f"- Average latency: {metrics['average_latency_ms']:.1f} ms",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in [
        "overall_case_pass_rate",
        "persona_pass_rate",
        "boundary_pass_rate",
        "retrieval_hit_rate",
        "tool_call_accuracy",
        "world_event_accuracy",
        "memory_recall_rate",
        "format_valid_rate",
        "quest_success_rate",
    ]:
        value = metrics.get(key)
        rendered = "n/a" if value is None else f"{value * 100:.1f}%"
        lines.append(f"| {key} | {rendered} |")

    lines.extend(["", "## Case Results", ""])
    for case in report["cases"]:
        status = "PASS" if case.get("passed") else "FAIL"
        lines.append(f"### {status} `{case['id']}`")
        lines.append("")
        lines.append(f"- Suite: `{case['suite']}`")
        for turn in case.get("turns", []):
            text = turn.get("response_text", "").replace("\n", " / ")
            lines.append(
                f"- Turn `{turn['id']}`: {turn['status']} in {turn['latency_ms']:.1f} ms, response: {text}"
            )
            failures = turn.get("failures", [])
            if failures:
                lines.append(f"- Failures: {', '.join(failures)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _rate(values: List[bool]) -> float | None:
    if not values:
        return None
    return sum(1 for value in values if value) / len(values)


def _average(values: Iterable[float]) -> float:
    collected = list(values)
    if not collected:
        return 0.0
    return sum(collected) / len(collected)

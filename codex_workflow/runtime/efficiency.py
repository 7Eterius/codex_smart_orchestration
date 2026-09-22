#!/usr/bin/env python3
"""Read-only Smart Orchestration API price reference, configuration and pacing tools.

No network, model calls, transcript access or writes. API token prices are only a
relative economics reference; they are NOT a conversion to ChatGPT/Codex plan quota.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import sys
import tomllib

AS_OF = "2026-09-22"
RATE_SOURCE = "https://developers.openai.com/api/docs/models/compare"
MODEL_SELECTION_SOURCE = "https://developers.openai.com/api/docs/guides/model-selection"
# Standard API text-token rates per million for requests at <=272K input tokens.
# Cache-write, regional, tool-call and service-tier costs are intentionally omitted.
RATES = {
    "gpt-6-luna": (Decimal("0.10"), Decimal("0.01"), Decimal("0.50")),
    "gpt-6-sol": (Decimal("2.00"), Decimal("0.20"), Decimal("10.00")),
    "gpt-6-astra": (Decimal("10.00"), Decimal("1.00"), Decimal("50.00")),
    # Legacy comparison points for migration economics only.
    "gpt-5.6-luna": (Decimal("0.20"), Decimal("0.02"), Decimal("1.20")),
    "gpt-5.6-sol": (Decimal("4.00"), Decimal("0.40"), Decimal("20.00")),
}
ROLES = ("simple_executor", "routine_executor", "default_executor", "senior_executor",
         "tester", "companion", "investigator", "archivist")
DISCLAIMER = (
    "Dated Standard API short-context token-price reference, not a bill or a "
    "ChatGPT/Codex weekly-quota estimate. It excludes cache writes, tool charges, "
    "regional processing and service-tier multipliers. Requests above 272K input "
    "tokens use different full-request multipliers, so aggregated session tokens "
    "cannot be repriced safely without request boundaries. Verify rates before later use."
)


def number(raw: str) -> Decimal:
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("Expected a finite number") from exc
    if not value.is_finite():
        raise argparse.ArgumentTypeError("Expected a finite number")
    return value


def count(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def reference(model: str, total_input: int, cached_input: int, output: int) -> dict:
    """Input includes cached tokens, matching the deployment reporter contract."""
    for value, label in ((total_input, "input"), (cached_input, "cached input"), (output, "output")):
        count(value, label)
    if cached_input > total_input:
        raise ValueError("Cached input is a subset of total input")
    if model not in RATES:
        raise ValueError("Unknown model; no inferred rate or fallback")
    input_rate, cache_rate, output_rate = RATES[model]
    usd = (Decimal(total_input - cached_input) * input_rate
           + Decimal(cached_input) * cache_rate
           + Decimal(output) * output_rate) / Decimal(1_000_000)
    return {
        "model": model,
        "api_standard_short_context_usd_reference": str(usd),
        "input_tokens_including_cached": total_input,
        "cached_input_tokens": cached_input,
        "output_tokens": output,
        "rate_as_of": AS_OF,
        "rate_source": RATE_SOURCE,
        "included_weekly_allowance_percent": None,
        "limitation": DISCLAIMER,
    }


def pace(remaining: Decimal, workdays_left: int, reserve: Decimal) -> dict:
    for value in (remaining, reserve):
        if not isinstance(value, Decimal) or not value.is_finite() or not 0 <= value <= 100:
            raise ValueError("Percentages must be finite and between 0 and 100")
    if isinstance(workdays_left, bool) or not isinstance(workdays_left, int) or workdays_left < 1:
        raise ValueError("workdays_left must be a positive integer")
    spendable = max(Decimal(0), remaining - reserve)
    return {
        "observed_remaining_percent": str(remaining),
        "reserve_percent": str(reserve),
        "workdays_left": workdays_left,
        "daily_percentage_point_budget": str((spendable / workdays_left).quantize(Decimal("0.01"))),
        "reserve_shortfall_percentage_points": str(max(Decimal(0), reserve - remaining)),
        "limitation": "Arithmetic from your dashboard observation, not a forecast of productivity. "
                      "Includes all work drawing on the shared pool. Never skip required checks to fit this budget.",
    }


def settings(home: Path) -> dict:
    """Show only configuration fields useful for cost diagnosis, never secrets."""
    home = home.expanduser()
    path = home / "config.toml"
    if path.is_symlink():
        raise ValueError("Config is symlinked; inspect it explicitly instead")
    cfg = tomllib.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    result = {
        "configured_parent": {key: cfg.get(key) for key in
            ("model", "model_reasoning_effort", "plan_mode_reasoning_effort", "service_tier")},
        "workers": [],
        "warnings": [],
    }
    for role in ROLES:
        path = home / "agents" / f"{role}.toml"
        if path.is_symlink():
            raise ValueError(f"Worker configuration is symlinked: {role}")
        worker = tomllib.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        result["workers"].append({
            "role": role,
            "file_present": path.is_file(),
            **{key: worker.get(key) for key in ("model", "model_reasoning_effort", "service_tier")},
        })
    if cfg.get("service_tier") in {"fast", "priority"}:
        result["warnings"].append("Fast mode configured; Standard is the workflow's cost-conscious baseline.")
    profiles = cfg.get("profiles", {})
    if isinstance(profiles, dict):
        for profile in profiles.values():
            if isinstance(profile, dict) and any(key in profile for key in
                    ("model", "model_reasoning_effort", "plan_mode_reasoning_effort",
                     "service_tier", "developer_instructions")):
                result["warnings"].append(
                    "A profile can override model/effort/speed/bootstrap; verify the selected profile."
                )
                break
    result["observation"] = (
        "On-disk configuration only. Null is unknown/inherited, not verified Standard speed. "
        "Unset Plan effort uses its built-in preset, not an inferred normal effort. "
        "Project, profile, CLI or spawn overrides may change actual settings. No live usage was read."
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("rates", help="Print the dated Standard API short-context price reference")
    comparison = sub.add_parser(
        "compare",
        help="Compare one identical short-context token workload; not a plan-quota estimate",
    )
    comparison.add_argument("--input-tokens", type=int, required=True, help="Total input INCLUDING cached subset")
    comparison.add_argument("--cached-input-tokens", type=int, required=True)
    comparison.add_argument("--output-tokens", type=int, required=True,
                            help="Recorded output; reasoning output is already included where applicable")
    comparison.add_argument("--model", choices=tuple(RATES), action="append")
    pacing = sub.add_parser("pace", help="Budget an observed remaining WEEKLY percentage over working days")
    pacing.add_argument("--remaining-percent", type=number, required=True)
    pacing.add_argument("--workdays-left", type=int, required=True)
    pacing.add_argument("--reserve-percent", type=number, default=Decimal(15))
    config = sub.add_parser("settings", help="Show selected on-disk fields only; no transcript or secret output")
    config.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", "~/.codex")))
    args = parser.parse_args(argv)
    try:
        if args.command == "rates":
            result = {
                "as_of": AS_OF,
                "source": RATE_SOURCE,
                "model_selection_source": MODEL_SELECTION_SOURCE,
                "units": "USD per 1M text tokens, Standard API, <=272K request input",
                "rates": {
                    model: dict(zip(("uncached_input", "cached_input", "output"), map(str, rates)))
                    for model, rates in RATES.items()
                },
                "limitation": DISCLAIMER,
            }
        elif args.command == "compare":
            result = {
                "comparisons": [
                    reference(model, args.input_tokens, args.cached_input_tokens, args.output_tokens)
                    for model in dict.fromkeys(args.model or RATES)
                ]
            }
        elif args.command == "pace":
            result = pace(args.remaining_percent, args.workdays_left, args.reserve_percent)
        else:
            result = settings(args.codex_home)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc), "writes_performed": 0}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

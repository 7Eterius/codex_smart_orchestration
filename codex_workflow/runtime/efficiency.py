#!/usr/bin/env python3
"""Read-only Smart Orchestration Work/Codex credit reference and diagnostics.

No network, model calls, transcript access or writes. Published credit rates and
message estimates are useful relative economics, not a conversion to an account's
remaining included allowance. Local/cloud use is shared and weekly limits may apply.
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
CREDIT_SOURCE = "https://developers.openai.com/codex/pricing"
MODEL_SOURCE = "https://openai.com/index/introducing-gpt-6-sol-and-luna/"
CREDIT_RATES = {
    "gpt-6-luna": (Decimal("2.5"), Decimal("0.25"), Decimal("12.5")),
    "gpt-6-sol": (Decimal("50"), Decimal("5"), Decimal("250")),
    "gpt-6-astra": (Decimal("250"), Decimal("25"), Decimal("1250")),
    "gpt-5.6-luna": (Decimal("5"), Decimal("0.5"), Decimal("30")),
    "gpt-5.6-terra": (Decimal("50"), Decimal("5"), Decimal("300")),
    "gpt-5.6-sol": (Decimal("100"), Decimal("10"), Decimal("500")),
}
# Compatibility alias for existing local callers. These are Work/Codex credits,
# not the API-dollar rates used before v1.6.2.
RATES = CREDIT_RATES
FAST_MULTIPLIER = Decimal("2.5")
FAST_MODELS = frozenset(("gpt-6-luna", "gpt-6-sol", "gpt-6-astra"))
MESSAGE_ESTIMATES = {
    "gpt-6-astra": {"plus": "5-45", "pro_5x": "25-225", "pro_20x": "100-900"},
    "gpt-6-sol": {"plus": "15-150", "pro_5x": "70-700", "pro_20x": "300-3,000"},
    "gpt-6-luna": {"plus": "350-3,000", "pro_5x": "1,750-14,000", "pro_20x": "7,000-56,000"},
}
ROLES = ("simple_executor", "routine_executor", "default_executor", "senior_executor",
         "tester", "companion", "investigator", "archivist")
DISCLAIMER = (
    "Dated Work/Codex credit reference, not a bill or included-plan quota meter. "
    "Actual message usage varies with task complexity, context, tools and reasoning. "
    "Local messages and cloud chats share plan usage; weekly limits may also apply. "
    "Credit purchases/overages and plan limits are distinct. Verify current docs later."
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


def reference(model: str, total_input: int, cached_input: int, output: int,
              speed: str = "standard") -> dict:
    """Input includes cached tokens, matching the deployment reporter contract."""
    for value, label in ((total_input, "input"), (cached_input, "cached input"), (output, "output")):
        count(value, label)
    if cached_input > total_input:
        raise ValueError("Cached input is a subset of total input")
    if model not in CREDIT_RATES:
        raise ValueError("Unknown model; no inferred rate or fallback")
    if speed not in {"standard", "fast"}:
        raise ValueError("speed must be standard or fast")
    if speed == "fast" and model not in FAST_MODELS:
        raise ValueError("No current published Fast multiplier for this model")
    input_rate, cache_rate, output_rate = CREDIT_RATES[model]
    standard = (Decimal(total_input - cached_input) * input_rate
                + Decimal(cached_input) * cache_rate
                + Decimal(output) * output_rate) / Decimal(1_000_000)
    multiplier = FAST_MULTIPLIER if speed == "fast" else Decimal(1)
    effective = standard * multiplier
    return {
        "model": model,
        "speed": speed,
        "standard_credit_reference": str(standard),
        "effective_credit_reference": str(effective),
        "speed_multiplier": str(multiplier),
        "input_tokens_including_cached": total_input,
        "cached_input_tokens": cached_input,
        "output_tokens": output,
        "rate_as_of": AS_OF,
        "rate_source": CREDIT_SOURCE,
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
        "limitation": "Arithmetic from a dashboard observation, not a productivity forecast. "
                      "Never skip required checks to fit this budget.",
    }


def settings(home: Path) -> dict:
    """Show selected cost-relevant configuration fields without secrets."""
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
        "relative_credit_economics": {
            "sol_vs_luna_per_token": "20x",
            "astra_vs_luna_per_token": "100x",
            "gpt6_fast_vs_standard": "2.5x",
        },
    }
    for role in ROLES:
        role_path = home / "agents" / f"{role}.toml"
        if role_path.is_symlink():
            raise ValueError(f"Worker configuration is symlinked: {role}")
        worker = tomllib.loads(role_path.read_text(encoding="utf-8")) if role_path.is_file() else {}
        result["workers"].append({
            "role": role,
            "file_present": role_path.is_file(),
            **{key: worker.get(key) for key in ("model", "model_reasoning_effort", "service_tier")},
        })
    if cfg.get("service_tier") in {"fast", "priority"}:
        result["warnings"].append(
            "Fast/priority speed is configured. GPT-6 Fast uses 2.5x the Standard "
            "credit rate where supported; owner setting preserved."
        )
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
        "On-disk configuration only. Null is unknown/inherited. Project, profile, "
        "CLI or spawn overrides may change actual settings. No live usage was read."
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("rates", help="Print dated Work/Codex credit rates and plan estimates")
    comparison = sub.add_parser("compare", help="Compare an identical token workload in Work/Codex credits")
    comparison.add_argument("--input-tokens", type=int, required=True, help="Total input INCLUDING cached subset")
    comparison.add_argument("--cached-input-tokens", type=int, required=True)
    comparison.add_argument("--output-tokens", type=int, required=True)
    comparison.add_argument("--model", choices=tuple(CREDIT_RATES), action="append")
    comparison.add_argument("--speed", choices=("standard", "fast"), default="standard")
    pacing = sub.add_parser("pace", help="Budget an observed remaining weekly percentage over workdays")
    pacing.add_argument("--remaining-percent", type=number, required=True)
    pacing.add_argument("--workdays-left", type=int, required=True)
    pacing.add_argument("--reserve-percent", type=number, default=Decimal(15))
    config = sub.add_parser("settings", help="Show selected on-disk fields only; no secret output")
    config.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", "~/.codex")))
    args = parser.parse_args(argv)
    try:
        if args.command == "rates":
            result = {
                "as_of": AS_OF,
                "source": CREDIT_SOURCE,
                "model_source": MODEL_SOURCE,
                "units": "Work/Codex credits per 1M tokens at Standard speed",
                "rates": {
                    model: dict(zip(("uncached_input", "cached_input", "output"), map(str, rates)))
                    for model, rates in CREDIT_RATES.items()
                },
                "fast_multiplier": str(FAST_MULTIPLIER),
                "message_estimates_per_five_hours": MESSAGE_ESTIMATES,
                "limitation": DISCLAIMER,
            }
        elif args.command == "compare":
            result = {
                "comparisons": [
                    reference(model, args.input_tokens, args.cached_input_tokens,
                              args.output_tokens, args.speed)
                    for model in dict.fromkeys(args.model or CREDIT_RATES)
                    if args.speed == "standard" or model in FAST_MODELS
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

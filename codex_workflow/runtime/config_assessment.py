"""Read-only configuration assessment; recommendations never establish live selection."""
from __future__ import annotations
from typing import Any
from .agent_defaults import DEFAULTS

PARENT_FIELDS = ("model", "model_reasoning_effort", "plan_mode_reasoning_effort", "service_tier")
MAIN_BASELINE = {"model": "gpt-6.1-sol", "model_reasoning_effort": "medium"}
SOL_61_EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max"})


def assess_configuration(cfg: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    unverified = [
        "Live agent availability, selected child models and history isolation were not observed.",
        "Owner-dispatched review, native thread release and pause propagation were not observed.",
        "Profile, project, command-line and per-spawn overrides were not resolved.",
    ]
    tables: dict[str, dict[str, Any]] = {}
    for key in ("agents", "features", "profiles"):
        value = cfg.get(key, {})
        if not isinstance(value, dict):
            errors.append(f"[{key}] must be a table.")
            value = {}
        tables[key] = value
    agents = tables["agents"]
    if "enabled" in agents and not isinstance(agents["enabled"], bool):
        errors.append("agents.enabled must be boolean.")
    elif agents.get("enabled") is False:
        errors.append("Subagents are explicitly disabled by agents.enabled=false; enable deliberately before installing.")
    caps = ("max_threads", "max_concurrent_threads_per_session")
    if all(key in agents for key in caps):
        errors.append("Both concurrency aliases are set; reconcile them before installing.")
    for key in caps:
        if key in agents:
            value = agents[key]
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                errors.append(f"agents.{key} must be a positive integer.")
    cap = agents.get(caps[1], agents.get(caps[0]))
    if cap is None:
        warnings.append("No concurrency cap is established in this configuration; live default is unverified.")
    elif isinstance(cap, int) and not isinstance(cap, bool) and cap > 3:
        warnings.append("Explicit concurrency above 3 is preserved; Smart targets at most two owned open threads across the run, respecting lower limits and other work.")
    for key in ("default_subagent_model", "default_subagent_reasoning_effort"):
        value = agents.get(key)
        if key in agents and (not isinstance(value, str) or not value.strip()):
            errors.append(f"agents.{key} must be a nonempty string.")
        elif value != DEFAULTS[key]:
            warnings.append(f"agents.{key} is absent or differs from the economical fallback; no live selection is inferred.")
    for key in ("multi_agent", "multi_agent_v2"):
        if key in tables["features"]:
            value = tables["features"][key]
            disabled = value is False or (isinstance(value, dict) and value.get("enabled") is False)
            state = "explicitly false" if disabled else "configured"
            warnings.append(f"features.{key} is {state}; compatibility is client/version-dependent and the setting is preserved.")
            unverified.append(f"The effect of features.{key} on the active backend was not determined.")
    parent = {}
    for key in PARENT_FIELDS:
        value = cfg.get(key)
        if key in cfg and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{key} must be a nonempty string when set.")
            value = None
        parent[key] = value
    if parent["service_tier"] in ("fast", "priority"):
        warnings.append("Fast mode configured; review allowance cost. No speed setting was changed.")
    if parent["plan_mode_reasoning_effort"] is None:
        unverified.append("Plan-mode effort is unset here; its built-in preset was not observed and is not inferred from normal effort.")
    baseline_status = "matches" if all(parent[k] == v for k, v in MAIN_BASELINE.items()) else "different_or_unset"
    if baseline_status != "matches":
        warnings.append("Recommended Main baseline is gpt-6.1-sol/medium. Existing parent/profile selections are preserved; select it explicitly where available.")
    # Validate only this known model contract, not an invented global model catalog.
    if parent["model"] == "gpt-6.1-sol":
        for key in ("model_reasoning_effort", "plan_mode_reasoning_effort"):
            effort = parent[key]
            if effort is not None and effort not in SOL_61_EFFORTS:
                errors.append(f"{key} is unsupported for gpt-6.1-sol; choose low, medium, high, xhigh or max explicitly.")
    for profile in tables["profiles"].values():
        if isinstance(profile, dict) and any(key in profile for key in PARENT_FIELDS + ("developer_instructions", "agents", "features")):
            warnings.append("A configured profile may override model, normal/Plan effort, speed or agent settings; selected profile is unverified.")
            break
    return {
        "errors": errors, "warnings": warnings, "unverified": unverified,
        "configured_parent": parent,
        "recommended_parent": dict(MAIN_BASELINE),
        "parent_baseline_status": baseline_status,
        "configured_child_defaults": {key: agents.get(key) for key in DEFAULTS},
        "effective_configured_cap": cap,
        "ok": not errors,
        "assessment_scope": "Supplied on-disk configuration only; ok means no detected errors, not live activation.",
    }

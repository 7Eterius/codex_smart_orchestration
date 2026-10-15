# Offline Smart weekly collector 1.2.0

Run on your own Mac with Python 3.11+: `python3 smart_weekly_stats.py --days 7`.
No extra packages, network, model calls or configuration/project edits are used. New reports
are created outside CODEX_HOME. Keep local-index.PRIVATE.json private; inspect SHARE-summary.zip
before sharing usage metadata. Never mix the report with another run's private index.

To inspect the same historical window as the 4.0.1 audit:

```sh
python3 smart_weekly_stats.py --since 2026-10-08T16:49:24.548748Z --until 2026-10-15T16:49:24.548748Z --timezone Asia/Tbilisi --all-files --max-line-mib 64
```

1.2 corrects ancestor-turn replay attribution, test words inside status inspections, and zero
wrapper exits that conflict with nonzero embedded exit markers. It preserves original exits
and reports test outcomes as unverified rather than claiming zero means a test passed. It
cannot reconstruct unavailable historical open residency, encrypted assignments or absent artifacts.
Role tags may describe several later duties and are not pure-role work or efficiency labels.

The command recognizer intentionally handles only a conservative executable-position shell subset.
Unknown wrappers, substitutions, heredocs and arbitrary JavaScript are not executed or guessed.
Repeated commands are candidates, not measured waste. The first up to 100 pairs include both
source/line references; they are ordered, not random. Inspect input identity and real runner
results locally before judging repeats. Initial/precreation parent payload times are not child work.
No computed overlap proves continuous model concurrency or compliance with a native open-thread cap.

Token counters retain response-ID de-duplication and existing cache/reasoning subset semantics.
There is no billing conversion or causal quality score. Native wrapper plus nested calls are not
separate model requests. Account-level quota snapshots can include activity outside these logs.
Unknown, deleted, unsupported, remote or omitted records remain outside the evidence.

Tests: `python3 -B -m unittest discover -s tools/stats -p 'test_*.py' -v` from source root.
The synthetic fixtures include the reported failure mechanisms without any private source logs.
This is an optional source tool, not an installed agent bootstrap, daemon or telemetry requirement.

## Collector 1.2.1

Malformed duration strings are unavailable evidence, not fatal parser exceptions. Exact workflow
markers (including 4.2.0/4.2.1) are separate from series-only markers and mixed versions. These are
session associations, not proof of per-call activation. The audit's copied-parent-turn correction
and native occupancy uncertainty remain unchanged. No raw logs are automatically rerun.

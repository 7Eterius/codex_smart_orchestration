# Scoped standards and evaluated review

Use project standards only where relevant; they do not replace original requirements or imply
another reviewer. Keep Smart's orchestration rules separate from product-specific architecture,
copy and visual choices. Reuse the project's existing authoritative standards location.

## Make the rule concrete before editing

Prefer prevention in architecture/types, then an executable test/lint/validator, then semantic or
visual judgment. Define the specific mistake, correction, applicable scope, reference example,
exceptions, severity and required evidence. Do not import another product's aesthetic preferences.
A root change can affect consumers elsewhere; include impacted paths, not just changed filenames.
Unknown impact widens selection rather than silently excluding a required rule.

The optional review_rules.py reads an explicitly selected JSON catalog, returns relevant compact
rules without their fixture corpus, and fingerprints rules plus cases. Scope paths are canonical
repository-relative prefixes, not guessed glob semantics. No command, hook, network or model is
invoked. No catalog is required for a typo. Do not duplicate rules across AGENTS.md, skills and JSON;
reference the controlling definition. Project standards cannot relax permissions or required gates.

## One independent review, actionable evidence

The existing appropriate Reviewer checks original requirements, the actual candidate and applicable
standards in one spec/quality pass. Return rule ID, compliant/violation/unverified/not-applicable,
supporting evidence and the needed correction. Not-applicable requires an actual exception/scope
reason. Optional style preferences are advisory, not correctness blockers. Missing required evidence
stays unresolved. A high probability from a classifier is not proof or an acceptance decision.

Valid checks and same-reviewer correction context can be reused for unchanged relevant inputs.
Review the complete correction delta and affected dependencies; a catalog change invalidates its
prior assessment. Never weaken standards or fixtures just to approve the implementation. A new
unlisted defect still matters; a short rule list is not complete requirements coverage.

## Evaluate the rule and reviewer separately

Use labelled violating, corrected, harmless-neighbor, permitted-exception and insufficient-evidence
cases. Include held-out cases; do not tune on the holdout. For visuals record comparable viewport,
state, theme and approved reference. Labels need human/independent review, not automatic acceptance
of a model's preference. Synthetic fixtures validate plumbing, not real-world reviewer capability.

fixture-inputs emits case questions without expected labels. score evaluates separately collected,
explicitly attributed model/effort predictions against the catalog digest. It reports missing
cases, mistakes, abstentions and development/holdout counts. It never calls a model or infers a
quota saving. Run a small comparison only when reviewer calibration is actually requested or a
verified repeated miss justifies it. No recurring model bake-off or new standing review role.

## Promote verified lessons, not every error

A reproducible defect usually deserves a regression test. A mechanical invariant deserves a
validator. A stable non-obvious convention belongs in the correct project instruction scope.
Temporary environment issues and hypotheses belong in the task checkpoint. A global Smart change
requires an independently supported general lesson and a reviewed patch. Preserve concise rules;
remove superseded duplicates through authorized maintenance, not automatic worker edits.

The Jev/Perplexity article informs this method, but neither service is installed or called. Any
future external classification is opt-in, uses approved data and must show net benefit against the
same labelled cases. Keep sensitive code, screenshots and private audits local unless authorized.

Evaluation fixture-inputs --compact emits schema 2: complete rules once, label-free cases by
reference. Expanded inputs remain default. Optional prediction split=development or split=holdout
limits completeness to that split; omission scores all cases. Results retain run_ref, not model
qualification. Catalog/prediction CLI reads allow 4 MiB; handoffs stay at 64 KiB.

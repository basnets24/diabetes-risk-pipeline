# Risk Register — CDRAP (Top 3)
## Risk 1: Small cohort noise inflates prevalence in rare combinations
**Why it matters:** Could produce misleading "high risk" cohorts that are too small to act on.
**Mitigation:**
- Enforce minimum cohort size threshold (>=500) for ranked outputs
- Always include cohort size + diabetes count in evidence tables
- Provide both pre-filter and post-filter counts

## Risk 2: Dirty categories / invalid numeric ranges break bucket logic and cohort assignment
**Why it matters:** Incorrect bucket assignment → incorrect cohort prevalence.
**Mitigation:**
- Validation checks for numeric ranges (age, BMI, HbA1c, glucose)
- Category cleaning summaries (unknown/rare values) as assumption test artifact
- Fail pipeline if invalid values exceed a set threshold (configurable)

## Risk 3: Reproducibility and ops proof fail (missing evidence, logs, or unstable run)
**Why it matters:** Deliverable fails course requirements even if analysis is correct.
**Mitigation:**
- Single entry script (run_sprint3.sh) generates ALL evidence deterministically
- Write run log via `tee` and separate stderr to out/errors.log
- Add simple “artifact existence checks” at end of script; fail if missing

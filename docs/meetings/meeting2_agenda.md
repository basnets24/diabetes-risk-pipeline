# Meeting 2: Decision Review and Finalize Brief


File path: docs/meetings/meeting2_agenda.md
Team: Team10
Date/Time: 2026-03-08 9:00 PM
Duration: 60 minutes
Facilitator (PM): Justin Tan
Notetaker: Krish Makwana

Goal of the meeting:
Review evidence artifacts, agree on a recommendation, and finalize the Decision Brief and Action Plan.

1) Status check (5 min)

- What artifacts are complete? out/evidence/
out/evidence/data_quality_report.txt
out/evidence/cohort_prevalence_summary.csv
out/evidence/ranked_high_risk_profiles.csv
out/evidence/location_prevalence_profile.csv
out/evidence/risk_rule_flags.csv
out/evidence/assumption_test_category_distinct_sample.txt

- What is blocked?
- Pandas (python library) missing on the virtual machine.Since we were     using dataframes to handle the CSV tables, we had to convert that functionality to base Python.

2) Evidence walkthrough (20 to 25 min)
For each artifact:
- What does it show (one sentence)?
- Why does it matter to the decision?
- Any caveats?

Artifacts:

**A1**: out/evidence/cohort_prevalence_summary.csv
- It shows the diabetes prevalence rates broken down across all demographic and clinical dimensions including age bucket, BMI bucket, gender, race, smoking history, hypertension, heart disease and location.
- Why it matters: This is the foundation of the entire analysis. It allows the Director to see which individual dimensions are most associated with diabetes prevalence above the 8.5% baseline.
- Caveats: No major caveats.

**A2**: out/evidence/ranked_high_risk_profiles.csv
- It shows the top N artifact for risk factors for diabetes. Basically, it shows the top cohorts ranked by prevalence in descending order.
- Why it matters: This is one of the primary decision artifacts. It tells the Director exactly which groups to prioritize for outreach.
- Caveats: No major caveats.


**A3**: out/evidence/location_prevalence_profile.csv
- It shows the diabetes prevalence rates ranked by geographic location, identifying which areas have the highest burden relative to their population size.
- Why it matters: It allows the Director to make location based funding decisions rather than applying even resources to every location (Causes misallocation of resources).
- Caveats: Some locations have smaller cohort sizes which may produce less stable prevalence estimates compared to larger areas.


**A4**: out/evidence/risk_rule_flags.csv
- It is the special rules and filters to see the targeted population, and shows the count of individuals and diabetes cases matching six combinations such as Hypertension AND Obese, Age 55+ AND Obese etc.
- Why it matters: Combination rules identify the highest-density clusters in the population which gives the Director practical screening criteria that can be applied to outreach programs.
- Caveats: Rules are not causal. Medical oversight is required before clinical use.


**Trust check**: out/evidence/data_quality_report.txt
- It shows whether the dataset has any null values. It also shows numeric ranges for multiple categories, as well as the field validation for binary values. Apart from this, it also shows the percentage of diabetes distribution.
- Why it matters: It confirms that the dataset is reliable enough to take any major decision by the Director. Without this, the Director cannot trust the prevalence numbers.
- caveats: No major caveats.


**Assumption test**: out/evidence/assumption_test_category_distinct_sample.txt
- It shows distinct category values and repetition frequency for key grouping fields including gender, race, smoking history, and location, confirming they are clean and consistent.
- Why it matters: It validates that the cohort segmentation logic is sound and that no structural data issues exist that could negatively impact the prevalence calculations.
- Caveats: High repetition in the ID field reflects year distribution across the dataset, and not the duplicate patient records.  

3) Recommendation drafting (10 to 15 min)
Draft 1 to 3 recommendation bullets and verify they are supported by evidence.
- R1: Prioritize immediate screening outreach for the top 3 cohorts identified in ranked_high_risk_profiles.csv (Heart disease, Hypertension, and 70+ Age)
- R2: Allocate additional budget to regions with the highest prevalence of “Former” or “Current” smokers over age 55.
- R3: Use the rule-based screening criteria in out/evidence/risk_rule_flags.csv to identify the individuals that match two or more high-risk flags as priority candidates for outreach programs.
- R4: Prioritize funding for top-N high-prevalence locations identified in out/evidence/location_prevalence_profile.csv


4) Action plan finalization (10 min)
Confirm owners, due dates, and definitions of done for remaining deliverables.

5) Wrap (2 min)
Confirm the plan, finalize the Decision Brief and the remaining tasks.


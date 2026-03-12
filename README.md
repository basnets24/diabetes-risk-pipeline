# Team10 - Comprehensive Diabetes Clinical Dataset Analysis

---

## Team Members
- Justin Tan
- Sneha Basnet
- Prathana Dankhara
- Krish Makwana

---

## Dataset Choice & Justification

**Dataset Title:**
100,000 Diabetes Clinical Dataset

**Source:** 
https://www.kaggle.com/datasets/priyamchoksi/100000-diabetes-clinical-dataset/data

**Size / Scope:**
- 100,000 patient records
- Mix of numerical and categorical features

**Description:**
This dataset contains anonymized clinical information related to diabetes. It includes patient demographics, clinical measurements such as blood glucose and HbA1c, and indicators of related conditions like hypertension and heart disease. The data is structured and suitable for large-scale analysis.

**Justification:**
Diabetes is one of the leading chronic diseases that affect the population of the United States. Early identification of high-risk population segments would allow the health authorities to direct limited prevention budgets toward the groups that are most likely to benefit from the targeted outreach. We have analyzed clinical and demographic patterns in a structured dataset of 100,000 individuals spanning years 2015 to 2022 to identify which specific groups are at the highest risk.
---
## Data Card Section 

### File Format and Size 
- **File format(s):** CSV 
- **Compression:** .zip , .csv
- **File size(s):** 896K (zip), 5.9M (.csv) 

### Shape
- **Row count:** 100001
- **Column count:** 16

### Parsing Details
- **Delimiter:** comma 
- **Header row present:** yes 
- **Encoding:** charset=us-ascii 

---

### Evidence Summary  

Baseline Metrics: The total dataset of 100,000 individuals confirms a baseline prevalence of exactly 8.50% (8,500 diabetic out of 91,500 non-diabetic), which can be verified from out/evidence/data_quality_report.txt. Zero null values were found across all the 16 columns and all the binary fields contain only valid 0 or 1 values, and no invalid entries.

Risk Profiles: Analysis of 20 ranked cohorts identified groups with prevalence rates ranging from 32.1% (Heart Disease) down to 4.1% (Smoking status: Unknown). All the top 3 cohorts surpass the baseline by a lot. This can be verified by looking at the full rankings in out/evidence/ranked_high_risk_profiles.csv.

Geographic Density: Regional analysis across 53 locations in out/evidence/location_prevalence_profile.csv identified that Delaware, Kansas, and Illinois are the top three regions. All these regions exceeded 9.5% prevalence rate compared to the 8.5% baseline.

Reliability Check: Categorical consistency was validated in out/evidence/assumption_test_category_distinct_sample.txt, where the gender field contains exactly three clean distinct values (Female, Male, Other). The ID repeat analysis in assumption_test_id_repeats_top20.txt confirms that high repetition in year values reflects the dataset distribution across 2015-2022, not duplicate patient records. 


### Recommendation

Targeted Outreach: Prioritize screening and education resources for the top three high-prevalence cohorts identified in out/evidence/ranked_high_risk_profiles.csv, which are individuals with Heart Disease (32.1% prevalence, 3,942 individuals), Hypertension (27.9%, 7,485 individuals), and Age 70+ (20.1%, 13,275 individuals). All three exceed the 8.5% baseline by a significant margin.

Smoking Cessation Integration: Integrate diabetes screening into existing anti-smoking campaigns, specifically focusing on “Former” (13.9% prevalence, 19,803 individuals) and “Current” smokers (10.2%, 9,286 individuals) over the age of 55 as identified in out/evidence/ranked_high_risk_profiles.csv.

Rule-Based Screening: As seen in out/evidence/risk_rule_flags.csv, the highest risk combination is Hypertension AND Obese at 32.5% prevalence rate across 3,246 individuals with 1,143 confirmed diabetes cases. Age 55+ AND Obese (30.5%) and Heart Disease (32.1%) are the next highest priority factors. More attention could be paid to these patients.

Regional Funding: Additional funding to the locations with the highest prevalence as identified in out/evidence/location_prevalence_profile.csv. Delaware (9.82%), Kansas (9.77%), and Illinois (9.58%) lead the ranking and should be prioritized for location-targeted outreach programs.


## Repository Structure
- README.md - Project overview, team members, and dataset description.
- data/ - dataset download instructions (raw dataset is not stored in this repository).
- .gitignore - Specifies files excluded from version control.

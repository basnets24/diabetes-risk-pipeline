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
Diabetes is a major public health issue, and this dataset allows us to study how clinical and lifestyle factors affect different population groups. Its size and structure make it appropriate for a semester-long big data project focused on building scalable data pipelines and generating meaningful health insights.

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

### Data Quality Notes
- Missing values: 35,816 entries labeled "No Info" in the smoking_history column.
- Duplicate IDs: No unique ID column present.
- Inconsistent formatting: All rows contain 16 columns.
- Age range: 0.08 to 80 years (age stored as decimal values)
- Year range: 2015 to 2022.
- Class distribution:
  - Diabetes (1): 8,500 individuals (8.5%)
  - No Diabetes (0): 91,500 individuals (91.5%)
  - Dataset is imbalanced toward non-diabetic cases
- Gender distribution:
  - Female: 58,552 (58.55%)
  - Male: 41,430 (41.43%)
  - Other: 18 (0.018%)
  - Male-to-Female ratio: 0.71:1 (female-skewed dataset)

---

## Repository Structure

- README.md - Project overview, team members, and dataset description.
- data/ - dataset download instructions (raw dataset is not stored in this repository).
- .gitignore - Specifies files excluded from version control.

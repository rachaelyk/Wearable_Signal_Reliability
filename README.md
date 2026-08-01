# Does Body Composition Affect Wearable Signal Reliability?

## Overview

This project investigates whether a wearer's body composition influences the reliability of wearable sensor signals, and whether that relationship depends on where the sensor is placed on the body. Using accelerometer data from the PAMAP2 Physical Activity Monitoring dataset, I applied correlation analysis, mixed-effects regression, and robustness testing to determine whether BMI predicts signal variance at the wrist, chest, and ankle.

As wearable and smart garment technology becomes more central to health monitoring and fashion-integrated design, understanding whether sensor performance holds up consistently across different body types is important for equitable and reliable device design.

## Research Question

Does BMI predict wearable sensor signal quality at a fixed body location, independent of activity type, and does this relationship vary by sensor placement?

## Dataset

**Source:**

Reiss, A. (2012). PAMAP2 Physical Activity Monitoring [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5NW2H

The dataset contains accelerometer, gyroscope, and heart rate measurements collected from 9 subjects performing 18 physical activities, recorded via three wearable IMUs (wrist, chest, ankle) sampled at 100Hz. Subject-level demographics were used to compute BMI.

| Variable | Description |
|---|---|
| Variance | Signal energy per subject × location × activity |
| Missing Rate | Fraction of dropped/NaN samples |
| Location | Sensor placement (wrist, chest, ankle) |
| Activity | Physical activity performed during recording |
| BMI | Computed from subject height and weight |

The dataset includes 273 subject × location × activity observations across 9 subjects.

## Tools & Technologies

- Python (data parsing, feature engineering)
- PostgreSQL (relational storage, aggregation)
- R (`lme4`, `MASS`, `sandwich`, `lmtest`)
- Correlation Testing (`cor.test`)
- One-Way ANOVA (`aov`)
- Linear Mixed-Effects Models
- Robust Regression (Iteratively Reweighted Least Squares)
- Bootstrap Resampling
- Tableau

## Methodology

### Feature Engineering

Raw accelerometer streams were grouped by subject, location, and activity, and two signal quality metrics were computed for each group: variance (signal energy) and missing rate.

```python
summary = acc.groupby("activity_id").agg(
    variance=("x", "var"),
    missing_rate=("x", lambda s: s.isna().mean()),
)
```

### Relational Storage

Engineered features were loaded into a PostgreSQL database, with an analytical view aggregating signal quality by location, activity, and BMI quartile.

```sql
CREATE VIEW signal_quality_summary AS
SELECT location, activity, bmi_quartile, AVG(variance) AS avg_variance
FROM readings_raw JOIN bmi_quartiles USING (subject_id)
GROUP BY location, activity, bmi_quartile;
```

### Correlation and ANOVA

BMI's relationship with signal variance was tested separately at each location, and a one-way ANOVA tested whether variance differed significantly by location overall.

```r
cor.test(sub$bmi, sub$variance)
aov(variance ~ location, data = pamap2)
```

### Mixed-Effects Modeling

Because each subject contributed repeated readings across activities, a naive pooled regression would understate BMI's true uncertainty. A mixed-effects model treating subject as a random effect was used instead, with a BMI × location interaction term to test whether BMI's effect varied by placement.

```r
lmer(variance ~ bmi * location + activity + (1 | subject_id), data = pamap2)
```

### Robustness Testing

A leave-one-subject-out sensitivity analysis and a robust regression (downweighting outlier influence) were used to confirm the stability of the results.

## Key Findings

### Finding 1: Sensor Location Significantly Affects Signal Variance

A one-way ANOVA found that signal variance differed significantly across the three sensor locations (F(2,267) = 17.07, p = 1.06 × 10⁻⁷). This confirms that placement itself is a meaningful factor in signal capture.

<img width="250" height="676" alt="figure1_location_variance" src="https://github.com/user-attachments/assets/ece4a190-2c90-482a-954b-de2498e554d2" />

*Figure 1. Average signal variance by sensor location, showing significant differences across placements (ANOVA p = 1.06 × 10⁻⁷).*

### Finding 2: BMI's Relationship with Signal Quality Depends on Location

| Location | r | p-value | 95% Bootstrap CI |
|---|---|---|---|
| Wrist | -0.663 | 0.052 | [-0.936, -0.052] |
| Chest | -0.338 | 0.374 | [-0.835, 0.218] |
| Ankle | -0.182 | 0.639 | [-0.699, 0.664] |

Only the wrist showed a bootstrapped confidence interval that excluded zero, indicating that BMI's negative relationship with signal variance is most defensible at that location.

<img width="1127" height="507" alt="figure2_bmi_by_location" src="https://github.com/user-attachments/assets/c2c4325e-4083-47e1-a60f-4f6a85b2d2a8" />

*Figure 2. BMI vs. signal variance by location, with linear trend lines. Only the wrist shows a consistent negative trend.*

### Finding 3: A Naive Pooled Model Understates BMI's Effect

A regression pooling all 273 readings found no significant BMI effect (p = 0.90). This approach treats repeated readings from the same subject as independent, which is not appropriate given that BMI only varies across 9 subjects, not 273 observations.

### Finding 4: The BMI × Location Interaction Confirms Placement-Dependence

A mixed-effects model with a BMI × location interaction term found a significant interaction at the wrist (β = -4.51, t = -2.33), but not at the chest (β = -1.79, t = -0.93). This directly supports the location-dependent pattern observed in Finding 2.

<img width="322" height="675" alt="figure3_bootstrap_ci" src="https://github.com/user-attachments/assets/c3a34676-5aae-42fb-9955-fa64c83df649" />

*Figure 3. Bootstrapped 95% confidence intervals for the BMI-variance correlation at each location. Only the wrist's interval excludes zero.*

### Finding 5: The Result Is Robust to Outliers and Individual Subjects

A leave-one-subject-out analysis confirmed the location effect remained significant regardless of which subject was excluded (p ranging from 5.8 × 10⁻⁸ to 2.0 × 10⁻⁶). A robust regression produced a BMI coefficient consistent in sign and magnitude with the correlation-based findings.

## Why It Matters

Wearable devices are increasingly used for health monitoring, fitness tracking, and smart garment applications, but device validation often relies on average performance across a population. Understanding whether specific placements are more sensitive to body composition can support:

- Inclusive wearable and smart garment design
- Placement-specific calibration strategies
- Fit-adjustment considerations for garment-integrated sensors
- Materials and design decisions in wearable technology development

This analysis demonstrates how statistical modeling can be applied to evaluate the consistency and fairness of sensor-based technology across different body types.

## Limitations

- The dataset contains only 9 subjects, limiting statistical power to detect smaller BMI effects.
- BMI is an imperfect proxy for body composition, as it does not distinguish muscle from fat mass or account for garment fit.
- Signal quality metrics (variance, missing rate) are proxies for reliability and have not been validated against a downstream outcome such as activity recognition accuracy.

## Conclusion

Using correlation analysis, mixed-effects regression, and robustness testing, I investigated whether body composition affects wearable sensor signal reliability. The analysis found that BMI's relationship with signal quality is not uniform across the body: it is most pronounced at the wrist, where the effect held up under bootstrap resampling, interaction modeling, and leave-one-subject-out validation. These findings suggest that a single sensor placement may not perform equally well across different body compositions, and that placement-specific calibration may be warranted for wearable and smart garment design.

## Repository Structure

```
├── README.md
├── pamap2_analysis_scipy.py     # Python: parses raw .dat files, engineers features
├── pamap2_schema.sql            # PostgreSQL schema + analytical views
├── load_to_sql.py               # loads engineered features into Postgres
├── pamap2_final_nocat.R         # R: correlation, ANOVA, mixed-effects, robustness checks
├── pamap2_quality_clean.csv     # engineered features (output of the Python step)
└── figures/
    ├── figure1_location_variance.png
    ├── figure2_bmi_by_location.png
    └── figure3_bootstrap_ci.png
```

## Running It

1. Download PAMAP2 from the [UCI ML Repository](https://archive.ics.uci.edu/dataset/231/pamap2+physical+activity+monitoring) and unzip `PAMAP2_Dataset/Protocol/`
2. Transcribe the 9 subjects' demographics from `subjectInformation.pdf` into `SUBJECT_INFO` in `pamap2_analysis_scipy.py`
3. Run `python3 pamap2_analysis_scipy.py` to produce `pamap2_quality_clean.csv`
4. Create a PostgreSQL database, run `pamap2_schema.sql`, then `python3 load_to_sql.py`
5. Run `pamap2_final_nocat.R` for the statistical analysis
6. Connect Tableau to the PostgreSQL database to reproduce the dashboard

## Author

Rachael Kim    
Biometry & Statistics, Cornell University (minors in Data Science and Fashion Studies)

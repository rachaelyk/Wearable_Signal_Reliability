# Does Body Composition Affect Wearable Signal Reliability?

## Overview

This project investigates whether a wearer's body composition influences the reliability of wearable sensor signals, and whether that relationship depends on where the sensor is placed on the body. Using accelerometer data from the PAMAP2 Physical Activity Monitoring dataset, I applied correlation analysis, robust regression, and bootstrap resampling to determine whether BMI predicts signal variance at the wrist, chest, and ankle.

As wearable and smart garment technology becomes more central to health monitoring and fashion-integrated design, understanding whether sensor performance holds up consistently across different body types is important for equitable and reliable device design.

## Research Question

Does BMI predict wearable sensor signal quality at a fixed body location, and does this relationship vary by sensor placement?

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
- R (`sandwich`, `lmtest`, `MASS`)
- Correlation Testing (`cor.test`)
- One-Way ANOVA (`aov`)
- OLS Regression with Robust Standard Errors
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

BMI's relationship with signal variance was tested separately at each location, using subject-level averages (n=9 per location) rather than the raw 273 rows — since BMI is a subject-level trait, it doesn't vary across a subject's repeated readings, so the honest sample size for this test is 9, not 273. A one-way ANOVA tested whether variance differed significantly by location overall.

```r
cor.test(sub$bmi, sub$variance)
aov(variance ~ location, data = pamap2)
```

### OLS Regression with Robust Standard Errors

A pooled regression across all 273 readings (`variance ~ bmi + location + activity`) was fit with heteroskedasticity-robust standard errors, following the same approach used in prior coursework analyzing binary and continuous outcomes.

```r
ols.fit <- lm(variance ~ bmi + location + activity, data = pamap2)
coeftest(ols.fit, vcov = vcovHC(ols.fit, type = "HC1"))
```

### Robustness Testing

Two checks were used to assess the stability of the results:

- **Bootstrap resampling**: because the sample size is small (n=9 subjects), the usual formula-based confidence interval for a correlation assumes a larger sample than is available here. Instead, the 9 subjects were resampled with replacement 2,000 times to construct an empirical 95% confidence interval for each location's correlation.
- **Robust regression** (`MASS::rlm`): downweights the influence of outlier observations automatically, rather than removing them by hand, as a check on whether the pooled OLS result was sensitive to extreme values.
- **Leave-one-subject-out**: the location ANOVA was refit nine times, each time excluding one subject, to confirm the result wasn't driven by any single individual.

## Key Findings

### Finding 1: Sensor Location Effect on Signal Variance

A one-way ANOVA found that signal variance differed significantly across the three sensor locations (F(2,267) = 17.07, p = 1.06 × 10⁻⁷), indicating that where a sensor sits on the body meaningfully affects the signal it captures.

<img width="250" height="676" alt="figure1_location_variance" src="https://github.com/user-attachments/assets/2a54b181-4b7d-4f85-9808-a29a43b50f8e" />

*Figure 1. Average signal variance by sensor location.*

### Finding 2: BMI's Relationship with Signal Quality by Location

Correlation between BMI and signal variance was tested separately at each location (subject-level, n=9):

| Location | r | p-value |
|---|---|---|
| Hand (wrist) | -0.663 | 0.052 |
| Chest | -0.338 | 0.374 |
| Ankle | -0.182 | 0.639 |

The wrist showed the strongest relationship, approaching but not reaching conventional significance (p=0.052) — a higher-BMI subject tended to show lower signal variance at that location. The chest showed a weaker trend in the same direction, and the ankle showed almost no relationship.

<img width="1127" height="507" alt="figure2_bmi_by_location" src="https://github.com/user-attachments/assets/312a6cf5-1d40-4d3b-8fd4-1257dabfb56d" />

*Figure 2. BMI vs. signal variance by location, with linear trend lines.*

### Finding 3: Bootstrap Confidence Intervals

Because of the small sample size, 95% confidence intervals for each location's correlation were constructed via bootstrap resampling (2,000 resamples) rather than a formula-based approach:

| Location | r | 95% Bootstrap CI |
|---|---|---|
| Hand (wrist) | -0.663 | [-0.936, -0.052] |
| Chest | -0.338 | [-0.835, 0.218] |
| Ankle | -0.182 | [-0.699, 0.664] |

Only the wrist's interval falls entirely below zero. The chest's and ankle's intervals both include zero, meaning a "no relationship" result cannot be ruled out at those locations given this sample size — while the wrist's negative relationship is comparatively more defensible.

<img width="322" height="675" alt="figure3_bootstrap_ci" src="https://github.com/user-attachments/assets/b4732c16-f8be-4564-81de-9c226fb573dd" />

*Figure 3. Bootstrapped 95% confidence intervals for the BMI-variance correlation at each location. A location whose interval excludes zero has a more statistically defensible relationship than one whose interval crosses zero.*

### Finding 4: Robustness

A leave-one-subject-out analysis confirmed the location effect (Finding 1) remained significant regardless of which subject was excluded (p ranging from 5.8 × 10⁻⁸ to 2.0 × 10⁻⁶ across all nine refits), indicating no single subject was driving the result.

A robust regression (which downweights the influence of outlier observations) produced a BMI coefficient of -0.123, consistent in direction with the wrist correlation, though a naive pooled OLS across all 273 readings (0.119, p=0.90) did not detect a significant effect — as expected, since that approach treats each subject's repeated readings as more independent than they truly are, diluting BMI's true subject-level relationship with signal quality.

| Model | BMI Estimate |
|---|---|
| Correlation (wrist only) | -0.663 |
| Naive pooled OLS | 0.119 |
| Robust regression (rlm) | -0.123 |

## Why It Matters

Wearable devices are increasingly used for health monitoring, fitness tracking, and smart garment applications, but device validation often relies on average performance across a population. Understanding whether specific placements are more sensitive to body composition can support:

- Inclusive wearable and smart garment design
- Placement-specific calibration strategies
- Fit-adjustment considerations for garment-integrated sensors
- Materials and design decisions in wearable technology development

This analysis demonstrates how statistical modeling can be applied to evaluate the consistency of sensor-based technology across different body types.

## Limitations

- The dataset contains only 9 subjects, limiting statistical power to detect smaller BMI effects; results should be read as exploratory.
- BMI is an imperfect proxy for body composition, as it does not distinguish muscle from fat mass or account for garment fit.
- Signal quality metrics (variance, missing rate) are proxies for reliability and have not been validated against a downstream outcome such as activity recognition accuracy.
- Correlation and robust regression establish association, not causation, and the pooled OLS model treats repeated readings from the same subject as more independent than they truly are.

## Conclusion

Using correlation analysis, robust regression, and bootstrap resampling, I investigated whether body composition affects wearable sensor signal reliability, and whether that relationship depends on sensor placement. Signal variance differed significantly by location overall, and BMI's relationship with signal variance was strongest and most defensible at the wrist (r=-0.663, bootstrap 95% CI entirely below zero), weaker at the chest, and essentially absent at the ankle. This finding held up under a leave-one-subject-out sensitivity check and was consistent in direction with a robust regression estimate. These results suggest that a single sensor placement may not perform equally well across different body compositions, and that the wrist in particular may warrant further attention in wearable and smart garment design.

## Repository Structure

```
├── README.md
├── pamap2_analysis_scipy.py     # Python: parses raw .dat files, engineers features
├── pamap2_schema.sql            # PostgreSQL schema + analytical views
├── load_to_sql.py               # loads engineered features into Postgres
├── pamap2.Rmd         # R: correlation, ANOVA, OLS with robust SE, bootstrap CI, robust regression, leave-one-out
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
5. Run `pamap2.Rmd` for the statistical analysis
6. Connect Tableau to the PostgreSQL database to reproduce the dashboard

## Author

Rachael Kim    
Biometry & Statistics, Cornell University (minors in Data Science and Fashion Studies)

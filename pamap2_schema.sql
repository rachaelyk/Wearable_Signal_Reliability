-- Body Composition & Signal Reliability: Database Schema
-- Load pamap2_quality_clean.csv (output of pamap2_analysis_scipy.py) into `readings_raw`

DROP VIEW IF EXISTS signal_quality_summary;
DROP VIEW IF EXISTS bmi_quartiles;
DROP TABLE IF EXISTS readings_raw;
DROP TABLE IF EXISTS subjects;

CREATE TABLE readings_raw (
    activity_id    REAL,
    variance       REAL,
    missing_rate   REAL,
    location       TEXT,     -- 'hand' | 'chest' | 'ankle'
    subject_id     INTEGER,
    activity       TEXT,
    gender         TEXT,
    age            INTEGER,
    height_cm      REAL,
    weight_kg      REAL,
    resting_hr     REAL,
    max_hr         REAL,
    dominant_hand  TEXT,
    bmi            REAL
);

CREATE TABLE subjects (
    subject_id  INTEGER PRIMARY KEY,
    gender      TEXT,
    age         INTEGER,
    height_cm   REAL,
    weight_kg   REAL,
    resting_hr  REAL,
    max_hr      REAL,
    dominant_hand TEXT,
    bmi         REAL
);

-- BMI quartile bucketing -- useful directly in Tableau for a clean categorical axis
CREATE VIEW bmi_quartiles AS
SELECT
    subject_id,
    bmi,
    NTILE(4) OVER (ORDER BY bmi) AS bmi_quartile
FROM subjects;

-- Main analytical view: average signal quality by location, activity, and BMI quartile
CREATE VIEW signal_quality_summary AS
SELECT
    r.location,
    r.activity,
    q.bmi_quartile,
    AVG(r.variance)      AS avg_variance,
    AVG(r.missing_rate)  AS avg_missing_rate,
    COUNT(*)             AS n_rows
FROM readings_raw r
JOIN bmi_quartiles q ON r.subject_id = q.subject_id
GROUP BY r.location, r.activity, q.bmi_quartile;

-- Example analytical queries --------------------------------------------

-- 1. Does signal variance at the hand differ across BMI quartiles during
--    high-motion activities (walking, running, stairs)?
-- SELECT bmi_quartile, AVG(avg_variance) AS mean_variance
-- FROM signal_quality_summary
-- WHERE location = 'hand' AND activity IN ('walking','running','ascending_stairs','descending_stairs')
-- GROUP BY bmi_quartile
-- ORDER BY bmi_quartile;

-- 2. Which location shows the LEAST variation in signal quality across BMI
--    quartiles -- i.e. the most "body-agnostic" placement?
-- SELECT location, MAX(avg_variance) - MIN(avg_variance) AS bmi_spread
-- FROM signal_quality_summary
-- GROUP BY location
-- ORDER BY bmi_spread ASC;

-- 3. Missing-data rate by BMI quartile (motion artifact / sensor slippage proxy)
-- SELECT bmi_quartile, location, AVG(avg_missing_rate) AS missing_rate
-- FROM signal_quality_summary
-- GROUP BY bmi_quartile, location;
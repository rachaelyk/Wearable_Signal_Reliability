"""
Does Body Composisiton Affect Wearable Signal Reliability?

Dataset: PAMAP2 Physical Activity Monitoring (UCI ML Repository, id=231)
Download: https://archive.ics.uci.edu/dataset/231/pamap2+physical+activity+monitoring
"""

import pandas as pd
import glob
from scipy.stats import pearsonr, f_oneway
import matplotlib.pyplot as plt


DATA_DIR = "/Users/rachaelkim/pamap2/PAMAP2_Dataset/Protocol"

ACTIVITY_MAP = {
    1: "lying", 2: "sitting", 3: "standing", 4: "walking", 5: "running",
    6: "cycling", 7: "Nordic_walking", 9: "watching_TV", 10: "computer_work",
    11: "car_driving", 12: "ascending_stairs", 13: "descending_stairs",
    16: "vacuum_cleaning", 17: "ironing", 18: "folding_laundry",
    19: "house_cleaning", 20: "playing_soccer", 24: "rope_jumping", 0: "other",
}

SUBJECT_INFO = pd.DataFrame({
    "subject_id": [101, 102, 103, 104, 105, 106, 107, 108, 109],
    "gender": ["M", "F", "M", "M", "M", "M", "M", "M", "M"],
    "age": [27, 25, 31, 24, 26, 26, 23, 32, 31],
    "height_cm": [182, 169, 187, 194, 180, 183, 173, 179, 168],
    "weight_kg": [83, 78, 92, 95, 73, 69, 86, 87, 65],
    "resting_hr": [75, 74, 68, 58, 70, 60, 60, 66, 54],
    "max_hr": [193, 195, 189, 196, 194, 194, 197, 188, 189],
    "dominant_hand": ["right", "right", "right", "right", "right", "right", "right", "left", "right"],
})

SUBJECT_INFO["bmi"] = SUBJECT_INFO["weight_kg"] / ((SUBJECT_INFO["height_cm"] / 100) ** 2)

LOCATIONS = {
    "hand": [4, 5, 6],
    "chest": [21, 22, 23],
    "ankle": [38, 39, 40],
}


# Signal quality table
all_quality_tables = []

for filepath in sorted(glob.glob(f"{DATA_DIR}/subject*.dat")):
    subject_id = int(filepath.split("subject")[-1].split(".dat")[0])
    df = pd.read_csv(filepath, sep=r"\s+", header=None)
    df["activity_id"] = df[1]

    for location, cols in LOCATIONS.items():
        acc = df.iloc[:, cols].copy()
        acc.columns = ["x", "y", "z"]
        acc["activity_id"] = df["activity_id"]

        summary = acc.groupby("activity_id").agg(
            variance=("x", "var"),
            missing_rate=("x", lambda s: s.isna().mean()),
        ).reset_index()
 
        summary["location"] = location
        summary["subject_id"] = subject_id
        all_quality_tables.append(summary)

quality_df = pd.concat(all_quality_tables, ignore_index=True)
quality_df["activity"] = quality_df["activity_id"].map(ACTIVITY_MAP)
quality_df = quality_df[quality_df["activity_id"] != 0]
quality_df = quality_df.merge(SUBJECT_INFO, on="subject_id", how="left")

print(quality_df.head())
print(f"\nTotal rows: {len(quality_df)}")


# Does BMI correlate with signal variance, at each location?
subject_location_avg = (
    quality_df.groupby(["subject_id", "location"])["variance"]
    .mean()
    .reset_index()
    .merge(SUBJECT_INFO[["subject_id", "bmi"]], on="subject_id")
)

print("\n BMI vs Signal Variance Correlation by Location")
for location in LOCATIONS:
    subset = subject_location_avg[subject_location_avg["location"] == location]
    r, p = pearsonr(subset["bmi"], subset["variance"])
    print(f"{location}: r = {r:.3f}, p = {p:.3f} (n={len(subset)} subjects)")


# Does average signal variance differ significantly across locations?
groups = [quality_df[quality_df["location"] == loc]["variance"].dropna() for loc in LOCATIONS]
f_stat, p_val = f_oneway(*groups)
print(f"\n ANOVA: Variance across locations: F = {f_stat:.3f}, p = {p_val:.3f}")


# Visual check
fig, axes = plt.subplots(1,3,figsize=(12,4), sharey=True)
for ax, location in zip(axes, LOCATIONS):
    subset = subject_location_avg[subject_location_avg["location"] == location]
    ax.scatter(subset["bmi"], subset["variance"])
    ax.set_title(location)
    ax.set_xlabel("BMI")
axes[0].set_ylabel("avg signal variance")
plt.tight_layout()
plt.savefig("bmi_vs_variance.png", dpi=150)
print("\nSaved bmi_vs_variance.png")


# Export for SQL
quality_df.to_csv("pamap2_quality_clean.csv", index=False)
print("Exported pamap2_quality_clean.csv")
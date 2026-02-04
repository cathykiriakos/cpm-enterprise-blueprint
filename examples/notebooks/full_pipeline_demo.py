#!/usr/bin/env python3
"""CPM Enterprise Blueprint - Full Pipeline Demo"""

import sys
from pathlib import Path
import warnings
import logging
warnings.filterwarnings("ignore")

print("=" * 60)
print("CPM ENTERPRISE BLUEPRINT - FULL PIPELINE DEMO")
print("=" * 60)

# Setup paths
SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent.parent
SRC_DIR = REPO_ROOT / "src"

print(f"\nRepo root: {REPO_ROOT}")
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(REPO_ROOT))

import pandas as pd
import numpy as np
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.WARNING)

# Imports
print("\n--- Verifying Imports ---")
from data_generator import SyntheticDataGenerator, GeneratorConfig
print("✓ data_generator")
from identity_resolution.identity_resolver import ConstituentUnifier, SourceRecord, MatchConfig
print("✓ identity_resolver")
from ml_models.churn_prediction import ChurnPredictor, generate_sample_data as gen_churn_data
print("✓ churn_prediction")
from ml_models.upgrade_propensity import UpgradePropensityModel, generate_sample_data as gen_upgrade_data
print("✓ upgrade_propensity")
from metrics.engine import MetricsEngine
print("✓ metrics_engine")
from data_quality.validator import DataValidator, QualityCheck, CheckType, CheckSeverity
print("✓ data_quality")
print("\n✓ All imports successful!")

# Step 1: Generate Data
print("\n" + "=" * 60)
print("STEP 1: GENERATING SYNTHETIC DATA")
print("=" * 60)

config = GeneratorConfig(num_constituents=1000, sustainer_rate=0.25, churn_rate=0.15, overlap_rate=0.40)
generator = SyntheticDataGenerator(config)
datasets = generator.generate_all()

output_dir = REPO_ROOT / "data" / "demo"
output_dir.mkdir(parents=True, exist_ok=True)
for name, df in datasets.items():
    df.to_csv(output_dir / f"{name}.csv", index=False)
    print(f"  ✓ {name}: {len(df):,} records")

# Step 2: Identity Resolution
print("\n" + "=" * 60)
print("STEP 2: IDENTITY RESOLUTION")
print("=" * 60)

match_config = MatchConfig(auto_match_threshold=0.85, review_threshold=0.70)
unifier = ConstituentUnifier(match_config)

wbez_records = []
wbez_df = datasets.get("wbez_donations", pd.DataFrame())
for _, row in wbez_df.drop_duplicates("person_id").head(500).iterrows():
    wbez_records.append(SourceRecord(
        source_system="wbez", source_id=str(row["person_id"]),
        email=row.get("email"), phone=row.get("phone"),
        first_name=row.get("first_name"), last_name=row.get("last_name"),
        address_line1=row.get("address"), city=row.get("city"),
        state=row.get("state"), zip_code=str(row.get("zip", ""))
    ))
print(f"  ✓ WBEZ: {len(wbez_records)} records")

suntimes_records = []
suntimes_df = datasets.get("suntimes_subscriptions", pd.DataFrame())
for _, row in suntimes_df.iterrows():
    suntimes_records.append(SourceRecord(
        source_system="suntimes", source_id=str(row["subscription_id"]),
        email=row.get("email"), phone=row.get("phone"),
        first_name=row.get("first_name"), last_name=row.get("last_name"),
        address_line1=row.get("address"), city=row.get("city"),
        state=row.get("state"), zip_code=str(row.get("zip", ""))
    ))
print(f"  ✓ Sun-Times: {len(suntimes_records)} records")

all_records = wbez_records + suntimes_records
print(f"\nTotal: {len(all_records)} records")

# Suppress identity resolver logging for cleaner output
logging.getLogger("constituent_unification.identity_resolver").setLevel(logging.WARNING)
golden_records = unifier.unify_records(all_records)
print(f"✓ Created {len(golden_records)} unified records")
consolidation = (len(all_records) - len(golden_records)) / len(all_records) * 100
print(f"  Consolidation rate: {consolidation:.1f}%")

# Step 3: Churn Model (using model's sample data)
print("\n" + "=" * 60)
print("STEP 3: CHURN PREDICTION MODEL")
print("=" * 60)

print("  Generating sample churn data...")
churn_df, churn_labels = gen_churn_data(n=2000)
print(f"  ✓ Sample data: {len(churn_df)} records")

predictor = ChurnPredictor()
print("  Training model...")
metrics = predictor.train(churn_df, churn_labels)
print(f"✓ AUC: {metrics.get('auc', 0):.3f}")
print(f"  Precision: {metrics.get('precision', 0):.3f}")
print(f"  Recall: {metrics.get('recall', 0):.3f}")

# Step 4: Upgrade Model
print("\n" + "=" * 60)
print("STEP 4: UPGRADE PROPENSITY MODEL")
print("=" * 60)

print("  Generating sample upgrade data...")
upgrade_df, upgrade_labels = gen_upgrade_data(n=2000)
print(f"  ✓ Sample data: {len(upgrade_df)} records")

model = UpgradePropensityModel()
print("  Training model...")
metrics = model.train(upgrade_df, upgrade_labels)
print(f"✓ One-Time → Sustainer AUC: {metrics['to_sustainer'].get('auc', 0):.3f}")
print(f"  Sustainer Upgrade AUC: {metrics['sustainer_increase'].get('auc', 0):.3f}")
print(f"  Major Gift AUC: {metrics['to_major'].get('auc', 0):.3f}")

# Step 5: Data Quality
print("\n" + "=" * 60)
print("STEP 5: DATA QUALITY VALIDATION")
print("=" * 60)

ground_truth = datasets.get("ground_truth", pd.DataFrame())
validator = DataValidator()
validator.add_check(QualityCheck(name="person_id_complete", check_type=CheckType.COMPLETENESS, severity=CheckSeverity.ERROR, description="Person ID must be present", field="person_id"))
validator.add_check(QualityCheck(name="email_complete", check_type=CheckType.COMPLETENESS, severity=CheckSeverity.WARNING, description="Email should be present", field="email"))
validator.add_check(QualityCheck(name="person_id_unique", check_type=CheckType.UNIQUENESS, severity=CheckSeverity.ERROR, description="Person ID must be unique", field="person_id"))
report = validator.validate(ground_truth, dataset_name="ground_truth")
print(report.summary())

# Step 6: Metrics
print("\n" + "=" * 60)
print("STEP 6: METRICS ENGINE")
print("=" * 60)

metrics_file = REPO_ROOT / "config" / "metrics_definitions.yaml"
engine = MetricsEngine(str(metrics_file))
loaded_metrics = engine.list_metrics()
print(f"✓ Loaded {len(loaded_metrics)} certified metrics")
for m in loaded_metrics[:5]:
    print(f"  📊 {m}")

# Summary
print("\n" + "=" * 60)
print("DEMO COMPLETE!")
print("=" * 60)
print(f"\n  ✓ Generated {sum(len(df) for df in datasets.values()):,} synthetic records")
print(f"  ✓ Created {len(golden_records):,} golden records (consolidated {consolidation:.0f}%)")
print(f"  ✓ Churn model trained")
print(f"  ✓ Upgrade model trained (3 paths)")
print(f"  ✓ Data quality validated")
print(f"  ✓ Loaded {len(loaded_metrics)} certified metrics")
print("\nThank you for reviewing!")

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CPM Enterprise Blueprint - Data Generation Demo
================================================

This notebook demonstrates:
1. Generating synthetic constituent data
2. Running identity resolution
3. Training ML models (churn + upgrade)
4. Generating predictions

Run as: python 01_data_generation_demo.py
Or convert to Jupyter: jupytext --to notebook 01_data_generation_demo.py
"""

# %% [markdown]
# # CPM Enterprise Blueprint Demo
# 
# This notebook walks through the complete data pipeline from synthetic data
# generation through ML predictions.

# %% Setup
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

import pandas as pd
import numpy as np
from datetime import datetime

print("=" * 60)
print("CPM ENTERPRISE BLUEPRINT - DEMO")
print("=" * 60)

# %% [markdown]
# ## 1. Generate Synthetic Data
# 
# We'll create realistic public media constituent data including:
# - WBEZ donations (one-time and recurring)
# - Sun-Times subscriptions
# - Event tickets
# - Email engagement

# %%
from src.data_generator import SyntheticDataGenerator, GeneratorConfig

config = GeneratorConfig(
    num_constituents=100,  # Reduced for faster testing
    overlap_rate=0.25,  # 25% of people appear in multiple systems
    sustainer_rate=0.35,
    churn_rate=0.15,
)

generator = SyntheticDataGenerator(config)
datasets = generator.generate_all()

print("\nGenerated Datasets:")
for name, df in datasets.items():
    print(f"  {name}: {len(df):,} records")

# Limit to first 500 records per dataset for faster demo
print("\n⚡ Limiting datasets to 500 records each for faster processing...")
for name in datasets:
    datasets[name] = datasets[name].head(500)

# %%
# Preview WBEZ donations
print("\n📊 WBEZ Donations Sample:")
print(datasets['wbez_donations'].head())

# %% [markdown]
# ## 2. Identity Resolution
# 
# Now we unify records across systems to create golden constituent records.

# %%
from src.identity_resolution.identity_resolver import (
    IdentityResolver, SourceRecord, MatchConfig, ConstituentUnifier
)

# Convert donations to source records
source_records = []

for _, row in datasets['wbez_donations'].iterrows():
    source_records.append(SourceRecord(
        source_system="wbez",
        source_id=row['donation_id'],
        email=row.get('email'),
        first_name=row.get('first_name'),
        last_name=row.get('last_name'),
        phone=row.get('phone'),
        city=row.get('city'),
        state=row.get('state'),
        zip_code=row.get('zip'),
        raw_data=row.to_dict()
    ))

# Add Sun-Times subscriptions
for _, row in datasets['suntimes_subscriptions'].iterrows():
    source_records.append(SourceRecord(
        source_system="suntimes",
        source_id=row['subscription_id'],
        email=row.get('email'),
        first_name=row.get('first_name'),
        last_name=row.get('last_name'),
        phone=row.get('phone'),
        city=row.get('city'),
        state=row.get('state'),
        zip_code=row.get('zip'),
        raw_data=row.to_dict()
    ))

print(f"\nTotal source records: {len(source_records):,}")

# Run unification with timeout and limit
print("\n⏱️ Starting identity resolution (limited to 1000 source records for demo)...")
limited_source_records = source_records[:1000]  # Limit to 1000 for faster processing

unifier = ConstituentUnifier(MatchConfig())
constituents = unifier.unify_records(limited_source_records)

print(f"Unified constituents: {len(constituents):,}")

# Get statistics
stats = unifier.get_match_statistics()
print(f"\nMatch Statistics:")
print(f"  Average records per constituent: {stats['avg_records_per_constituent']:.2f}")

# %% [markdown]
# ## 3. Prepare Features & Train Churn Model

# %%
from src.ml_models.churn_prediction import ChurnPredictor, generate_sample_data

# For demo, use generated sample data
# In production, would use unified constituent data
df, churn_labels = generate_sample_data(n=2000)

print(f"\nTraining data: {len(df):,} samples")
print(f"Churn rate: {churn_labels.mean()*100:.1f}%")

# Train model
churn_model = ChurnPredictor()
metrics = churn_model.train(df, churn_labels)

print(f"\nChurn Model Performance:")
print(f"  AUC: {metrics['auc']:.3f}")
print(f"  Precision: {metrics['precision']:.3f}")
print(f"  Recall: {metrics['recall']:.3f}")

# %% [markdown]
# ## 4. Train Upgrade Propensity Model

# %%
from src.ml_models.upgrade_propensity import UpgradePropensityModel, generate_sample_data as gen_upgrade_data

df_upgrade, upgrade_labels = gen_upgrade_data(n=2000)

upgrade_model = UpgradePropensityModel()
upgrade_metrics = upgrade_model.train(df_upgrade, upgrade_labels)

print("\nUpgrade Model Performance:")
for target, m in upgrade_metrics.items():
    print(f"  {target}: AUC={m['auc']:.3f}")

# %% [markdown]
# ## 5. Generate Predictions

# %%
# Get predictions
test_sample = df.head(20)
churn_preds = churn_model.predict(test_sample)

print("\n🎯 Churn Predictions (Top 10):")
print(churn_preds[['constituent_id', 'churn_score', 'churn_tier']].head(10))

# %%
# Upgrade predictions
upgrade_preds = upgrade_model.predict(df_upgrade.head(20))

print("\n📈 Upgrade Predictions (Top 10):")
print(upgrade_preds[['constituent_id', 'upgrade_propensity', 'best_path']].head(10))

# %% [markdown]
# ## 6. Combined Recommendations
# 
# Combine churn risk and upgrade propensity for actionable recommendations.

# %%
# Merge for recommendations
combined = upgrade_preds.merge(
    churn_preds[['constituent_id', 'churn_score']],
    on='constituent_id',
    how='left'
)

recommendations = upgrade_model.get_recommendations(upgrade_preds, churn_preds)

print("\n🎬 Action Recommendations:")
print(recommendations[['constituent_id', 'action', 'priority', 'best_path']].head(10))

# %% [markdown]
# ## 7. Data Quality Validation

# %%
from src.data_quality.validator import DataValidator, get_constituent_checks

validator = DataValidator()
validator.add_checks(get_constituent_checks())

# Create sample constituent data for validation
sample_constituents = pd.DataFrame({
    'constituent_id': churn_preds['constituent_id'],
    'canonical_email': [f'test{i}@example.com' for i in range(len(churn_preds))],
    'lifecycle_stage': ['sustainer'] * len(churn_preds),
    'churn_risk_score': churn_preds['churn_score']
})

report = validator.validate(sample_constituents, "demo_constituents")
print(report.summary())

# %% [markdown]
# ## Summary
# 
# This demo showed the complete pipeline:
# 1. ✅ Synthetic data generation
# 2. ✅ Identity resolution across systems
# 3. ✅ Churn prediction model training
# 4. ✅ Upgrade propensity model training
# 5. ✅ Combined recommendations
# 6. ✅ Data quality validation
# 
# For production deployment, the same patterns apply with real data sources.

print("\n" + "=" * 60)
print("DEMO COMPLETE")
print("=" * 60)
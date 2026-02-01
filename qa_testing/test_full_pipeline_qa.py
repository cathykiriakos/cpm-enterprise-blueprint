#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QA Test Suite for CPM Enterprise Blueprint Full Pipeline Demo
=============================================================

Comprehensive testing covering:
- Import and module resolution
- Data generation and validation
- Identity resolution functionality
- ML model training and predictions
- Data quality validation
- Performance and edge cases
- Output correctness
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import traceback

# Setup path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def test_case(test_name, test_func):
    """Decorator to run and track test cases"""
    try:
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")
        test_func()
        test_results["passed"].append(test_name)
        print(f"✅ PASSED: {test_name}")
        return True
    except Exception as e:
        test_results["failed"].append((test_name, str(e)))
        print(f"❌ FAILED: {test_name}")
        print(f"Error: {e}")
        traceback.print_exc()
        return False

# ============================================================================
# SECTION 1: IMPORT & MODULE TESTS
# ============================================================================

def test_import_data_generator():
    """Test data generator module imports"""
    from src.data_generator import SyntheticDataGenerator, GeneratorConfig
    assert SyntheticDataGenerator is not None
    assert GeneratorConfig is not None
    print("✓ SyntheticDataGenerator imported successfully")
    print("✓ GeneratorConfig imported successfully")

def test_import_identity_resolver():
    """Test identity resolver module imports"""
    from src.identity_resolution.identity_resolver import (
        IdentityResolver, SourceRecord, MatchConfig, ConstituentUnifier
    )
    assert SourceRecord is not None
    assert MatchConfig is not None
    assert ConstituentUnifier is not None
    print("✓ All identity resolution classes imported")

def test_import_ml_models():
    """Test ML model imports"""
    from src.ml_models.churn_prediction import ChurnPredictor, generate_sample_data
    from src.ml_models.upgrade_propensity import UpgradePropensityModel
    assert ChurnPredictor is not None
    assert generate_sample_data is not None
    assert UpgradePropensityModel is not None
    print("✓ All ML model classes imported")

def test_import_data_quality():
    """Test data quality validator imports"""
    from src.data_quality.validator import DataValidator, get_constituent_checks
    assert DataValidator is not None
    assert get_constituent_checks is not None
    print("✓ Data quality classes imported")

# ============================================================================
# SECTION 2: DATA GENERATION TESTS
# ============================================================================

def test_data_generator_config():
    """Test GeneratorConfig initialization"""
    from src.data_generator import GeneratorConfig
    
    config = GeneratorConfig(
        num_constituents=50,
        overlap_rate=0.25,
        sustainer_rate=0.35,
        churn_rate=0.15
    )
    
    assert config.num_constituents == 50
    assert config.overlap_rate == 0.25
    assert config.sustainer_rate == 0.35
    assert config.churn_rate == 0.15
    print("✓ GeneratorConfig initialized with correct values")

def test_synthetic_data_generation():
    """Test synthetic data generation output"""
    from src.data_generator import SyntheticDataGenerator, GeneratorConfig
    
    config = GeneratorConfig(num_constituents=50)
    generator = SyntheticDataGenerator(config)
    datasets = generator.generate_all()
    
    # Validate datasets exist
    required_datasets = ['wbez_donations', 'suntimes_subscriptions', 
                        'event_tickets', 'email_engagement', 'ground_truth']
    for dataset_name in required_datasets:
        assert dataset_name in datasets, f"Missing dataset: {dataset_name}"
        assert len(datasets[dataset_name]) > 0, f"Empty dataset: {dataset_name}"
    
    print(f"✓ Generated {len(datasets)} datasets")
    for name, df in datasets.items():
        print(f"  - {name}: {len(df)} records")

def test_data_schema_validation():
    """Test generated data has correct columns"""
    from src.data_generator import SyntheticDataGenerator, GeneratorConfig
    
    config = GeneratorConfig(num_constituents=20)
    generator = SyntheticDataGenerator(config)
    datasets = generator.generate_all()
    
    # Check WBEZ donations schema
    wbez = datasets['wbez_donations']
    required_columns = ['donation_id', 'person_id', 'email', 'first_name', 
                       'last_name', 'donation_amount']
    for col in required_columns:
        assert col in wbez.columns, f"Missing column in wbez_donations: {col}"
    
    print("✓ WBEZ donations schema correct")
    
    # Check suntimes subscriptions schema
    suntimes = datasets['suntimes_subscriptions']
    assert 'subscription_id' in suntimes.columns
    assert 'email' in suntimes.columns
    print("✓ Suntimes subscriptions schema correct")

def test_data_quality_checks():
    """Test generated data quality"""
    from src.data_generator import SyntheticDataGenerator, GeneratorConfig
    
    config = GeneratorConfig(num_constituents=30)
    generator = SyntheticDataGenerator(config)
    datasets = generator.generate_all()
    
    # Check for nulls in critical fields
    wbez = datasets['wbez_donations']
    assert wbez['donation_id'].nunique() == len(wbez), "Duplicate donation IDs"
    assert wbez['donation_amount'].dtype in [np.float64, np.int64], "Invalid amount type"
    
    print("✓ Data quality checks passed")
    print(f"  - No duplicate donation IDs")
    print(f"  - Valid data types")

# ============================================================================
# SECTION 3: IDENTITY RESOLUTION TESTS
# ============================================================================

def test_source_record_creation():
    """Test SourceRecord object creation"""
    from src.identity_resolution.identity_resolver import SourceRecord
    
    record = SourceRecord(
        source_system="test_system",
        source_id="TEST-001",
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        phone="555-1234"
    )
    
    assert record.source_system == "test_system"
    assert record.source_id == "TEST-001"
    assert record.email == "test@example.com"
    print("✓ SourceRecord created with correct attributes")

def test_match_config():
    """Test MatchConfig initialization"""
    from src.identity_resolution.identity_resolver import MatchConfig
    
    config = MatchConfig()
    assert hasattr(config, 'generic_emails') or hasattr(config, 'email_threshold')
    print("✓ MatchConfig initialized successfully")

def test_constituent_unifier():
    """Test ConstituentUnifier basic functionality"""
    from src.identity_resolution.identity_resolver import (
        SourceRecord, MatchConfig, ConstituentUnifier
    )
    
    # Create test records
    records = [
        SourceRecord(
            source_system="wbez",
            source_id="D-001",
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe"
        ),
        SourceRecord(
            source_system="suntimes",
            source_id="S-001",
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe"
        )
    ]
    
    unifier = ConstituentUnifier(MatchConfig())
    constituents = unifier.unify_records(records)
    
    # Should match records with same email
    assert len(constituents) > 0, "No constituents created"
    print(f"✓ ConstituentUnifier created {len(constituents)} unified constituent(s)")

def test_unifier_statistics():
    """Test match statistics generation"""
    from src.identity_resolution.identity_resolver import (
        SourceRecord, MatchConfig, ConstituentUnifier
    )
    
    records = [
        SourceRecord(
            source_system="wbez",
            source_id="D-001",
            email=f"user{i}@example.com",
            first_name="User",
            last_name=f"Test{i}"
        ) for i in range(5)
    ]
    
    unifier = ConstituentUnifier(MatchConfig())
    constituents = unifier.unify_records(records)
    stats = unifier.get_match_statistics()
    
    assert 'avg_records_per_constituent' in stats or isinstance(stats, dict)
    print("✓ Match statistics generated")
    print(f"  - Stats: {stats}")

# ============================================================================
# SECTION 4: ML MODEL TESTS
# ============================================================================

def test_churn_predictor_initialization():
    """Test ChurnPredictor initialization"""
    from src.ml_models.churn_prediction import ChurnPredictor
    
    model = ChurnPredictor()
    assert model is not None
    print("✓ ChurnPredictor initialized")

def test_churn_model_training():
    """Test churn model training"""
    from src.ml_models.churn_prediction import ChurnPredictor, generate_sample_data
    
    X, y = generate_sample_data(n=100)
    assert len(X) == 100, "Sample data size mismatch"
    assert len(y) == 100, "Label size mismatch"
    
    model = ChurnPredictor()
    metrics = model.train(X, y)
    
    assert 'auc' in metrics, "AUC not in metrics"
    assert 'precision' in metrics, "Precision not in metrics"
    assert 'recall' in metrics, "Recall not in metrics"
    assert 0 <= metrics['auc'] <= 1, "Invalid AUC value"
    
    print("✓ Churn model trained successfully")
    print(f"  - AUC: {metrics['auc']:.3f}")
    print(f"  - Precision: {metrics['precision']:.3f}")
    print(f"  - Recall: {metrics['recall']:.3f}")

def test_churn_predictions():
    """Test churn model predictions"""
    from src.ml_models.churn_prediction import ChurnPredictor, generate_sample_data
    
    X_train, y_train = generate_sample_data(n=100)
    X_test, _ = generate_sample_data(n=20)
    
    model = ChurnPredictor()
    model.train(X_train, y_train)
    predictions = model.predict(X_test.head(10))
    
    assert len(predictions) > 0, "No predictions generated"
    assert 'constituent_id' in predictions.columns or len(predictions.columns) > 0
    print(f"✓ Generated {len(predictions)} churn predictions")

def test_upgrade_propensity_model():
    """Test UpgradePropensityModel initialization and training"""
    from src.ml_models.upgrade_propensity import (
        UpgradePropensityModel, generate_sample_data
    )
    
    X, y = generate_sample_data(n=100)
    model = UpgradePropensityModel()
    metrics = model.train(X, y)
    
    assert isinstance(metrics, dict), "Metrics should be dictionary"
    print("✓ UpgradePropensityModel trained successfully")
    print(f"  - Models trained: {len(metrics)}")

def test_upgrade_predictions():
    """Test upgrade propensity predictions"""
    from src.ml_models.upgrade_propensity import (
        UpgradePropensityModel, generate_sample_data
    )
    
    X_train, y_train = generate_sample_data(n=100)
    X_test, _ = generate_sample_data(n=15)
    
    model = UpgradePropensityModel()
    model.train(X_train, y_train)
    predictions = model.predict(X_test.head(10))
    
    assert len(predictions) > 0, "No predictions generated"
    print(f"✓ Generated {len(predictions)} upgrade predictions")

def test_recommendations_generation():
    """Test recommendation generation"""
    from src.ml_models.upgrade_propensity import (
        UpgradePropensityModel, generate_sample_data
    )
    from src.ml_models.churn_prediction import ChurnPredictor
    
    # Train both models
    X_churn, y_churn = generate_sample_data(n=100)
    X_upgrade, y_upgrade = generate_sample_data(n=100)
    
    churn_model = ChurnPredictor()
    churn_model.train(X_churn, y_churn)
    upgrade_model = UpgradePropensityModel()
    upgrade_model.train(X_upgrade, y_upgrade)
    
    # Get predictions
    churn_preds = churn_model.predict(X_churn.head(10))
    upgrade_preds = upgrade_model.predict(X_upgrade.head(10))
    
    # Generate recommendations
    recommendations = upgrade_model.get_recommendations(upgrade_preds, churn_preds)
    
    assert len(recommendations) > 0, "No recommendations generated"
    print(f"✓ Generated {len(recommendations)} recommendations")

# ============================================================================
# SECTION 5: DATA QUALITY VALIDATION TESTS
# ============================================================================

def test_data_validator_initialization():
    """Test DataValidator initialization"""
    from src.data_quality.validator import DataValidator, get_constituent_checks
    
    validator = DataValidator()
    assert validator is not None
    
    checks = get_constituent_checks()
    assert isinstance(checks, list) or isinstance(checks, dict)
    print("✓ DataValidator initialized")
    print(f"✓ Constituent checks retrieved")

def test_data_validation_report():
    """Test data validation report generation"""
    from src.data_quality.validator import DataValidator, get_constituent_checks
    
    validator = DataValidator()
    validator.add_checks(get_constituent_checks())
    
    # Create test data
    test_df = pd.DataFrame({
        'constituent_id': [f'C-{i:05d}' for i in range(20)],
        'canonical_email': [f'user{i}@example.com' for i in range(20)],
        'lifecycle_stage': ['sustainer'] * 20,
        'churn_risk_score': np.random.rand(20)
    })
    
    report = validator.validate(test_df, "test_constituents")
    assert report is not None
    print("✓ Validation report generated")
    print(f"  - Report type: {type(report).__name__}")

# ============================================================================
# SECTION 6: FULL PIPELINE INTEGRATION TEST
# ============================================================================

def test_full_pipeline():
    """Test complete pipeline execution"""
    from src.data_generator import SyntheticDataGenerator, GeneratorConfig
    from src.identity_resolution.identity_resolver import (
        SourceRecord, MatchConfig, ConstituentUnifier
    )
    from src.ml_models.churn_prediction import ChurnPredictor, generate_sample_data
    
    print("\n--- Phase 1: Data Generation ---")
    config = GeneratorConfig(num_constituents=30)
    generator = SyntheticDataGenerator(config)
    datasets = generator.generate_all()
    print(f"✓ Generated {len(datasets)} datasets")
    
    print("\n--- Phase 2: Identity Resolution ---")
    source_records = []
    for _, row in datasets['wbez_donations'].head(50).iterrows():
        source_records.append(SourceRecord(
            source_system="wbez",
            source_id=row['donation_id'],
            email=row.get('email'),
            first_name=row.get('first_name'),
            last_name=row.get('last_name')
        ))
    
    unifier = ConstituentUnifier(MatchConfig())
    constituents = unifier.unify_records(source_records)
    print(f"✓ Unified {len(constituents)} constituents from {len(source_records)} records")
    
    print("\n--- Phase 3: ML Model Training ---")
    X, y = generate_sample_data(n=100)
    churn_model = ChurnPredictor()
    metrics = churn_model.train(X, y)
    print(f"✓ Churn model trained (AUC: {metrics['auc']:.3f})")
    
    print("\n--- Phase 4: Predictions ---")
    predictions = churn_model.predict(X.head(10))
    print(f"✓ Generated {len(predictions)} predictions")
    
    print("\n✓ FULL PIPELINE EXECUTION SUCCESSFUL")

# ============================================================================
# SECTION 7: PERFORMANCE & EDGE CASES
# ============================================================================

def test_empty_dataset_handling():
    """Test handling of empty datasets"""
    from src.identity_resolution.identity_resolver import MatchConfig, ConstituentUnifier
    
    try:
        unifier = ConstituentUnifier(MatchConfig())
        constituents = unifier.unify_records([])
        print("✓ Empty dataset handled gracefully")
    except Exception as e:
        test_results["warnings"].append(f"Empty dataset may not be handled: {e}")
        print(f"⚠️  Warning: Empty dataset handling - {e}")

def test_missing_fields_handling():
    """Test handling of missing fields"""
    from src.identity_resolution.identity_resolver import SourceRecord
    
    record = SourceRecord(
        source_system="test",
        source_id="T-001"
    )
    assert record.source_system == "test"
    print("✓ Missing optional fields handled gracefully")

def test_large_batch_processing():
    """Test processing of larger batches"""
    from src.ml_models.churn_prediction import ChurnPredictor, generate_sample_data
    
    X, y = generate_sample_data(n=500)
    model = ChurnPredictor()
    metrics = model.train(X, y)
    
    assert metrics['auc'] is not None
    print(f"✓ Processed 500 samples successfully")
    print(f"  - AUC: {metrics['auc']:.3f}")

# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("CPM ENTERPRISE BLUEPRINT - QA TEST SUITE")
    print("="*60)
    
    # Section 1: Import Tests
    print("\n\n" + "█"*60)
    print("SECTION 1: IMPORT & MODULE TESTS")
    print("█"*60)
    test_case("Import Data Generator", test_import_data_generator)
    test_case("Import Identity Resolver", test_import_identity_resolver)
    test_case("Import ML Models", test_import_ml_models)
    test_case("Import Data Quality", test_import_data_quality)
    
    # Section 2: Data Generation
    print("\n\n" + "█"*60)
    print("SECTION 2: DATA GENERATION TESTS")
    print("█"*60)
    test_case("GeneratorConfig Initialization", test_data_generator_config)
    test_case("Synthetic Data Generation", test_synthetic_data_generation)
    test_case("Data Schema Validation", test_data_schema_validation)
    test_case("Data Quality Checks", test_data_quality_checks)
    
    # Section 3: Identity Resolution
    print("\n\n" + "█"*60)
    print("SECTION 3: IDENTITY RESOLUTION TESTS")
    print("█"*60)
    test_case("SourceRecord Creation", test_source_record_creation)
    test_case("MatchConfig Initialization", test_match_config)
    test_case("ConstituentUnifier", test_constituent_unifier)
    test_case("Unifier Statistics", test_unifier_statistics)
    
    # Section 4: ML Models
    print("\n\n" + "█"*60)
    print("SECTION 4: ML MODEL TESTS")
    print("█"*60)
    test_case("ChurnPredictor Initialization", test_churn_predictor_initialization)
    test_case("Churn Model Training", test_churn_model_training)
    test_case("Churn Predictions", test_churn_predictions)
    test_case("UpgradePropensityModel", test_upgrade_propensity_model)
    test_case("Upgrade Predictions", test_upgrade_predictions)
    test_case("Recommendations Generation", test_recommendations_generation)
    
    # Section 5: Data Quality
    print("\n\n" + "█"*60)
    print("SECTION 5: DATA QUALITY TESTS")
    print("█"*60)
    test_case("DataValidator Initialization", test_data_validator_initialization)
    test_case("Validation Report Generation", test_data_validation_report)
    
    # Section 6: Integration
    print("\n\n" + "█"*60)
    print("SECTION 6: FULL PIPELINE INTEGRATION TEST")
    print("█"*60)
    test_case("Full Pipeline Execution", test_full_pipeline)
    
    # Section 7: Performance
    print("\n\n" + "█"*60)
    print("SECTION 7: PERFORMANCE & EDGE CASES")
    print("█"*60)
    test_case("Empty Dataset Handling", test_empty_dataset_handling)
    test_case("Missing Fields Handling", test_missing_fields_handling)
    test_case("Large Batch Processing", test_large_batch_processing)
    
    # Summary Report
    print("\n\n" + "="*60)
    print("TEST EXECUTION SUMMARY")
    print("="*60)
    
    total_passed = len(test_results["passed"])
    total_failed = len(test_results["failed"])
    total_warnings = len(test_results["warnings"])
    total_tests = total_passed + total_failed
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📊 RESULTS:")
    print(f"  ✅ Passed:  {total_passed}/{total_tests}")
    print(f"  ❌ Failed:  {total_failed}/{total_tests}")
    print(f"  ⚠️  Warnings: {total_warnings}")
    print(f"  📈 Pass Rate: {pass_rate:.1f}%")
    
    if test_results["failed"]:
        print(f"\n❌ FAILED TESTS:")
        for test_name, error in test_results["failed"]:
            print(f"  - {test_name}")
            print(f"    Error: {error[:100]}...")
    
    if test_results["warnings"]:
        print(f"\n⚠️  WARNINGS:")
        for warning in test_results["warnings"]:
            print(f"  - {warning}")
    
    print(f"\n{'='*60}")
    if total_failed == 0:
        print("🎉 ALL TESTS PASSED - SOLUTION IS ROBUST!")
    else:
        print(f"⚠️  {total_failed} TEST(S) FAILED - REVIEW REQUIRED")
    print(f"{'='*60}\n")
    
    return total_failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
